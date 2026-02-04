#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 英雄对战模拟系统
使用PyInstaller打包为独立可执行文件
"""

import os
import sys
import subprocess
from pathlib import Path

def check_and_install_pyinstaller():
    """检查并安装PyInstaller"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("正在安装PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller 安装成功")
            return True
        except subprocess.CalledProcessError:
            print("✗ PyInstaller 安装失败")
            return False

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # PyInstaller命令参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "run_gui.py",  # 入口文件
        "--name=HeroBattleSimulator",
        "--onefile",  # 单文件模式
        "--windowed",  # 无控制台窗口
        "--add-data=英雄类数据1.xlsx:.",  # 包含数据文件
        "--add-data=config:config",  # 配置文件目录
        "--add-data=core:core",  # 核心模块
        "--add-data=data:data",  # 数据处理
        "--add-data=battle:battle",  # 战斗系统
        "--add-data=utils:utils",  # 工具模块
        "--hidden-import=pandas",
        "--hidden-import=openpyxl", 
        "--hidden-import=numpy",
        "--hidden-import=tkinter",
        "--hidden-import=PIL",
        "--clean",  # 清理缓存
        "--noconfirm"  # 不确认
    ]
    
    try:
        print("执行打包命令...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✓ 打包成功!")
            print(f"可执行文件位置: dist/HeroBattleSimulator")
            return True
        else:
            print("✗ 打包失败!")
            print("错误信息:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ 打包过程出错: {e}")
        return False

def main():
    """主函数"""
    print("=== 英雄对战模拟系统打包工具 ===\n")
    
    # 检查数据文件
    if not Path("英雄类数据1.xlsx").exists():
        print("✗ 错误: 数据文件 '英雄类数据1.xlsx' 不存在")
        print("请确保文件在项目根目录")
        return
    
    # 检查并安装PyInstaller
    if not check_and_install_pyinstaller():
        return
    
    # 构建可执行文件
    if build_executable():
        print("\n=== 打包完成 ===")
        print("文件位置: dist/HeroBattleSimulator")
        print("\n启动方式:")
        print("  cd dist")
        print("  ./HeroBattleSimulator")
    else:
        print("\n✗ 打包失败，请检查错误信息")

if __name__ == "__main__":
    main()