#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英雄对战模拟系统 - 可视化主界面
集成所有功能的图形化用户界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.data_loader import HeroDataLoader
from data.data_validator import DataValidator, ValidationResult
from skill_manager import SkillManager
from core.hero import Hero
from battle.simulator import BattleSimulator
from core.config_manager import config
from core.cache_manager import cache_manager
from core.plugin_manager import PluginManager
from core.plugin_config import plugin_config_manager
from core.skill_chain import SkillChainManager
from visual_editor import PluginEditor
from battle.skill_editor import SkillEditor, SkillType, DamageType, TargetType, BuffType, ControlType


class BattleSimulatorGUI:
    """英雄对战模拟系统可视化主界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("英雄对战模拟系统")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # 初始化管理器
        self.plugin_manager = PluginManager()
        self.skill_chain_manager = SkillChainManager()
        
        # 加载数据
        self.heroes_data = []
        self.skills_data = []
        self.base_heroes = []
        
        # 当前选择的英雄
        self.selected_hero1 = None
        self.selected_hero2 = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 英雄对战标签页
        self.battle_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.battle_frame, text="英雄对战")
        self._setup_battle_tab()
        
        # 2. 插件管理标签页
        self.plugin_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.plugin_frame, text="插件管理")
        self._setup_plugin_tab()
        
        # 3. 技能链管理标签页
        self.skill_chain_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.skill_chain_frame, text="技能链管理")
        self._setup_skill_chain_tab()
        
        # 4. 技能管理标签页
        self.skill_manager_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.skill_manager_frame, text="技能管理")
        self._setup_skill_manager_tab()
        
        # 5. 系统状态标签页
        self.status_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.status_frame, text="系统状态")
        self._setup_status_tab()
    
    def _setup_battle_tab(self):
        """设置对战标签页"""
        # 主框架
        main_frame = ttk.Frame(self.battle_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左右分栏
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 英雄选择区域
        self._setup_hero_selection(left_frame)
        
        # 战斗控制区域
        self._setup_battle_controls(right_frame)
    
    def _setup_hero_selection(self, parent):
        """设置英雄选择区域"""
        # 英雄1选择
        hero1_frame = ttk.LabelFrame(parent, text="英雄1选择")
        hero1_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(hero1_frame, text="选择英雄:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.hero1_var = tk.StringVar()
        self.hero1_combo = ttk.Combobox(hero1_frame, textvariable=self.hero1_var, values=[])
        self.hero1_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.hero1_combo.bind('<<ComboboxSelected>>', lambda e: self._on_hero1_selected())
        
        ttk.Label(hero1_frame, text="选择等级:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.level1_var = tk.StringVar()
        self.level1_combo = ttk.Combobox(hero1_frame, textvariable=self.level1_var, values=[])
        self.level1_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.level1_combo.bind('<<ComboboxSelected>>', lambda e: self._load_hero_details(1))
        self.level1_combo.bind('<KeyRelease>', lambda e: self._on_level_changed(1))
        self.level1_combo.bind('<FocusOut>', lambda e: self._on_level_changed(1))
        
        # 英雄1详情
        self.hero1_details = scrolledtext.ScrolledText(hero1_frame, height=8, width=40)
        self.hero1_details.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        self.hero1_details.configure(state='disabled')
        
        hero1_frame.columnconfigure(1, weight=1)
        
        # 英雄2选择
        hero2_frame = ttk.LabelFrame(parent, text="英雄2选择")
        hero2_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(hero2_frame, text="选择英雄:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.hero2_var = tk.StringVar()
        self.hero2_combo = ttk.Combobox(hero2_frame, textvariable=self.hero2_var, values=[])
        self.hero2_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.hero2_combo.bind('<<ComboboxSelected>>', lambda e: self._on_hero2_selected())
        
        ttk.Label(hero2_frame, text="选择等级:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.level2_var = tk.StringVar()
        self.level2_combo = ttk.Combobox(hero2_frame, textvariable=self.level2_var, values=[])
        self.level2_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.level2_combo.bind('<<ComboboxSelected>>', lambda e: self._load_hero_details(2))
        self.level2_combo.bind('<KeyRelease>', lambda e: self._on_level_changed(2))
        self.level2_combo.bind('<FocusOut>', lambda e: self._on_level_changed(2))
        
        # 英雄2详情
        self.hero2_details = scrolledtext.ScrolledText(hero2_frame, height=8, width=40)
        self.hero2_details.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        self.hero2_details.configure(state='disabled')
        
        hero2_frame.columnconfigure(1, weight=1)
    
    def _setup_battle_controls(self, parent):
        """设置战斗控制区域"""
        # 战斗设置
        settings_frame = ttk.LabelFrame(parent, text="战斗设置")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="最大回合:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_turns_var = tk.IntVar(value=50)
        ttk.Entry(settings_frame, textvariable=self.max_turns_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="战斗速度:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.speed_var = tk.StringVar(value="normal")
        speed_combo = ttk.Combobox(settings_frame, textvariable=self.speed_var, 
                                  values=["slow", "normal", "fast"], width=10)
        speed_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 伤害公式参数设置
        ttk.Label(settings_frame, text="防御参数1:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        # 从配置文件读取当前参数值，而不是硬编码默认值
        from config import DAMAGE_FORMULA_PARAMS
        self.defense_param1_var = tk.IntVar(value=DAMAGE_FORMULA_PARAMS['defense_param1'])
        ttk.Entry(settings_frame, textvariable=self.defense_param1_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="防御参数2:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.defense_param2_var = tk.IntVar(value=DAMAGE_FORMULA_PARAMS['defense_param2'])
        ttk.Entry(settings_frame, textvariable=self.defense_param2_var, width=10).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="最小伤害:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_damage_var = tk.IntVar(value=DAMAGE_FORMULA_PARAMS['min_damage'])
        ttk.Entry(settings_frame, textvariable=self.min_damage_var, width=10).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 应用参数按钮
        ttk.Button(settings_frame, text="应用参数", command=self._apply_damage_params).grid(row=5, column=0, columnspan=2, pady=5)
        
        # 战斗按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="开始战斗", command=self._start_battle).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="快速战斗", command=self._quick_battle).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空选择", command=self._clear_selection).pack(side=tk.LEFT, padx=5)
        
        # 战斗日志
        log_frame = ttk.LabelFrame(parent, text="战斗日志")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.battle_log = scrolledtext.ScrolledText(log_frame, height=20)
        self.battle_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.battle_log.configure(state='disabled')
    
    def _setup_plugin_tab(self):
        """设置插件管理标签页"""
        # 这里可以集成现有的PluginEditor
        info_frame = ttk.Frame(self.plugin_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="插件系统状态:").pack(side=tk.LEFT)
        
        # 插件统计信息
        stats_frame = ttk.Frame(self.plugin_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(stats_frame, text="已加载插件: 0").pack(side=tk.LEFT, padx=5)
        ttk.Label(stats_frame, text="可用插件: 0").pack(side=tk.LEFT, padx=5)
        
        # 插件操作按钮
        button_frame = ttk.Frame(self.plugin_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="打开插件编辑器", command=self._open_plugin_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重新加载插件", command=self._reload_plugins).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看插件配置", command=self._show_plugin_config).pack(side=tk.LEFT, padx=5)
        
        # 插件列表
        plugin_list_frame = ttk.LabelFrame(self.plugin_frame, text="已加载插件")
        plugin_list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name", "version", "author", "skill_type", "enabled")
        self.plugin_tree = ttk.Treeview(plugin_list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.plugin_tree.heading(col, text=col.capitalize())
            self.plugin_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(plugin_list_frame, orient=tk.VERTICAL, command=self.plugin_tree.yview)
        self.plugin_tree.configure(yscrollcommand=scrollbar.set)
        
        self.plugin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_skill_chain_tab(self):
        """设置技能链管理标签页"""
        # 技能链信息
        info_frame = ttk.Frame(self.skill_chain_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="技能链系统状态:").pack(side=tk.LEFT)
        
        # 技能链统计
        stats_frame = ttk.Frame(self.skill_chain_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(stats_frame, text="已加载技能链: 0").pack(side=tk.LEFT, padx=5)
        
        # 技能链操作按钮
        button_frame = ttk.Frame(self.skill_chain_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="加载技能链", command=self._load_skill_chains).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self._refresh_skill_chains).pack(side=tk.LEFT, padx=5)
        
        # 技能链列表
        chain_list_frame = ttk.LabelFrame(self.skill_chain_frame, text="技能链列表")
        chain_list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name", "type", "skills", "cooldown", "damage_bonus")
        self.chain_tree = ttk.Treeview(chain_list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.chain_tree.heading(col, text=col.capitalize())
            self.chain_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(chain_list_frame, orient=tk.VERTICAL, command=self.chain_tree.yview)
        self.chain_tree.configure(yscrollcommand=scrollbar.set)
        
        self.chain_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_status_tab(self):
        """设置系统状态标签页"""
        # 系统信息
        sys_info_frame = ttk.LabelFrame(self.status_frame, text="系统信息")
        sys_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = scrolledtext.ScrolledText(sys_info_frame, height=8)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.info_text.configure(state='normal')
        
        # 初始显示系统信息
        self._update_status_display()
        
        self.info_text.configure(state='disabled')
        
        # 操作按钮
        button_frame = ttk.Frame(self.status_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="清理缓存", command=self._clear_cache).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重新加载数据", command=self._reload_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出报告", command=self._export_report).pack(side=tk.LEFT, padx=5)
    
    def _load_data(self):
        """加载数据"""
        try:
            # 配置验证
            if not config.validate_config():
                messagebox.showerror("错误", "配置验证失败，请检查配置文件")
                return
            
            # 加载数据
            excel_path = config.excel_path
            self.heroes_data = HeroDataLoader.load_hero_data(excel_path)
            self.skills_data = HeroDataLoader.load_skills_data(excel_path)
            
            if not self.heroes_data:
                messagebox.showerror("错误", "无法加载英雄数据")
                return
            
            # 获取基础英雄列表
            self.base_heroes = HeroDataLoader.get_base_heroes(self.heroes_data)
            
            # 更新UI
            self._update_hero_comboboxes()
            
            # 加载插件和技能链
            self._load_plugins()
            self._load_skill_chains()
            
            # 更新系统状态显示
            self._update_status_display()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")

    def _update_status_display(self):
        """更新系统状态显示"""
        if hasattr(self, 'info_text'):
            self.info_text.configure(state='normal')
            self.info_text.delete(1.0, tk.END)
            
            # 显示系统信息
            self.info_text.insert(tk.END, "=== 系统状态 ===\n")
            self.info_text.insert(tk.END, f"英雄数据: {len(self.heroes_data)} 条记录\n")
            self.info_text.insert(tk.END, f"技能数据: {len(self.skills_data)} 条记录\n")
            self.info_text.insert(tk.END, f"基础英雄: {len(self.base_heroes)} 个\n")
            self.info_text.insert(tk.END, f"缓存状态: {cache_manager.get_cache_stats()}\n")
            self.info_text.insert(tk.END, f"配置状态: 正常\n")
            
            self.info_text.configure(state='disabled')

    def _update_hero_comboboxes(self):
        """更新英雄选择下拉框"""
        # 更新英雄选择下拉框
        if hasattr(self, 'hero1_combo') and hasattr(self, 'hero2_combo'):
            self.hero1_combo['values'] = self.base_heroes
            self.hero2_combo['values'] = self.base_heroes
    
    def _on_hero1_selected(self):
        """英雄1选择事件 - 动态更新等级选择并自动加载详情"""
        hero_name = self.hero1_var.get()
        if hero_name:
            level_range = HeroDataLoader.get_hero_level_range(hero_name, self.heroes_data)
            levels = list(range(level_range['min'], level_range['max'] + 1))
            self.level1_combo['values'] = levels
            
            # 自动选择第一个可用等级并加载详情
            if levels:
                self.level1_var.set(str(levels[0]))
                self._load_hero_details(1)

    def _on_hero2_selected(self):
        """英雄2选择事件 - 动态更新等级选择并自动加载详情"""
        hero_name = self.hero2_var.get()
        if hero_name:
            level_range = HeroDataLoader.get_hero_level_range(hero_name, self.heroes_data)
            levels = list(range(level_range['min'], level_range['max'] + 1))
            self.level2_combo['values'] = levels
            
            # 自动选择第一个可用等级并加载详情
            if levels:
                self.level2_var.set(str(levels[0]))
                self._load_hero_details(2)

    def _on_level_changed(self, hero_num):
        """等级变化事件 - 动态更新英雄详情"""
        if hero_num == 1:
            hero_name = self.hero1_var.get()
            level_str = self.level1_var.get()
        else:
            hero_name = self.hero2_var.get()
            level_str = self.level2_var.get()
        
        # 只有当英雄和等级都有效时才加载详情
        if hero_name and level_str and level_str.isdigit():
            self._load_hero_details(hero_num)
    
    def _load_hero_details(self, hero_num):
        """加载英雄详细信息"""
        try:
            if hero_num == 1:
                hero_name = self.hero1_var.get()
                level = int(self.level1_var.get())
                text_widget = self.hero1_details
            else:
                hero_name = self.hero2_var.get()
                level = int(self.level2_var.get())
                text_widget = self.hero2_details
            
            # 获取英雄数据
            filtered_heroes = HeroDataLoader.filter_heroes_by_name_and_level(self.heroes_data, hero_name, level)
            if not filtered_heroes:
                return
            
            hero_data = filtered_heroes[0]
            
            # 显示详细信息
            text_widget.configure(state='normal')
            text_widget.delete(1.0, tk.END)
            
            text_widget.insert(tk.END, f"=== {hero_name} Lv.{level} ===\n")
            text_widget.insert(tk.END, f"职业: {hero_data.get('职业', '未知')}\n")
            text_widget.insert(tk.END, f"品阶: {hero_data.get('品阶', '未知')}\n")
            text_widget.insert(tk.END, f"生命值(HP): {hero_data.get('HP', 0)}\n")
            text_widget.insert(tk.END, f"攻击力(ATK): {hero_data.get('ATK', 0)}\n")
            text_widget.insert(tk.END, f"防御力(DEF): {hero_data.get('DEF', 0)}\n")
            text_widget.insert(tk.END, f"攻速(SPD): {hero_data.get('SPD', 0)}\n")
            
            text_widget.configure(state='disabled')
            
            # 保存选择的英雄
            if hero_num == 1:
                self.selected_hero1 = hero_data
            else:
                self.selected_hero2 = hero_data
                
        except Exception as e:
            messagebox.showerror("错误", f"加载英雄详情失败: {e}")
    
    def _apply_damage_params(self):
        """应用伤害公式参数"""
        try:
            # 获取用户输入的参数值
            defense_param1 = self.defense_param1_var.get()
            defense_param2 = self.defense_param2_var.get()
            min_damage = self.min_damage_var.get()
            
            # 验证参数有效性
            if defense_param1 <= 0 or defense_param2 <= 0 or min_damage < 0:
                messagebox.showerror("错误", "参数值必须为正数")
                return
            
            # 更新配置参数
            from config import DAMAGE_FORMULA_PARAMS
            DAMAGE_FORMULA_PARAMS['defense_param1'] = defense_param1
            DAMAGE_FORMULA_PARAMS['defense_param2'] = defense_param2
            DAMAGE_FORMULA_PARAMS['min_damage'] = min_damage
            
            # 保存参数到配置文件
            self._save_damage_params_to_config(defense_param1, defense_param2, min_damage)
            
            # 显示成功消息
            messagebox.showinfo("成功", f"伤害公式参数已更新并保存:\n防御参数1: {defense_param1}\n防御参数2: {defense_param2}\n最小伤害: {min_damage}")
            
            # 记录到日志
            self._log_message(f"伤害公式参数已更新: 防御参数1={defense_param1}, 防御参数2={defense_param2}, 最小伤害={min_damage}")
            
        except Exception as e:
            messagebox.showerror("错误", f"应用参数失败: {e}")
    
    def _save_damage_params_to_config(self, defense_param1, defense_param2, min_damage):
        """保存伤害公式参数到配置文件"""
        try:
            import os
            config_file_path = os.path.join(os.path.dirname(__file__), 'config.py')
            
            # 读取当前配置文件内容
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 更新DAMAGE_FORMULA_PARAMS配置
            import re
            # 使用正则表达式替换参数值
            config_content = re.sub(
                r"'defense_param1': \d+", 
                f"'defense_param1': {defense_param1}", 
                config_content
            )
            config_content = re.sub(
                r"'defense_param2': \d+", 
                f"'defense_param2': {defense_param2}", 
                config_content
            )
            config_content = re.sub(
                r"'min_damage': \d+", 
                f"'min_damage': {min_damage}", 
                config_content
            )
            
            # 写回配置文件
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            self._log_message(f"伤害公式参数已保存到配置文件: {config_file_path}")
            
        except Exception as e:
            self._log_message(f"保存参数到配置文件失败: {e}")
            raise
    
    def _start_battle(self):
        """开始战斗"""
        if not self.selected_hero1 or not self.selected_hero2:
            messagebox.showwarning("警告", "请先选择两个英雄")
            return
        
        # 在新线程中运行战斗
        thread = threading.Thread(target=self._run_battle_thread)
        thread.daemon = True
        thread.start()
    
    def _run_battle_thread(self):
        """运行战斗线程"""
        try:
            # 创建英雄实例
            hero1 = Hero(self.selected_hero1, self.skills_data)
            hero2 = Hero(self.selected_hero2, self.skills_data)
            
            # 设置战斗模拟器
            simulator = BattleSimulator()
            simulator.setup_battle(hero1, hero2)
            
            # 清空日志
            self.battle_log.configure(state='normal')
            self.battle_log.delete(1.0, tk.END)
            self.battle_log.insert(tk.END, "=== 战斗开始 ===\n")
            self.battle_log.insert(tk.END, f"{hero1.name} vs {hero2.name}\n\n")
            self.battle_log.configure(state='disabled')
            
            # 运行战斗，传递最大回合数参数
            max_turns = self.max_turns_var.get()
            battle_result = simulator.run_battle(max_turns=max_turns)
            
            # 显示详细战斗日志
            if 'detailed_log' in battle_result:
                self._log_detailed_battle_log(battle_result['detailed_log'])
            
            # 显示战斗结果
            self._show_battle_result(battle_result)
            
        except Exception as e:
            self._log_message(f"战斗错误: {e}")
    
    def _log_detailed_battle_log(self, detailed_log):
        """记录详细战斗日志到GUI"""
        self.battle_log.configure(state='normal')
        for log_entry in detailed_log:
            self.battle_log.insert(tk.END, log_entry + "\n")
        self.battle_log.see(tk.END)
        self.battle_log.configure(state='disabled')
    
    def _quick_battle(self):
        """快速战斗"""
        # 实现快速战斗逻辑
        pass
    
    def _clear_selection(self):
        """清空选择"""
        self.hero1_var.set("")
        self.hero2_var.set("")
        self.level1_var.set("")
        self.level2_var.set("")
        self.selected_hero1 = None
        self.selected_hero2 = None
        
        self.hero1_details.configure(state='normal')
        self.hero1_details.delete(1.0, tk.END)
        self.hero1_details.configure(state='disabled')
        
        self.hero2_details.configure(state='normal')
        self.hero2_details.delete(1.0, tk.END)
        self.hero2_details.configure(state='disabled')
        
        self.battle_log.configure(state='normal')
        self.battle_log.delete(1.0, tk.END)
        self.battle_log.configure(state='disabled')
    
    def _show_battle_result(self, result):
        """显示战斗结果"""
        self.battle_log.configure(state='normal')
        self.battle_log.insert(tk.END, f"\n=== 战斗结果 ===\n")
        self.battle_log.insert(tk.END, f"胜利者: {result['winner']}\n")
        self.battle_log.insert(tk.END, f"战斗回合: {result['turns']}\n")
        self.battle_log.insert(tk.END, f"剩余生命: {result['winner_health']}\n")
        self.battle_log.configure(state='disabled')
    
    def _log_message(self, message):
        """记录消息到日志"""
        self.battle_log.configure(state='normal')
        self.battle_log.insert(tk.END, message + "\n")
        self.battle_log.see(tk.END)
        self.battle_log.configure(state='disabled')
    
    def _load_plugins(self):
        """加载插件"""
        try:
            self.plugin_manager.discover_plugins()
            loaded_plugins = self.plugin_manager.get_loaded_plugins()
            
            # 更新插件树
            self.plugin_tree.delete(*self.plugin_tree.get_children())
            for plugin_name in loaded_plugins:
                plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
                if plugin_info:
                    self.plugin_tree.insert("", tk.END, values=(
                        plugin_info.get('name', ''),
                        plugin_info.get('version', ''),
                        plugin_info.get('author', ''),
                        plugin_info.get('skill_type', ''),
                        "是" if plugin_info.get('enabled', False) else "否"
                    ))
            
        except Exception as e:
            messagebox.showerror("错误", f"加载插件失败: {e}")
    
    def _load_skill_chains(self):
        """加载技能链"""
        try:
            self.skill_chain_manager.load_chains()
            chains = self.skill_chain_manager.chains
            
            # 更新技能链树
            self.chain_tree.delete(*self.chain_tree.get_children())
            for chain_name, chain_data in chains.items():
                self.chain_tree.insert("", tk.END, values=(
                    chain_data.name,
                    chain_data.chain_type.value,
                    ", ".join(chain_data.skill_names),
                    chain_data.cooldown,
                    f"{chain_data.damage_multiplier}x" if chain_data.damage_multiplier > 1.0 else "无"
                ))
            
        except Exception as e:
            messagebox.showerror("错误", f"加载技能链失败: {e}")
    
    def _open_plugin_editor(self):
        """打开插件编辑器"""
        editor_window = tk.Toplevel(self.root)
        editor_window.title("插件编辑器")
        editor_window.geometry("900x700")
        
        PluginEditor(editor_window)
    
    def _reload_plugins(self):
        """重新加载插件"""
        self._load_plugins()
        messagebox.showinfo("成功", "插件已重新加载")
    
    def _show_plugin_config(self):
        """显示插件配置"""
        # 实现插件配置显示
        pass
    
    def _refresh_skill_chains(self):
        """刷新技能链列表"""
        self._load_skill_chains()
        messagebox.showinfo("成功", "技能链列表已刷新")
    
    def _clear_cache(self):
        """清理缓存"""
        cache_manager.clear_cache()
        messagebox.showinfo("成功", "缓存已清理")
    
    def _reload_data(self):
        """重新加载数据"""
        self._load_data()
        messagebox.showinfo("成功", "数据已重新加载")
    
    def _export_report(self):
        """导出报告"""
        # 实现报告导出功能
        messagebox.showinfo("信息", "报告导出功能开发中")

    def _setup_skill_manager_tab(self):
        """设置技能管理标签页"""
        # 初始化技能管理器
        self.skill_manager = SkillManager()
        
        # 技能管理信息
        info_frame = ttk.Frame(self.skill_manager_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="技能管理系统状态:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(info_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # 技能统计信息
        stats_frame = ttk.Frame(self.skill_manager_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.total_skills_label = ttk.Label(stats_frame, text="总技能数: 0")
        self.total_skills_label.pack(side=tk.LEFT, padx=5)
        self.active_skills_label = ttk.Label(stats_frame, text="主动技能: 0")
        self.active_skills_label.pack(side=tk.LEFT, padx=5)
        self.passive_skills_label = ttk.Label(stats_frame, text="被动技能: 0")
        self.passive_skills_label.pack(side=tk.LEFT, padx=5)
        self.modified_label = ttk.Label(stats_frame, text="已修改: 0")
        self.modified_label.pack(side=tk.LEFT, padx=5)
        
        # 技能操作按钮
        button_frame = ttk.Frame(self.skill_manager_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="加载技能数据", command=self._load_skills_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="新增技能", command=self._add_new_skill).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="打开技能编辑器", command=self._open_skill_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除技能", command=self._delete_skill).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="验证技能数据", command=self._validate_skills).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存修改", command=self._save_skills).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="撤销修改", command=self._revert_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看修改", command=self._show_modifications).pack(side=tk.LEFT, padx=5)
        
        # 技能列表
        skill_list_frame = ttk.LabelFrame(self.skill_manager_frame, text="技能列表")
        skill_list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name", "type", "cd", "level1", "level2", "level3", "level4", "level5")
        self.skill_tree = ttk.Treeview(skill_list_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        column_widths = {"name": 120, "type": 80, "cd": 50, "level1": 60, "level2": 60, 
                        "level3": 60, "level4": 60, "level5": 60}
        
        for col in columns:
            self.skill_tree.heading(col, text=col.capitalize())
            self.skill_tree.column(col, width=column_widths.get(col, 80))
        
        scrollbar = ttk.Scrollbar(skill_list_frame, orient=tk.VERTICAL, command=self.skill_tree.yview)
        self.skill_tree.configure(yscrollcommand=scrollbar.set)
        
        self.skill_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.skill_tree.bind("<Double-1>", self._on_skill_double_click)

    def _load_skills_data(self):
        """加载技能数据"""
        try:
            self.status_label.config(text="正在加载技能数据...")
            
            # 重新初始化技能管理器以获取最新数据
            self.skill_manager = SkillManager()
            skills_data = self.skill_manager.skills_data
            
            # 更新技能树
            self.skill_tree.delete(*self.skill_tree.get_children())
            
            for skill_data in skills_data:
                self.skill_tree.insert("", tk.END, values=(
                    skill_data.get('技能名称', ''),
                    skill_data.get('技能类型', ''),
                    skill_data.get('技能CD', ''),
                    skill_data.get('Level1', ''),
                    skill_data.get('Level2', ''),
                    skill_data.get('Level3', ''),
                    skill_data.get('Level4', ''),
                    skill_data.get('Level5', '')
                ))
            
            # 更新统计信息
            self._update_skill_stats()
            
            self.status_label.config(text="就绪")
            messagebox.showinfo("成功", f"已加载 {len(skills_data)} 个技能")
            
        except Exception as e:
            self.status_label.config(text="加载失败")
            messagebox.showerror("错误", f"加载技能数据失败: {e}")
    
    def _update_skill_stats(self):
        """更新技能统计信息"""
        skills_data = self.skill_manager.skills_data
        total_skills = len(skills_data)
        active_skills = sum(1 for skill in skills_data if str(skill.get('技能类型', '')).strip() in ['1', 1])
        passive_skills = sum(1 for skill in skills_data if str(skill.get('技能类型', '')).strip() in ['2', 2])
        modified_count = len(self.skill_manager.get_modified_skills())
        
        self.total_skills_label.config(text=f"总技能数: {total_skills}")
        self.active_skills_label.config(text=f"主动技能: {active_skills}")
        self.passive_skills_label.config(text=f"被动技能: {passive_skills}")
        self.modified_label.config(text=f"已修改: {modified_count}")
        
        # 如果有修改，显示警告颜色
        if modified_count > 0:
            self.modified_label.config(foreground="orange")
        else:
            self.modified_label.config(foreground="black")

    def _open_skill_editor(self, skill_name=None, is_new_skill=False):
        """打开技能编辑器
        
        Args:
            skill_name: 技能名称，如果为None且is_new_skill=False则获取选中技能
            is_new_skill: 是否为新建技能
        """
        # 如果是编辑现有技能但没有传入skill_name，则获取选中的技能
        if skill_name is None and not is_new_skill:
            # 获取当前选中的技能
            selected_item = self.skill_tree.selection()
            if not selected_item:
                messagebox.showwarning("警告", "请先选择一个技能")
                return
            
            # 获取技能数据
            item_values = self.skill_tree.item(selected_item[0], 'values')
            skill_name = item_values[0]
        
        # 打开技能编辑器窗口
        editor_window = tk.Toplevel(self.root)
        if skill_name:
            editor_window.title(f"技能编辑器 - {skill_name}")
        else:
            editor_window.title("新建技能")
        editor_window.geometry("800x600")
        
        # 这里可以集成SkillEditor类
        self._setup_skill_editor(editor_window, skill_name)

    def _setup_skill_editor(self, parent, skill_name):
        """设置技能编辑器"""
        # 初始化技能编辑器
        self.skill_editor = SkillEditor()
        
        # 获取技能数据
        skill_data = None
        if skill_name:
            # 尝试从技能编辑器加载技能
            skill_data = self.skill_editor.load_skill_from_file(skill_name + ".json")
            
            # 如果从技能编辑器加载失败（返回None），尝试从技能管理器加载
            if skill_data is None:
                for skill in self.skill_manager.skills_data:
                    if skill.get('技能名称') == skill_name:
                        skill_data = skill
                        break
            
            if not skill_data:
                messagebox.showerror("错误", f"未找到技能: {skill_name}")
                return
        else:
            # 使用技能编辑器创建新技能模板
            skill_data = self.skill_editor.generate_skill_template()
        
        # 创建编辑器框架
        editor_frame = ttk.Frame(parent, padding="10")
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # 技能基本信息
        info_frame = ttk.LabelFrame(editor_frame, text="技能基本信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 技能名称
        ttk.Label(info_frame, text="技能名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar(value=skill_data.get('name', skill_data.get('技能名称', '')))
        name_entry = ttk.Entry(info_frame, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 技能描述
        ttk.Label(info_frame, text="技能描述:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        description_var = tk.StringVar(value=skill_data.get('description', ''))
        description_entry = ttk.Entry(info_frame, textvariable=description_var, width=30)
        description_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 技能类型
        ttk.Label(info_frame, text="技能类型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        skill_type_var = tk.StringVar(value=skill_data.get('skill_type', 'damage'))
        skill_type_combo = ttk.Combobox(info_frame, textvariable=skill_type_var, 
                                       values=[st.value for st in SkillType], width=12)
        skill_type_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # 目标类型
        ttk.Label(info_frame, text="目标类型:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        target_type_var = tk.StringVar(value=skill_data.get('target_type', 'single_enemy'))
        target_type_combo = ttk.Combobox(info_frame, textvariable=target_type_var, 
                                       values=[tt.value for tt in TargetType], width=12)
        target_type_combo.grid(row=1, column=3, padx=5, pady=5)
        
        # 冷却时间
        ttk.Label(info_frame, text="冷却时间:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        cooldown_var = tk.StringVar(value=str(skill_data.get('cooldown', skill_data.get('技能CD', 3))))
        cooldown_entry = ttk.Entry(info_frame, textvariable=cooldown_var, width=8)
        cooldown_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # 魔法消耗
        ttk.Label(info_frame, text="魔法消耗:").grid(row=1, column=4, sticky=tk.W, padx=5, pady=5)
        mana_cost_var = tk.StringVar(value=str(skill_data.get('mana_cost', 0)))
        mana_cost_entry = ttk.Entry(info_frame, textvariable=mana_cost_var, width=8)
        mana_cost_entry.grid(row=1, column=5, padx=5, pady=5)
        
        # 伤害类型（仅对伤害类技能）
        ttk.Label(info_frame, text="伤害类型:").grid(row=0, column=6, sticky=tk.W, padx=5, pady=5)
        damage_type_var = tk.StringVar(value=skill_data.get('damage_type', DamageType.PHYSICAL.value))
        damage_type_combo = ttk.Combobox(info_frame, textvariable=damage_type_var, 
                                       values=[dt.value for dt in DamageType], width=12)
        damage_type_combo.grid(row=0, column=7, padx=5, pady=5)
        
        # 基础伤害
        ttk.Label(info_frame, text="基础伤害:").grid(row=1, column=6, sticky=tk.W, padx=5, pady=5)
        base_damage_var = tk.StringVar(value=str(skill_data.get('base_damage', 100)))
        base_damage_entry = ttk.Entry(info_frame, textvariable=base_damage_var, width=8)
        base_damage_entry.grid(row=1, column=7, padx=5, pady=5)
        
        # 等级数值编辑区域
        level_frame = ttk.LabelFrame(editor_frame, text="等级数值")
        level_frame.pack(fill=tk.X, pady=(10, 10))
        
        # 创建5个等级的数值输入框
        level_vars = {}
        for i in range(1, 6):
            ttk.Label(level_frame, text=f"等级 {i}:").grid(row=0, column=(i-1)*2, padx=5, pady=5)
            level_var = tk.StringVar(value=str(skill_data.get('level_values', {}).get(i, 0.2)))
            level_entry = ttk.Entry(level_frame, textvariable=level_var, width=8)
            level_entry.grid(row=0, column=(i-1)*2+1, padx=5, pady=5)
            level_vars[i] = level_var
        
        # 按钮区域
        button_frame = ttk.Frame(editor_frame)
        button_frame.pack(fill=tk.X)
        
        def save_changes():
            """保存修改"""
            try:
                # 创建新的技能数据
                skill_config = {
                    "name": name_var.get(),
                    "description": description_var.get(),
                    "skill_type": skill_type_var.get(),
                    "cooldown": int(cooldown_var.get()) if cooldown_var.get().isdigit() else 3,
                    "mana_cost": int(mana_cost_var.get()) if mana_cost_var.get().isdigit() else 0,
                    "target_type": target_type_var.get(),
                "damage_type": damage_type_var.get(),
                "base_damage": int(base_damage_var.get()) if base_damage_var.get().isdigit() else 100,
                "level_values": {
                    1: float(level_vars[1].get()) if level_vars[1].get().replace('.', '', 1).isdigit() else 0.2,
                    2: float(level_vars[2].get()) if level_vars[2].get().replace('.', '', 1).isdigit() else 0.3,
                    3: float(level_vars[3].get()) if level_vars[3].get().replace('.', '', 1).isdigit() else 0.4,
                    4: float(level_vars[4].get()) if level_vars[4].get().replace('.', '', 1).isdigit() else 0.5,
                    5: float(level_vars[5].get()) if level_vars[5].get().replace('.', '', 1).isdigit() else 0.6
                },
                "effects": []
                }
                
                # 使用技能编辑器创建技能
                custom_skill = self.skill_editor.create_custom_skill(skill_config)
                
                # 保存技能到文件
                filename = f"{name_var.get()}.json"
                if self.skill_editor.save_skill_to_file(custom_skill, filename):
                    messagebox.showinfo("成功", f"技能 '{name_var.get()}' 已保存到文件")
                    
                    # 清理技能数据缓存并重新加载数据
                    cache_manager.clear_cache('skills')
                    self._load_skills_data()
                    self._update_skill_stats()
                    
                    parent.destroy()
                else:
                    messagebox.showerror("错误", "保存技能失败")
                    
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=parent.destroy).pack(side=tk.LEFT, padx=5)

    def _validate_skills(self):
        """验证技能数据"""
        try:
            self.status_label.config(text="正在验证技能数据...")
            
            # 使用现有的验证器验证技能数据
            validator = DataValidator()
            validation_result = validator.validate_skill_data(self.skill_manager.skills_data)
            
            # 生成验证报告
            validation_report = validator.generate_validation_report(
                ValidationResult(),  # 空的英雄验证结果
                validation_result
            )
            
            # 显示验证结果
            result_window = tk.Toplevel(self.root)
            result_window.title("技能数据验证结果")
            result_window.geometry("800x500")
            
            # 创建标签页
            notebook = ttk.Notebook(result_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 详细报告标签页
            report_frame = ttk.Frame(notebook, padding="10")
            notebook.add(report_frame, text="详细报告")
            
            text_widget = scrolledtext.ScrolledText(report_frame)
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, validation_report)
            text_widget.configure(state='disabled')
            
            # 统计信息标签页
            stats_frame = ttk.Frame(notebook, padding="10")
            notebook.add(stats_frame, text="统计信息")
            
            stats_text = f"验证结果汇总:\n"
            stats_text += f"有效性: {'通过' if validation_result.is_valid else '失败'}\n"
            stats_text += f"错误数量: {len(validation_result.errors)}\n"
            stats_text += f"警告数量: {len(validation_result.warnings)}\n"
            stats_text += f"无效数值: {len(validation_result.invalid_values)}\n"
            
            if validation_result.errors:
                stats_text += f"\n错误详情:\n"
                for error in validation_result.errors[:10]:  # 显示前10个错误
                    stats_text += f"• {error}\n"
                if len(validation_result.errors) > 10:
                    stats_text += f"... 还有 {len(validation_result.errors) - 10} 个错误\n"
            
            stats_label = ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT)
            stats_label.pack(anchor=tk.W)
            
            self.status_label.config(text="就绪")
            
            if not validation_result.is_valid:
                messagebox.showwarning("警告", "技能数据验证发现错误，请查看详细报告")
            else:
                messagebox.showinfo("成功", "技能数据验证通过")
            
        except Exception as e:
            self.status_label.config(text="验证失败")
            messagebox.showerror("错误", f"验证技能数据失败: {e}")

    def _save_skills(self):
        """保存技能数据"""
        try:
            # 检查是否有修改
            modified_skills = self.skill_manager.get_modified_skills()
            if not modified_skills:
                messagebox.showinfo("信息", "没有需要保存的修改")
                return
            
            # 确认保存
            confirm = messagebox.askyesno(
                "确认保存", 
                f"确定要保存 {len(modified_skills)} 个技能的修改到Excel文件吗？\n\n"
                "此操作将覆盖原始数据，建议先备份文件。"
            )
            
            if not confirm:
                return
            
            self.status_label.config(text="正在保存技能数据...")
            
            # 保存到Excel
            if self.skill_manager.save_to_excel():
                # 清理缓存并重新加载数据以更新状态
                cache_manager.clear_cache('skills')
                self.skill_manager._load_skills_data()
                self._load_skills_data()
                self._update_skill_stats()
                
                self.status_label.config(text="就绪")
                messagebox.showinfo("成功", f"已成功保存 {len(modified_skills)} 个技能的修改")
            else:
                self.status_label.config(text="保存失败")
                messagebox.showerror("错误", "保存技能数据失败")
                
        except Exception as e:
            self.status_label.config(text="保存失败")
            messagebox.showerror("错误", f"保存技能数据失败: {e}")

    def _on_skill_double_click(self, event):
        """技能树双击事件"""
        self._open_skill_editor()
    
    def _revert_changes(self):
        """撤销所有修改"""
        try:
            modified_skills = self.skill_manager.get_modified_skills()
            if not modified_skills:
                messagebox.showinfo("信息", "没有需要撤销的修改")
                return
            
            confirm = messagebox.askyesno(
                "确认撤销", 
                f"确定要撤销 {len(modified_skills)} 个技能的修改吗？\n\n"
                "此操作将丢失所有未保存的修改。"
            )
            
            if confirm:
                # 重新加载原始数据
                self.skill_manager._load_skills_data()
                self._load_skills_data()  # 刷新界面
                messagebox.showinfo("成功", "所有修改已撤销")
                
        except Exception as e:
            messagebox.showerror("错误", f"撤销修改失败: {e}")
    
    def _show_modifications(self):
        """显示修改详情"""
        try:
            modified_skills = self.skill_manager.get_modified_skills()
            if not modified_skills:
                messagebox.showinfo("信息", "没有检测到修改")
                return
            
            # 创建修改详情窗口
            mod_window = tk.Toplevel(self.root)
            mod_window.title("技能修改详情")
            mod_window.geometry("800x500")
            
            # 创建文本区域
            text_widget = scrolledtext.ScrolledText(mod_window)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 生成修改报告
            report = f"技能修改详情 (共 {len(modified_skills)} 个技能)\n"
            report += "=" * 50 + "\n\n"
            
            for mod in modified_skills:
                skill_name = mod['current'].get('技能名称', '未知')
                hero_name = mod['current'].get('名称', '未知')
                
                report += f"技能: {skill_name} (英雄: {hero_name})\n"
                report += "-" * 30 + "\n"
                
                for change in mod['changes']:
                    report += f"  {change}\n"
                
                report += "\n"
            
            text_widget.insert(tk.END, report)
            text_widget.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("错误", f"显示修改详情失败: {e}")

    def _add_new_skill(self):
        """新增技能"""
        # 打开技能编辑器创建新技能
        self._open_skill_editor(skill_name=None, is_new_skill=True)

    def _delete_skill(self):
        """删除选中的技能"""
        try:
            # 获取当前选中的技能
            selected_item = self.skill_tree.selection()
            if not selected_item:
                messagebox.showwarning("警告", "请先选择一个技能")
                return
            
            # 获取技能数据
            item_values = self.skill_tree.item(selected_item[0], 'values')
            skill_name = item_values[0]
            
            # 查找技能对应的英雄名称
            hero_name = None
            for skill in self.skill_manager.skills_data:
                if skill.get('技能名称') == skill_name:
                    hero_name = skill.get('名称')
                    break
            
            if not hero_name:
                messagebox.showerror("错误", f"未找到技能 '{skill_name}' 对应的英雄信息")
                return
            
            # 确认删除
            confirm = messagebox.askyesno(
                "确认删除", 
                f"确定要删除技能 '{skill_name}' (英雄: {hero_name}) 吗？\n\n"
                "此操作不可撤销，建议先备份数据。"
            )
            
            if not confirm:
                return
            
            # 删除技能
            if self.skill_manager.delete_skill(skill_name, hero_name):
                # 刷新界面
                self._load_skills_data()
                messagebox.showinfo("成功", f"已删除技能: {skill_name}")
            else:
                messagebox.showerror("错误", f"删除技能 '{skill_name}' 失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"删除技能失败: {e}")


def main():
    """主函数"""
    root = tk.Tk()
    app = BattleSimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()