#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI交互增强模块 - 提供更好的用户体验
"""

from typing import Dict, List, Optional, Callable, Any
import sys
import os
from dataclasses import dataclass
from enum import Enum
import readline  # 提供命令行历史记录和自动补全


class TextColor:
    """终端文本颜色常量"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class MenuOption:
    """菜单选项类"""
    
    def __init__(self, key: str, description: str, handler: Callable, 
                 color: str = TextColor.WHITE, enabled: bool = True):
        self.key = key
        self.description = description
        self.handler = handler
        self.color = color
        self.enabled = enabled


class CLIEnhancer:
    """CLI交互增强器"""
    
    def __init__(self, app_name: str = "英雄对战模拟系统"):
        self.app_name = app_name
        self.menu_history: List[str] = []
        self.current_menu: Optional[List[MenuOption]] = None
        
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: Optional[str] = None):
        """打印应用头部"""
        self.clear_screen()
        header_title = title or self.app_name
        print(f"{TextColor.CYAN}{TextColor.BOLD}{'='*60}{TextColor.RESET}")
        print(f"{TextColor.CYAN}{TextColor.BOLD}{header_title:^60}{TextColor.RESET}")
        print(f"{TextColor.CYAN}{TextColor.BOLD}{'='*60}{TextColor.RESET}\n")
    
    def print_success(self, message: str):
        """打印成功消息"""
        print(f"{TextColor.GREEN}✓ {message}{TextColor.RESET}")
    
    def print_warning(self, message: str):
        """打印警告消息"""
        print(f"{TextColor.YELLOW}⚠ {message}{TextColor.RESET}")
    
    def print_error(self, message: str):
        """打印错误消息"""
        print(f"{TextColor.RED}✗ {message}{TextColor.RESET}")
    
    def print_info(self, message: str):
        """打印信息消息"""
        print(f"{TextColor.BLUE}ℹ {message}{TextColor.RESET}")
    
    def create_menu(self, options: List[MenuOption], title: str = "请选择操作") -> Optional[Callable]:
        """创建交互式菜单"""
        self.current_menu = options
        
        while True:
            self.print_header(title)
            
            # 显示菜单历史（如果有）
            if self.menu_history:
                print(f"{TextColor.WHITE}当前位置: {' > '.join(self.menu_history)}{TextColor.RESET}\n")
            
            # 显示菜单选项
            for option in options:
                status = "" if option.enabled else "(禁用)"
                color = TextColor.WHITE if option.enabled else TextColor.YELLOW
                print(f"{color}{option.key}. {option.description} {status}{TextColor.RESET}")
            
            # 显示返回选项（如果不是主菜单）
            if len(self.menu_history) > 0:
                print(f"{TextColor.MAGENTA}b. 返回上级菜单{TextColor.RESET}")
            print(f"{TextColor.MAGENTA}q. 退出程序{TextColor.RESET}")
            
            # 获取用户输入
            choice = input(f"\n{TextColor.CYAN}请输入选择: {TextColor.RESET}").strip().lower()
            
            # 处理特殊命令
            if choice == 'q':
                return None
            elif choice == 'b' and len(self.menu_history) > 0:
                self.menu_history.pop()
                return None
            
            # 查找匹配的选项
            selected_option = next((opt for opt in options if opt.key.lower() == choice), None)
            
            if selected_option:
                if selected_option.enabled:
                    return selected_option.handler
                else:
                    self.print_warning("该选项当前不可用")
                    input("按回车键继续...")
            else:
                self.print_error("无效的选择，请重新输入")
                input("按回车键继续...")
    
    def prompt_yes_no(self, question: str, default: bool = True) -> bool:
        """是/否提示"""
        options = "(Y/n)" if default else "(y/N)"
        while True:
            response = input(f"{TextColor.CYAN}{question} {options}: {TextColor.RESET}").strip().lower()
            if response == '':
                return default
            elif response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                self.print_error("请输入 y(es) 或 n(o)")
    
    def prompt_number(self, prompt: str, min_val: Optional[int] = None, 
                     max_val: Optional[int] = None, default: Optional[int] = None) -> Optional[int]:
        """数字输入提示"""
        range_text = ""
        if min_val is not None and max_val is not None:
            range_text = f" ({min_val}-{max_val})"
        elif min_val is not None:
            range_text = f" (≥{min_val})"
        elif max_val is not None:
            range_text = f" (≤{max_val})"
        
        default_text = f" [{default}]" if default is not None else ""
        
        while True:
            try:
                response = input(f"{TextColor.CYAN}{prompt}{range_text}{default_text}: {TextColor.RESET}").strip()
                
                if response == '' and default is not None:
                    return default
                
                value = int(response)
                
                if (min_val is not None and value < min_val) or (max_val is not None and value > max_val):
                    self.print_error(f"数值必须在 {min_val}-{max_val} 范围内")
                    continue
                
                return value
                
            except ValueError:
                self.print_error("请输入有效的数字")
    
    def prompt_selection(self, prompt: str, options: List[str], 
                        display_func: Optional[Callable[[str], str]] = None) -> Optional[int]:
        """选项选择提示"""
        print(f"{TextColor.CYAN}{prompt}:{TextColor.RESET}")
        
        for i, option in enumerate(options, 1):
            display_text = display_func(option) if display_func else option
            print(f"  {i}. {display_text}")
        
        while True:
            try:
                choice = input(f"{TextColor.CYAN}请选择 (1-{len(options)}): {TextColor.RESET}").strip()
                
                if not choice:
                    return None
                
                index = int(choice) - 1
                
                if 0 <= index < len(options):
                    return index
                else:
                    self.print_error(f"请选择 1-{len(options)} 之间的数字")
                    
            except ValueError:
                self.print_error("请输入有效的数字")
    
    def show_loading(self, message: str, duration: float = 1.0):
        """显示加载动画"""
        import time
        
        print(f"{TextColor.BLUE}{message}...{TextColor.RESET}", end="", flush=True)
        
        # 简单加载动画
        for i in range(3):
            print(".", end="", flush=True)
            time.sleep(duration / 3)
        
        print()
    
    def format_battle_result(self, result: Dict[str, Any]) -> str:
        """格式化战斗结果"""
        winner = result.get('winner', '未知')
        turns = result.get('turns', 0)
        winner_health = result.get('winner_health', 0)
        
        return (
            f"{TextColor.GREEN}{TextColor.BOLD}战斗结束!{TextColor.RESET}\n"
            f"胜利者: {TextColor.GREEN}{winner}{TextColor.RESET}\n"
            f"战斗回合: {turns}\n"
            f"剩余生命: {winner_health}"
        )


# 全局CLI实例
cli = CLIEnhancer()