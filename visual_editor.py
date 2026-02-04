#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化编辑器模块
提供图形化界面用于插件创建和编辑
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class PluginEditor:
    """插件可视化编辑器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("技能插件可视化编辑器")
        self.root.geometry("800x600")
        
        # 当前编辑的插件信息
        self.current_plugin: Optional[Dict[str, Any]] = None
        self.plugins_dir = "plugins"
        
        self._setup_ui()
        self._load_plugins_list()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 插件列表区域
        plugins_frame = ttk.LabelFrame(main_frame, text="插件列表", padding="5")
        plugins_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 插件列表
        self.plugins_listbox = tk.Listbox(plugins_frame, width=20, height=15)
        self.plugins_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.plugins_listbox.bind('<<ListboxSelect>>', self._on_plugin_select)
        
        # 插件列表滚动条
        scrollbar = ttk.Scrollbar(plugins_frame, orient=tk.VERTICAL, command=self.plugins_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.plugins_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 插件操作按钮
        button_frame = ttk.Frame(plugins_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(button_frame, text="新建插件", command=self._create_new_plugin).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="刷新列表", command=self._load_plugins_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="删除插件", command=self._delete_plugin).pack(side=tk.LEFT, padx=2)
        
        # 编辑区域
        editor_frame = ttk.LabelFrame(main_frame, text="插件编辑", padding="5")
        editor_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        editor_frame.columnconfigure(1, weight=1)
        
        # 基本信息
        ttk.Label(editor_frame, text="插件名称:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(editor_frame, text="版本:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.version_var = tk.StringVar(value="1.0.0")
        ttk.Entry(editor_frame, textvariable=self.version_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(editor_frame, text="作者:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.author_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.author_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # 技能类型
        ttk.Label(editor_frame, text="技能类型:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.skill_type_var = tk.StringVar(value="damage")
        skill_type_combo = ttk.Combobox(editor_frame, textvariable=self.skill_type_var, 
                                       values=["damage", "heal", "control", "buff", "debuff"])
        skill_type_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # 伤害/治疗值
        ttk.Label(editor_frame, text="基础值:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.base_value_var = tk.IntVar(value=100)
        ttk.Entry(editor_frame, textvariable=self.base_value_var).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # 冷却时间
        ttk.Label(editor_frame, text="冷却时间:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.cooldown_var = tk.IntVar(value=0)
        ttk.Entry(editor_frame, textvariable=self.cooldown_var).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # 技能描述
        ttk.Label(editor_frame, text="技能描述:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.description_text = scrolledtext.ScrolledText(editor_frame, height=4, width=40)
        self.description_text.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # 额外效果
        ttk.Label(editor_frame, text="额外效果:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.effects_text = scrolledtext.ScrolledText(editor_frame, height=3, width=40)
        self.effects_text.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # 保存按钮
        ttk.Button(editor_frame, text="保存插件", command=self._save_plugin).grid(row=8, column=1, sticky=tk.E, pady=10)
        
        # 代码预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="代码预览", padding="5")
        preview_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=15)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.preview_text.configure(state='disabled')
    
    def _load_plugins_list(self):
        """加载插件列表"""
        self.plugins_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            return
        
        # 查找所有Python插件文件
        plugin_files = []
        for file in os.listdir(self.plugins_dir):
            if file.endswith('.py') and file != '__init__.py':
                plugin_files.append(file[:-3])  # 移除.py后缀
        
        for plugin_name in sorted(plugin_files):
            self.plugins_listbox.insert(tk.END, plugin_name)
    
    def _on_plugin_select(self, event):
        """选择插件事件"""
        selection = self.plugins_listbox.curselection()
        if not selection:
            return
        
        plugin_name = self.plugins_listbox.get(selection[0])
        self._load_plugin(plugin_name)
    
    def _load_plugin(self, plugin_name: str):
        """加载插件内容"""
        plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
        
        if not os.path.exists(plugin_path):
            messagebox.showerror("错误", f"插件文件不存在: {plugin_path}")
            return
        
        try:
            # 读取插件文件内容
            with open(plugin_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析插件信息（简化实现）
            plugin_info = self._parse_plugin_content(content, plugin_name)
            
            # 更新UI
            self.name_var.set(plugin_info.get('name', ''))
            self.version_var.set(plugin_info.get('version', '1.0.0'))
            self.author_var.set(plugin_info.get('author', ''))
            self.skill_type_var.set(plugin_info.get('skill_type', 'damage'))
            self.base_value_var.set(plugin_info.get('base_value', 100))
            self.cooldown_var.set(plugin_info.get('cooldown', 0))
            
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(1.0, plugin_info.get('description', ''))
            
            self.effects_text.delete(1.0, tk.END)
            self.effects_text.insert(1.0, plugin_info.get('effects', ''))
            
            # 更新代码预览
            self._update_preview()
            
            self.current_plugin = plugin_info
            
        except Exception as e:
            messagebox.showerror("错误", f"加载插件失败: {e}")
    
    def _parse_plugin_content(self, content: str, plugin_name: str) -> Dict[str, Any]:
        """解析插件文件内容"""
        # 简化实现：从代码中提取信息
        info = {
            'name': plugin_name,
            'version': '1.0.0',
            'author': '未知',
            'skill_type': 'damage',
            'base_value': 100,
            'cooldown': 0,
            'description': '',
            'effects': ''
        }
        
        # 尝试从代码中提取信息
        lines = content.split('\n')
        for line in lines:
            if '__version__' in line and '=' in line:
                info['version'] = line.split('=')[1].strip().strip('"\'')
            elif '__author__' in line and '=' in line:
                info['author'] = line.split('=')[1].strip().strip('"\'')
            elif 'get_skill_name' in line and 'return' in line:
                info['name'] = line.split('return')[1].strip().strip('"\'')
            elif 'get_skill_description' in line and 'return' in line:
                info['description'] = line.split('return')[1].strip().strip('"\'')
        
        return info
    
    def _create_new_plugin(self):
        """创建新插件"""
        # 清空编辑区域
        self.name_var.set("")
        self.version_var.set("1.0.0")
        self.author_var.set("")
        self.skill_type_var.set("damage")
        self.base_value_var.set(100)
        self.cooldown_var.set(0)
        self.description_text.delete(1.0, tk.END)
        self.effects_text.delete(1.0, tk.END)
        
        self.current_plugin = None
        self._update_preview()
    
    def _save_plugin(self):
        """保存插件"""
        plugin_name = self.name_var.get().strip()
        if not plugin_name:
            messagebox.showerror("错误", "请输入插件名称")
            return
        
        try:
            # 生成插件代码
            plugin_code = self._generate_plugin_code()
            
            # 保存到文件
            plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
            
            with open(plugin_path, 'w', encoding='utf-8') as f:
                f.write(plugin_code)
            
            messagebox.showinfo("成功", f"插件 {plugin_name} 保存成功")
            self._load_plugins_list()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存插件失败: {e}")
    
    def _delete_plugin(self):
        """删除插件"""
        selection = self.plugins_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的插件")
            return
        
        plugin_name = self.plugins_listbox.get(selection[0])
        plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
        
        if not os.path.exists(plugin_path):
            messagebox.showerror("错误", "插件文件不存在")
            return
        
        if messagebox.askyesno("确认", f"确定要删除插件 {plugin_name} 吗？"):
            try:
                os.remove(plugin_path)
                messagebox.showinfo("成功", f"插件 {plugin_name} 已删除")
                self._load_plugins_list()
                self._create_new_plugin()  # 清空编辑区域
            except Exception as e:
                messagebox.showerror("错误", f"删除插件失败: {e}")
    
    def _generate_plugin_code(self) -> str:
        """生成插件代码"""
        plugin_name = self.name_var.get().strip()
        version = self.version_var.get().strip()
        author = self.author_var.get().strip()
        skill_type = self.skill_type_var.get()
        base_value = self.base_value_var.get()
        cooldown = self.cooldown_var.get()
        description = self.description_text.get(1.0, tk.END).strip()
        effects = self.effects_text.get(1.0, tk.END).strip()
        
        # 根据技能类型生成不同的execute_skill方法
        execute_method = self._generate_execute_method(skill_type, base_value, effects)
        
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{plugin_name} 插件
{description}
"""

__version__ = "{version}"
__author__ = "{author}"

from core.plugin_manager import SkillPlugin
from typing import Dict, Any, Optional


class {plugin_name}Plugin(SkillPlugin):
    """{description}"""
    
    def get_skill_name(self) -> str:
        return "{plugin_name}"
    
    def get_skill_description(self) -> str:
        return "{description}"
    
    def get_cooldown(self) -> int:
        return {cooldown}
    
    def can_use_skill(self, hero, target) -> bool:
        """检查是否可以使用技能"""
        return True
    
{execute_method}

    def get_skill_type(self) -> str:
        return "{skill_type}"
'''
        
        return code
    
    def _generate_execute_method(self, skill_type: str, base_value: int, effects: str) -> str:
        """生成execute_skill方法"""
        if skill_type == "damage":
            return f'''    def execute_skill(self, hero, target) -> Dict[str, Any]:
        """执行技能：造成{base_value}点伤害"""
        damage = {base_value}
        target.health = max(0, target.health - damage)
        
        return {{
            'damage': damage,
            'is_crit': False,
            'target_health': target.health,
            'extra_effects': [],
            'message': f"{{hero.name}} 使用 {{self.get_skill_name()}} 对 {{target.name}} 造成 {{damage}} 点伤害"
        }}'''
        
        elif skill_type == "heal":
            return f'''    def execute_skill(self, hero, target) -> Dict[str, Any]:
        """执行技能：治疗{base_value}点生命值"""
        heal_amount = {base_value}
        target.health = min(target.max_health, target.health + heal_amount)
        
        return {{
            'damage': -heal_amount,  # 负伤害表示治疗
            'is_crit': False,
            'target_health': target.health,
            'extra_effects': [],
            'message': f"{{hero.name}} 使用 {{self.get_skill_name()}} 治疗 {{target.name}} {{heal_amount}} 点生命值"
        }}'''
        
        elif skill_type == "control":
            return f'''    def execute_skill(self, hero, target) -> Dict[str, Any]:
        """执行技能：控制效果"""
        # 添加控制效果
        target.status_effects.append({{
            'type': 'stun',
            'duration': 1,
            'message': "被眩晕"
        }})
        
        return {{
            'damage': 0,
            'is_crit': False,
            'target_health': target.health,
            'extra_effects': [{{'type': 'stun', 'duration': 1}}],
            'message': f"{{hero.name}} 使用 {{self.get_skill_name()}} 眩晕了 {{target.name}}"
        }}'''
        
        else:  # buff/debuff
            return f'''    def execute_skill(self, hero, target) -> Dict[str, Any]:
        """执行技能：增益/减益效果"""
        # 这里实现具体的buff/debuff逻辑
        return {{
            'damage': 0,
            'is_crit': False,
            'target_health': target.health,
            'extra_effects': [],
            'message': f"{{hero.name}} 使用 {{self.get_skill_name()}}"
        }}'''
    
    def _update_preview(self):
        """更新代码预览"""
        try:
            plugin_code = self._generate_plugin_code()
            self.preview_text.configure(state='normal')
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, plugin_code)
            self.preview_text.configure(state='disabled')
        except Exception as e:
            self.preview_text.configure(state='normal')
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"生成预览时出错: {e}")
            self.preview_text.configure(state='disabled')


def main():
    """主函数"""
    root = tk.Tk()
    app = PluginEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()