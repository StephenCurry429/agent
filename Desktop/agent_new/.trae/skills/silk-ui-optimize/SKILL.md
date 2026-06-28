---
name: "silk-ui-optimize"
description: "Debugs frontend UI visual bugs and enforces Silk Design System consistency. Invoke when frontend styles misalign, colors mismatch, chat bubbles layout breaks, borders/shadows/spacing deviate from Silk spec, or UI doesn't match reference screenshots."
---

# Silk UI Optimize

专门用来调试前端页面 UI 视觉 bug、统一 Silk Design System 规范。覆盖场景：
- 前端页面样式错位、色差、圆角/阴影不一致
- 聊天气泡布局错乱、头像缺失、圆角切角异常、文字溢出、宽度超限
- 侧边会话列表 hover/激活态色值不统一、文字截断、间距混乱
- 功能卡片 hover 阴影、圆角、内边距不符合 Silk 规范
- 输入框焦点边框、占位文字样式异常
- 页面和参考截图 UI 不匹配

## 触发时机

发现前端页面样式错位、色差、圆角/阴影不一致、聊天气泡布局错乱、页面和参考截图 UI 不匹配时自动触发。

---

## 核心执行规则

### 1. 不重构原有业务代码
- 不改动接口、状态管理、useState、会话切换逻辑
- 不修改页面布局 DOM 结构、不新增/删除 DOM 节点
- 不修改消息数据结构、不修改循环渲染逻辑
- 仅修复视觉样式 Bug

### 2. 严格遵循 Silk Design System 统一规范

**色彩体系：**
| Token | 色值 | 用途 |
|-------|------|------|
| silk.primary | `#2563eb` | 主色：按钮、链接、焦点边框、用户气泡、强调元素 |
| silk.secondary | `#f97316` | 辅助色：警告提示、次要强调 |
| silk.success | `#10b981` | 成功状态 |
| silk.danger | `#ef4444` | 危险/错误状态 |
| silk.warning | `#f59e0b` | 警告状态 |
| silk.neutral.50 | `#f8fafc` | 页面背景、输入框背景 |
| silk.neutral.100 | `#f1f5f9` | AI 消息气泡背景 |
| silk.neutral.200 | `#e2e8f0` | 边框、分割线、用户头像背景 |
| silk.neutral.300 | `#cbd5e1` | 禁用态文字/边框 |
| silk.neutral.400 | `#94a3b8` | 占位文字 |
| silk.neutral.500 | `#64748b` | 次要文字 |
| silk.neutral.600 | `#475569` | 用户头像文字色 |
| silk.neutral.700 | `#334155` | 标题文字 |
| silk.neutral.800 | `#1e293b` | 正文文字（AI 气泡） |
| silk.neutral.900 | `#0f172a` | 深色背景文字 |

**圆角：** sm=`4px` md=`8px` lg=`12px` xl=`16px`

**间距：** xs=`4px` sm=`8px` md=`16px` lg=`24px` xl=`32px`

**阴影（3 层轻量化）：**
- silkSm: `0 1px 3px rgba(0,0,0,0.08)`
- silkMd: `0 4px 12px rgba(0,0,0,0.1)`
- silkLg: `0 8px 24px rgba(0,0,0,0.12)`

**字体：** fontFamily silk: `["Inter", "system-ui", "sans-serif"]`

### 3. 聊天界面 Bug 专项修复规范

**SilkChatBubble 聊天气泡标准：**
- 用户消息：右对齐、`bg-silk-primary text-white`、`rounded-tl-lg rounded-tr-lg rounded-bl-lg rounded-br-none`（右上直角）
- AI 消息：左对齐、`bg-silk-neutral-100 text-silk-neutral-800`、`rounded-tl-lg rounded-tr-lg rounded-bl-none rounded-br-lg`（左上直角）
- 头像：AI 用方形 32x32 `rounded-lg bg-silk-primary/10 text-silk-primary`，用户用圆形 32x32 `rounded-full bg-silk-neutral-200 text-silk-neutral-600`
- 气泡最大宽度 `max-w-[65%]`，移动端 `max-w-[85%]`
- 内边距 `px-md py-sm`（即 16px / 8px）

**侧边栏会话列表：**
- hover 态：`bg-silk-neutral-100`
- 激活态：`bg-silk-primary/10 border-l-2 border-silk-primary`
- 文字溢出：`truncate`
- 间距：`px-sm py-xs`

**功能卡片：**
- 默认：`bg-white rounded-lg shadow-silkSm p-md`
- hover：`shadow-silkMd` + `transition-all duration-200`
- 内边距：`p-md`（16px）

**输入框：**
- 默认：`border border-silk-neutral-200 rounded-md px-sm py-xs`
- 焦点：`focus:border-silk-primary focus:ring-1 focus:ring-silk-primary`
- 占位文字：`placeholder-silk-neutral-400`
- 过渡：`transition-all`

### 4. Bug 修复流程

1. **检查 Tailwind 配置**：读取 `tailwind.config.js`，检查是否存在 silk 主题 token；缺失则追加到 `theme.extend` 中，不覆盖原有配置
2. **检查全局 CSS 工具类**：检查是否存在 `.silk-card-base`、`.silk-input-base` 工具类；缺失则追加到全局样式文件
3. **定位 Bug 组件**：读取出错 UI 组件代码，定位问题 class
4. **修复 class 类名**：只修改 className，业务逻辑、变量、循环渲染完全保留
5. **输出修复报告**：列出改动文件清单，标注每一处 UI Bug 修改点，附修改前后样式对比

### 5. 约束红线

- 禁止删除/新增页面 DOM 节点
- 禁止修改 useState、接口请求、会话切换逻辑
- 禁止替换页面整体布局
- 禁止修改消息数据结构
- 兼容项目原有样式，不删除原有全局样式代码

---

## 参考素材（内置 Tailwind Silk 主题代码）

追加到 `tailwind.config.js` 的 `theme.extend` 中：

```js
silk: {
  primary: "#2563eb",
  secondary: "#f97316",
  success: "#10b981",
  danger: "#ef4444",
  warning: "#f59e0b",
  neutral: {
    50: "#f8fafc",
    100: "#f1f5f9",
    200: "#e2e8f0",
    300: "#cbd5e1",
    400: "#94a3b8",
    500: "#64748b",
    600: "#475569",
    700: "#334155",
    800: "#1e293b",
    900: "#0f172a",
  },
},
borderRadius: {
  sm: "4px",
  md: "8px",
  lg: "12px",
  xl: "16px",
},
spacing: {
  xs: "4px",
  sm: "8px",
  md: "16px",
  lg: "24px",
  xl: "32px",
},
boxShadow: {
  silkSm: "0 1px 3px rgba(0,0,0,0.08)",
  silkMd: "0 4px 12px rgba(0,0,0,0.1)",
  silkLg: "0 8px 24px rgba(0,0,0,0.12)",
},
```

## 全局 CSS Silk 工具类

追加到全局样式文件：

```css
.silk-card-base {
  @apply bg-white rounded-lg shadow-silkMd p-md transition-all duration-200 hover:shadow-silkLg;
}
.silk-input-base {
  @apply border border-silk-neutral-200 rounded-md px-sm py-xs outline-none focus:border-silk-primary focus:ring-1 focus:ring-silk-primary transition-all;
}
```

## SilkChatBubble 组件参考

```jsx
const SilkChatBubble = ({ type, content }) => {
  const isUser = type === 'user';
  return (
    <div className={`flex w-full my-md ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-silk-primary/10 flex-shrink-0 mr-sm flex items-center justify-center text-silk-primary">
          A
        </div>
      )}
      <div
        className={`max-w-[65%] px-md py-sm rounded-lg ${
          isUser
            ? 'bg-silk-primary text-white rounded-tr-none'
            : 'bg-silk-neutral-100 text-silk-neutral-800 rounded-tl-none'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{content}</p>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-silk-neutral-200 flex-shrink-0 ml-sm flex items-center justify-center text-silk-neutral-600">
          Z
        </div>
      )}
    </div>
  );
};
```
