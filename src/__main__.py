#!/usr/bin/env python3
"""
主模块入口点，支持 python -m src.main 调用
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import app

if __name__ == "__main__":
    app()
