#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能管理器 - 提供技能数据的可视化编辑和管理功能
支持实时修改技能效果、持续时间、数值等参数
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
from typing import Dict, List, Optional, Any
import os
from pathlib import Path

from data.data_loader import HeroDataLoader
from data.data_validator import DataValidator
from core.config_manager import config


class SkillManager:
    """技能管理器类"""
    
    def __init__(self, excel_path: Optional[str] = None):
        """
        初始化技能管理器
        
        Args:
            excel_path: Excel文件路径，默认为配置中的路径
        """
        self.excel_path = excel_path or config.data.excel_path
        self.skills_data = []
        self.original_skills_data = []
        self._load_skills_data()
    
    def _load_skills_data(self) -> bool:
        """加载技能数据"""
        try:
            # 从Excel加载技能数据（不使用缓存以确保获取最新数据）
            self.skills_data = HeroDataLoader.load_skills_data(
                self.excel_path, 
                validate=False,  # 不验证，允许编辑时可能存在的临时无效数据
                use_cache=False   # 不使用缓存
            )
            
            # 保存原始数据副本用于比较
            self.original_skills_data = self.skills_data.copy()
            
            print(f"成功加载 {len(self.skills_data)} 条技能数据")
            return True
            
        except Exception as e:
            print(f"加载技能数据失败: {e}")
            self.skills_data = []
            self.original_skills_data = []
            return False
    
    def get_skill_by_name(self, skill_name: str, hero_name: Optional[str] = None) -> Optional[Dict]:
        """
        根据技能名称获取技能数据
        
        Args:
            skill_name: 技能名称
            hero_name: 英雄名称（可选，用于精确匹配）
            
        Returns:
            技能数据字典，如果未找到则返回None
        """
        for skill in self.skills_data:
            if skill.get('技能名称') == skill_name:
                if hero_name is None or skill.get('名称') == hero_name:
                    return skill
        return None
    
    def get_hero_skills(self, hero_name: str) -> List[Dict]:
        """
        获取指定英雄的所有技能
        
        Args:
            hero_name: 英雄名称
            
        Returns:
            该英雄的技能列表
        """
        return [skill for skill in self.skills_data 
                if skill.get('名称') == hero_name]
    
    def update_skill(self, skill_data: Dict) -> bool:
        """
        更新技能数据
        
        Args:
            skill_data: 包含更新后数据的技能字典
            
        Returns:
            是否成功更新
        """
        try:
            skill_name = skill_data.get('技能名称')
            hero_name = skill_data.get('名称')
            
            if not skill_name or not hero_name:
                return False
            
            # 查找并更新技能
            for i, skill in enumerate(self.skills_data):
                if (skill.get('技能名称') == skill_name and 
                    skill.get('名称') == hero_name):
                    self.skills_data[i] = skill_data
                    return True
            
            # 如果未找到，添加新技能
            self.skills_data.append(skill_data)
            return True
            
        except Exception as e:
            print(f"更新技能数据失败: {e}")
            return False

    def delete_skill(self, skill_name: str, hero_name: str) -> bool:
        """
        删除指定技能
        
        Args:
            skill_name: 技能名称
            hero_name: 英雄名称
            
        Returns:
            是否成功删除
        """
        try:
            # 查找技能索引
            for i, skill in enumerate(self.skills_data):
                if (skill.get('技能名称') == skill_name and 
                    skill.get('名称') == hero_name):
                    # 删除技能
                    del self.skills_data[i]
                    print(f"已删除技能: {skill_name} (英雄: {hero_name})")
                    return True
            
            print(f"未找到技能: {skill_name} (英雄: {hero_name})")
            return False
            
        except Exception as e:
            print(f"删除技能失败: {e}")
            return False
    
    def validate_skill_data(self, skill_data: Dict) -> Dict:
        """
        验证技能数据有效性
        
        Args:
            skill_data: 要验证的技能数据
            
        Returns:
            包含验证结果的字典
        """
        validator = DataValidator()
        result = validator.validate_skill_data([skill_data])
        
        return {
            'is_valid': result.is_valid,
            'errors': result.errors,
            'warnings': result.warnings,
            'invalid_values': result.invalid_values
        }
    
    def save_to_excel(self) -> bool:
        """
        将修改后的技能数据保存回Excel文件
        
        Returns:
            是否成功保存
        """
        try:
            # 读取原始Excel文件
            with pd.ExcelFile(self.excel_path) as xls:
                sheets = {sheet: pd.read_excel(xls, sheet_name=sheet) 
                         for sheet in xls.sheet_names}
            
            # 更新技能数据表
            skill_sheet = config.data.skill_data_sheet
            if skill_sheet in sheets:
                # 创建新的DataFrame
                new_skills_df = pd.DataFrame(self.skills_data)
                
                # 处理level_values字典和Level1-5字段的同步
                for i, skill in enumerate(new_skills_df.to_dict('records')):
                    # 检查Level1-5字段是否有用户修改的值
                    level_fields_modified = any(
                        f'Level{level}' in skill and skill[f'Level{level}'] is not None 
                        for level in range(1, 6)
                    )
                    
                    # 如果Level字段有用户修改的值，优先使用Level字段值更新level_values字典
                    if level_fields_modified:
                        level_values = {}
                        for level in range(1, 6):
                            level_key = f'Level{level}'
                            if level_key in skill and skill[level_key] is not None:
                                level_values[level] = skill[level_key]
                        new_skills_df.at[i, 'level_values'] = level_values
                    # 如果没有Level字段修改但有level_values字典，使用字典数据更新Level字段
                    elif 'level_values' in skill and isinstance(skill['level_values'], dict):
                        level_values = skill['level_values']
                        for level in range(1, 6):
                            level_key = f'Level{level}'
                            new_skills_df.at[i, level_key] = level_values.get(level, 0.0)
                
                # 保持原始列顺序
                original_columns = sheets[skill_sheet].columns.tolist()
                new_skills_df = new_skills_df.reindex(columns=original_columns, fill_value=None)
                
                sheets[skill_sheet] = new_skills_df
            
            # 写回Excel文件
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                for sheet_name, df in sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"技能数据已成功保存到 {self.excel_path}")
            return True
            
        except Exception as e:
            print(f"保存技能数据失败: {e}")
            return False
    
    def get_skill_summary(self) -> Dict:
        """
        获取技能数据统计摘要
        
        Returns:
            包含技能统计信息的字典
        """
        return HeroDataLoader.analyze_skills_by_type(self.skills_data)
    
    def get_modified_skills(self) -> List[Dict]:
        """
        获取已修改的技能列表
        
        Returns:
            包含修改信息的技能列表
        """
        modified = []
        for i, (orig, current) in enumerate(zip(self.original_skills_data, self.skills_data)):
            if orig != current:
                modified.append({
                    'index': i,
                    'original': orig,
                    'current': current,
                    'changes': self._get_changes(orig, current)
                })
        return modified
    
    def _get_changes(self, orig: Dict, current: Dict) -> List[str]:
        """获取两个字典之间的差异"""
        changes = []
        all_keys = set(orig.keys()) | set(current.keys())
        
        for key in all_keys:
            orig_val = orig.get(key)
            current_val = current.get(key)
            
            if orig_val != current_val:
                changes.append(f"{key}: {orig_val} -> {current_val}")
        
        return changes


def create_skill_manager_gui(parent, excel_path: Optional[str] = None) -> tk.Frame:
    """
    创建技能管理GUI界面
    
    Args:
        parent: 父级窗口或框架
        excel_path: Excel文件路径
        
    Returns:
        包含技能管理界面的Frame
    """
    frame = ttk.Frame(parent, padding="10")
    
    # 初始化技能管理器
    skill_manager = SkillManager(excel_path)
    
    # 创建界面组件
    _setup_skill_manager_ui(frame, skill_manager)
    
    return frame


def _setup_skill_manager_ui(parent, skill_manager: SkillManager):
    """设置技能管理界面"""
    
    # 顶部控制区域
    control_frame = ttk.Frame(parent)
    control_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 英雄选择
    ttk.Label(control_frame, text="选择英雄:").pack(side=tk.LEFT, padx=5)
    hero_var = tk.StringVar()
    hero_combo = ttk.Combobox(control_frame, textvariable=hero_var, width=20)
    hero_combo.pack(side=tk.LEFT, padx=5)
    
    # 技能选择
    ttk.Label(control_frame, text="选择技能:").pack(side=tk.LEFT, padx=5)
    skill_var = tk.StringVar()
    skill_combo = ttk.Combobox(control_frame, textvariable=skill_var, width=20)
    skill_combo.pack(side=tk.LEFT, padx=5)
    
    # 刷新按钮
    refresh_btn = ttk.Button(control_frame, text="刷新", command=lambda: _refresh_skills())
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    # 中间编辑区域
    edit_frame = ttk.LabelFrame(parent, text="技能编辑")
    edit_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # 创建编辑表格
    _create_skill_editor(edit_frame)
    
    # 底部按钮区域
    button_frame = ttk.Frame(parent)
    button_frame.pack(fill=tk.X)
    
    save_btn = ttk.Button(button_frame, text="保存修改", command=lambda: _save_changes())
    save_btn.pack(side=tk.LEFT, padx=5)
    
    validate_btn = ttk.Button(button_frame, text="验证数据", command=lambda: _validate_data())
    validate_btn.pack(side=tk.LEFT, padx=5)
    
    revert_btn = ttk.Button(button_frame, text="撤销修改", command=lambda: _revert_changes())
    revert_btn.pack(side=tk.LEFT, padx=5)
    
    # 初始化英雄列表
    _refresh_heroes()


def _refresh_heroes():
    """刷新英雄列表"""
    # 实现英雄列表刷新逻辑
    pass


def _refresh_skills():
    """刷新技能列表"""
    # 实现技能列表刷新逻辑
    pass


def _create_skill_editor(parent):
    """创建技能编辑器"""
    # 实现技能编辑器创建逻辑
    pass


def _save_changes():
    """保存修改"""
    # 实现保存逻辑
    pass


def _validate_data():
    """验证数据"""
    # 实现验证逻辑
    pass


def _revert_changes():
    """撤销修改"""
    # 实现撤销逻辑
    pass


if __name__ == "__main__":
    # 测试技能管理器
    root = tk.Tk()
    root.title("技能管理器测试")
    
    frame = create_skill_manager_gui(root)
    frame.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()