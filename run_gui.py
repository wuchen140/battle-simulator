#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI启动脚本
运行可视化主界面
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import tkinter
        import pandas
        import openpyxl
        return True
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("正在启动英雄对战模拟系统 GUI...")
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查数据文件是否存在
    excel_path = project_root / "英雄类数据1.xlsx"
    if not excel_path.exists():
        print(f"错误: 数据文件不存在: {excel_path}")
        print("请确保 '英雄类数据1.xlsx' 文件在项目根目录")
        return
    
    try:
        from main_gui import main as gui_main
        print("GUI启动成功!")
        gui_main()
        
    except Exception as e:
        print(f"启动GUI失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()