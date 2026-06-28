# -*- coding: utf-8 -*-
"""
生成式 Agent 系统 (Generative Agents)

基于 Stanford "Generative Agents" 论文架构实现:
- MemoryStream: 记忆流，带重要性评分 + 时效衰减 + 混合检索
- Reflection:   反思模块，定期从记忆提炼高层洞察
- Planning:     规划模块，生成/跟踪/修正分层计划

核心公式:
  检索得分 = recency_weight × recency + importance_weight × importance
           + relevance_weight × relevance
"""

import os
import re
import time
import json
import math
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict

import jieba

from core.config import settings
from core.logger import logger

# ═══════════════════════════════════════════════════════════════════
# 常量配置
# ═══════════════════════════════════════════════════════════════════

# 记忆流存储路径
_MEMORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "generative_memory"
)

# 检索权重
RECENCY_WEIGHT = 0.3
IMPORTANCE_WEIGHT = 0.4
RELEVANCE_WEIGHT = 0.3

# 时效衰减半衰期（秒）：24 小时
RECENCY_DECAY_HALFLIFE = 86400

# 反思触发条件
REFLECTION_IMPORTANCE_THRESHOLD = 30  # 累计重要性超过此值触发反思
MAX_REFLECTIONS = 50                  # 最多保存的反思数

# 记忆上限
MAX_MEMORIES = 500

# 检索返回数
RETRIEVAL_K = 5


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

def _get_llm(temperature: float = 0.3, max_tokens: int = 256):
    """获取用于反思和规划的轻量 LLM。"""
    from models import create_chat_model
    # 从环境变量获取模型名，兼容本地代理
    model_name = os.getenv("REFLECTION_MODEL") or os.getenv("MIMO_MODEL") or os.getenv("OPENAI_MODEL_NAME") or "gpt-4o-mini"
    return create_chat_model(
        provider_name="openai",
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _tokenize(text: str) -> List[str]:
    """jieba 分词提取关键词。"""
    words = jieba.lcut(text)
    return [w.strip() for w in words if len(w.strip()) >= 2
            and not re.match(r'^[，,。！!？?：:；;\s\d]+$', w)]


def _compute_recency(timestamp: float, now: float = None) -> float:
    """指数衰减计算时效分 (0~1)。"""
    if now is None:
        now = time.time()
    elapsed = now - timestamp
    return math.exp(-elapsed * math.log(2) / RECENCY_DECAY_HALFLIFE)


# ═══════════════════════════════════════════════════════════════════
# MemoryStream — 记忆流
# ═══════════════════════════════════════════════════════════════════

class MemoryStream:
    """
    记忆流：存储 Agent 的所有观察/对话记忆。

    每条记忆:
      {
        "id":        "m001",
        "session_id": "sess-xxx",
        "content":   "用户询问了北京天气, AI回答说晴天25度",
        "importance": 7.5,          # 1~10 重要性评分
        "timestamp":  1700000000.0,
        "keywords":   ["北京", "天气", "晴天"],
        "type":       "observation", # observation / reflection / plan
      }

    检索:
      score = 0.3*recency + 0.4*importance + 0.3*relevance
    """

    def __init__(self):
        os.makedirs(_MEMORY_DIR, exist_ok=True)
        self._memories: List[Dict] = []
        self._id_counter = 0
        self._cumulative_importance = 0.0  # 累计重要性，用于触发反思
        self._load()

    def _load(self):
        path = os.path.join(_MEMORY_DIR, "memory_stream.jsonl")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self._memories.append(json.loads(line))
            if self._memories:
                self._id_counter = max(
                    int(m["id"][1:]) for m in self._memories
                    if m["id"].startswith("m")
                )
                self._cumulative_importance = sum(
                    m.get("importance", 5) for m in self._memories
                )
            logger.info(f"记忆流: 恢复 {len(self._memories)} 条记忆")
        except Exception as e:
            logger.warning(f"记忆流: 恢复失败 {e}")

    def _save(self):
        path = os.path.join(_MEMORY_DIR, "memory_stream.jsonl")
        try:
            with open(path, "w", encoding="utf-8") as f:
                for m in self._memories[-MAX_MEMORIES:]:
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"记忆流: 持久化失败 {e}")

    def _rate_importance(self, content: str) -> float:
        """用 LLM 对记忆重要性打分 (1~10)。"""
        prompt = (
            "请对以下对话片段的重要性打分（1~10整数），"
            "考虑: 是否包含用户偏好/关键决策/待办事项/重要数据。\n"
            f"对话: {content[:500]}\n"
            "只输出数字。"
        )
        try:
            response = _get_llm(temperature=0, max_tokens=4).invoke(prompt)
            score = float(response.content.strip())
            return max(1.0, min(10.0, score))
        except Exception:
            # LLM 不可用时用规则：长度越长越重要
            return min(10.0, 3.0 + len(content) / 100)

    def add(self, session_id: str, query: str, response: str,
            mem_type: str = "observation") -> Dict:
        """
        存入一条记忆。

        Returns: 记忆条目
        """
        self._id_counter += 1
        content = f"Q: {query[:400]}\nA: {response[:400]}"
        importance = self._rate_importance(content)
        now = time.time()

        memory = {
            "id": f"m{self._id_counter:05d}",
            "session_id": session_id,
            "content": content,
            "importance": round(importance, 1),
            "timestamp": now,
            "keywords": _tokenize(f"{query} {response}"),
            "type": mem_type,
        }

        self._memories.append(memory)
        self._cumulative_importance += importance

        if len(self._memories) > MAX_MEMORIES:
            removed = self._memories[:-MAX_MEMORIES]
            self._cumulative_importance -= sum(m.get("importance", 5) for m in removed)
            self._memories = self._memories[-MAX_MEMORIES:]

        # 每 10 条持久化一次
        if self._id_counter % 10 == 0:
            self._save()

        logger.info(
            f"记忆流: +{memory['id']} importance={importance:.1f} "
            f"({memory['keywords'][:3]}...)"
        )
        return memory

    def _keyword_relevance(self, query: str, memory: Dict) -> float:
        """关键词匹配得分 (0~1)。"""
        qtokens = set(_tokenize(query))
        mtokens = set(memory.get("keywords", []))
        if not qtokens:
            return 0.0
        overlap = qtokens & mtokens
        return len(overlap) / len(qtokens)

    def retrieve(self, query: str, k: int = RETRIEVAL_K,
                 now: float = None) -> List[Dict]:
        """
        混合检索：时效 × 重要性 × 关键词相关度。

        Returns: 按得分降序的 Top-K 记忆列表。
        """
        if not self._memories:
            return []
        if now is None:
            now = time.time()

        scored = []
        for mem in self._memories:
            recency = _compute_recency(mem["timestamp"], now)
            importance = mem.get("importance", 5) / 10.0  # 归一化到 0~1
            relevance = self._keyword_relevance(query, mem)

            # 加权融合
            score = (
                RECENCY_WEIGHT * recency +
                IMPORTANCE_WEIGHT * importance +
                RELEVANCE_WEIGHT * relevance
            )

            if score > 0.05:  # 最低阈值
                scored.append((mem, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        top = scored[:k]
        if top:
            logger.info(
                f"记忆流检索: '{query[:30]}...' → {len(top)}/{len(self._memories)} "
                f"(recency={top[0][1]:.3f})"
            )

        return [mem for mem, _score in top]

    def get_recent(self, n: int = 10) -> List[Dict]:
        """获取最近 N 条记忆（按时间倒序）。"""
        return sorted(self._memories, key=lambda m: m["timestamp"], reverse=True)[:n]

    @property
    def should_reflect(self) -> bool:
        """是否需要触发反思。"""
        return self._cumulative_importance >= REFLECTION_IMPORTANCE_THRESHOLD

    def reset_reflection_counter(self):
        """重置累计重要性计数器（反思后调用）。"""
        self._cumulative_importance = 0.0

    def clear(self):
        self._memories = []
        self._id_counter = 0
        self._cumulative_importance = 0.0
        self._save()
        logger.info("记忆流: 已清空")


# ═══════════════════════════════════════════════════════════════════
# Reflection — 反思模块
# ═══════════════════════════════════════════════════════════════════

class Reflection:
    """
    反思模块：定期从记忆流中提炼高层洞察。

    触发条件: 累计重要性超过阈值
    产出:     3 条反思性问题 → 生成抽象反思答案
    存储:     反思结果回写记忆流（type=reflection, importance=9）
    """

    _REFLECTION_QUESTIONS = [
        "关于用户的长期偏好和习惯，从这些对话中能推断出什么？",
        "这些对话中出现了哪些重复的主题或用户反复关心的问题？",
        "用户有哪些明确表达的待办事项或后续需求？",
    ]

    def __init__(self, memory_stream: MemoryStream):
        self._memory = memory_stream
        self._reflections: List[Dict] = []
        self._reflection_count = 0

    def reflect(self) -> Optional[List[Dict]]:
        """
        执行一次反思。

        Returns: 新生成的反思记忆列表，如果不应反思则返回 None。
        """
        if not self._memory.should_reflect:
            return None

        # 取最近高重要性记忆
        recent = self._memory.get_recent(50)
        important = sorted(
            recent, key=lambda m: m.get("importance", 5), reverse=True
        )[:20]

        if not important:
            return None

        # 提交给 LLM 反思
        context = "\n".join(
            f"[{m['id']}] ({m.get('importance',5):.0f}) {m['content'][:200]}"
            for m in important
        )

        new_reflections = []
        for q in self._REFLECTION_QUESTIONS[:2]:  # 每次反思只问 2 个问题
            try:
                prompt = (
                    f"基于以下最近对话记录，请回答:\n\n"
                    f"对话记录:\n{context}\n\n"
                    f"问题: {q}\n\n"
                    f"只回答核心洞察，2~3句话，简洁有力。"
                )
                response = _get_llm(max_tokens=200).invoke(prompt)
                answer = response.content.strip()
                if answer and len(answer) > 10:
                    ref_memory = {
                        "id": f"r{self._reflection_count:04d}",
                        "session_id": "system",
                        "content": f"[反思] Q: {q}\nA: {answer}",
                        "importance": 9.0,
                        "timestamp": time.time(),
                        "keywords": _tokenize(answer),
                        "type": "reflection",
                    }
                    new_reflections.append(ref_memory)
                    self._reflections.append(ref_memory)
                    self._reflection_count += 1
                    logger.info(f"反思: {answer[:60]}...")
            except Exception as e:
                logger.warning(f"反思失败: {e}")

        # 反思结果写入记忆流
        for ref in new_reflections:
            self._memory._memories.append(ref)

        self._memory.reset_reflection_counter()
        self._memory._save()

        return new_reflections

    @property
    def count(self) -> int:
        return len(self._reflections)


# ═══════════════════════════════════════════════════════════════════
# Planning — 规划模块
# ═══════════════════════════════════════════════════════════════════

class Planner:
    """
    规划模块：生成分层计划并跟踪执行。

    计划结构:
      {
        "plan_id": "p001",
        "goal": "帮助用户完成项目X",
        "created_at": 1700000000.0,
        "status": "active",       # active / completed / abandoned
        "tasks": [
          { "id": "t1", "desc": "步骤1: ...", "status": "done" },
          { "id": "t2", "desc": "步骤2: ...", "status": "pending" },
        ],
      }

    分层:
      L1 - 目标级: 大方向
      L2 - 任务级: 具体步骤
      L3 - 子任务级: 可执行细节 (由 Agent 自动分解)
    """

    def __init__(self):
        self._plans: List[Dict] = []
        self._plan_counter = 0
        self._plans_path = os.path.join(_MEMORY_DIR, "plans.jsonl")
        self._load()

    def _load(self):
        if not os.path.exists(self._plans_path):
            return
        try:
            with open(self._plans_path, "r", encoding="utf-8") as f:
                self._plans = [json.loads(line) for line in f if line.strip()]
            if self._plans:
                self._plan_counter = len(self._plans)
            logger.info(f"规划: 恢复 {len(self._plans)} 个计划")
        except Exception as e:
            logger.warning(f"规划: 恢复失败 {e}")

    def _save(self):
        try:
            with open(self._plans_path, "w", encoding="utf-8") as f:
                for p in self._plans:
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"规划: 持久化失败 {e}")

    def generate_plan(self, context: str, recent_memories: List[Dict],
                      reflections: List[Dict]) -> Optional[Dict]:
        """
        根据当前上下文和记忆生成计划。

        Args:
            context: 当前用户意图/对话上下文
            recent_memories: 最近记忆
            reflections: 反思结果

        Returns: 生成的计划，如果不需要则返回 None
        """
        # 构建摘要
        recent_text = "\n".join(
            m["content"][:150] for m in recent_memories[:5]
        )
        reflections_text = "\n".join(
            r["content"][:150] for r in reflections[:3]
        )

        try:
            prompt = (
                "你是一个智能规划助手。基于当前的对话上下文和历史，判断需要不需要生成一个计划。\n"
                "如果只是简单闲聊，回复 NO_PLAN_NEEDED。\n"
                "如果需要规划（多步骤任务、用户有明确目标、需要后续跟进的场景），回复:\n"
                "GOAL: <一句话目标>\n"
                "TASKS:\n"
                "- <任务1>\n- <任务2>\n\n"
                f"=== 当前对话上下文 ===\n{context[:300]}\n\n"
                f"=== 最近记忆 ===\n{recent_text}\n\n"
                f"=== 已有洞察 ===\n{reflections_text}"
            )
            response = _get_llm(max_tokens=300).invoke(prompt)
            text = response.content.strip()

            if "NO_PLAN_NEEDED" in text:
                return None

            # 解析计划
            goal_match = re.search(r'GOAL:\s*(.+)', text)
            if not goal_match:
                return None

            goal = goal_match.group(1).strip()
            task_matches = re.findall(r'-\s*(.+)', text)

            if not task_matches:
                return None

            self._plan_counter += 1
            plan = {
                "plan_id": f"p{self._plan_counter:04d}",
                "goal": goal,
                "created_at": time.time(),
                "status": "active",
                "tasks": [
                    {"id": f"t{i+1}", "desc": t.strip(), "status": "pending"}
                    for i, t in enumerate(task_matches[:5])
                ],
            }

            self._plans.append(plan)
            self._save()
            logger.info(f"规划: 新建计划 [{plan['plan_id']}] {goal[:40]} ({len(task_matches)} 任务)")
            return plan

        except Exception as e:
            logger.warning(f"规划生成失败: {e}")
            return None

    def update_task(self, plan_id: str, task_id: str, status: str):
        """更新任务状态 (pending/doing/done/blocked)。"""
        for plan in self._plans:
            if plan["plan_id"] == plan_id:
                for task in plan["tasks"]:
                    if task["id"] == task_id:
                        task["status"] = status
                        if all(t["status"] == "done" for t in plan["tasks"]):
                            plan["status"] = "completed"
                        self._save()
                        return
                break

    @property
    def active_plans(self) -> List[Dict]:
        return [p for p in self._plans if p["status"] == "active"]

    def format_active(self) -> str:
        """格式化当前活跃计划为上下文字符串。"""
        active = self.active_plans
        if not active:
            return ""
        lines = ["[当前的活跃计划]"]
        for p in active[-3:]:
            lines.append(f"\n📋 {p['goal']}")
            for t in p["tasks"]:
                icon = {"done": "✅", "doing": "🔄", "pending": "⬜", "blocked": "🚫"}.get(t["status"], "⬜")
                lines.append(f"  {icon} {t['desc']}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# GenerativeAgent — 生成式 Agent 核心
# ═══════════════════════════════════════════════════════════════════

class GenerativeAgent:
    """
    生成式 Agent: 记忆流 + 反思 + 规划 三件套。

    使用方式:
      agent = GenerativeAgent()

      # 每轮对话后
      agent.observe(session_id, query, response)

      # 检索相关记忆，注入上下文
      context = agent.build_context(current_query, session_id)
    """

    def __init__(self):
        self.memory = MemoryStream()
        self.reflection = Reflection(self.memory)
        self.planner = Planner()
        self._last_reflect_time = 0.0

    def observe(self, session_id: str, query: str, response: str):
        """
        记录一条观察（对话轮次）。

        流程:
          memory.add() → 检查是否触发反思 → 检查是否生成计划
        """
        mem = self.memory.add(session_id, query, response)

        # 触发反思（每 5 分钟最多一次）
        now = time.time()
        if self.memory.should_reflect and (now - self._last_reflect_time > 300):
            self.reflection.reflect()
            self._last_reflect_time = now
            logger.info(f"生成式Agent: 已触发反思 (总反思 {self.reflection.count} 条)")

        return mem

    def build_context(self, current_query: str, session_id: str) -> str:
        """
        为当前对话构建增强上下文。

        返回可注入给 LLM 的文本:
          [记忆流相关记忆]
          [反思洞察]
          [活跃计划]
        """
        parts = []

        # 记忆流检索
        memories = self.memory.retrieve(current_query)
        if memories:
            lines = ["[📝 相关历史记忆]"]
            for mem in memories:
                ts = datetime.fromtimestamp(mem["timestamp"]).strftime("%m-%d %H:%M")
                imp = mem.get("importance", 5)
                tag = "⭐" if imp >= 7 else ("📌" if imp >= 5 else "💬")
                lines.append(f"{tag} ({ts}) {mem['content'][:200]}")
            parts.append("\n".join(lines))

        # 反思洞察
        if self.reflection._reflections:
            recent_ref = self.reflection._reflections[-3:]
            lines = ["\n[🧠 洞察与反思]"]
            for r in recent_ref:
                lines.append(f"- {r['content'][:200]}")
            parts.append("\n".join(lines))

        # 活跃计划
        plan_text = self.planner.format_active()
        if plan_text:
            parts.append("\n" + plan_text)

        return "\n".join(parts) if parts else ""

    def try_plan(self, current_query: str, session_id: str) -> Optional[Dict]:
        """尝试生成计划（如果当前对话有明确目标）。"""
        recent = self.memory.get_recent(10)
        refs = self.reflection._reflections[-5:] if self.reflection._reflections else []
        return self.planner.generate_plan(current_query, recent, refs)

    def clear(self):
        self.memory.clear()
        self.reflection._reflections = []
        self.reflection._reflection_count = 0
        self.planner._plans = []
        self.planner._save()
        logger.info("生成式Agent: 已清空全部状态")


# ═══════════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════════

_gen_agent: Optional[GenerativeAgent] = None


def get_generative_agent() -> GenerativeAgent:
    global _gen_agent
    if _gen_agent is None:
        _gen_agent = GenerativeAgent()
        logger.info("生成式Agent: 初始化完成 (记忆流 + 反思 + 规划)")
    return _gen_agent
