# -*- coding: utf-8 -*-
"""
入口包装脚本（兼容运行方式）

真实实现位于：
`examples/gradio_multimodal_deepseek/gradio_multimodal_deepseek.py`

这样你可以直接执行：
`uv run python examples/gradio_multimodal_deepseek.py`
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    inner = (
        Path(__file__).resolve().parent
        / "gradio_multimodal_deepseek"
        / "gradio_multimodal_deepseek.py"
    )
    runpy.run_path(str(inner), run_name="__main__")


if __name__ == "__main__":
    main()
