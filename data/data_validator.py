#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证器 - 验证Excel数据的完整性和有效性
"""

from typing import Dict, List, Tuple, Optional, Set, Any
import pandas as pd
from dataclasses import dataclass
from core.config_manager import config
import logging


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_fields: Dict[str, List[str]]
    invalid_values: Dict[str, List[Tuple[str, Any]]]
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.missing_fields = {'heroes': [], 'skills': []}
        self.invalid_values = {'heroes': [], 'skills': []}
    
    def add_error(self, message: str):
        """添加错误信息"""
        self.is_valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """添加警告信息"""
        self.warnings.append(message)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'is_valid': self.is_valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'missing_fields': self.missing_fields,
            'invalid_values': self.invalid_values
        }


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 英雄属性有效范围
        self.hero_attribute_ranges = {
            'HP': (500, 10000),      # 生命值
            'ATK': (30, 500),        # 攻击力
            'DEF': (20, 300),        # 防御力
            'SPD': (50, 250),        # 速度
            'CRIT%': (0.0, 0.5),    # 暴击率
            'CRIT_DMG': (1.0, 3.0)  # 暴击伤害
        }
        
        # 有效职业类型
        self.valid_roles = {'DPS', 'TANK', 'SNIP'}
        
        # 有效技能类型
        self.valid_skill_types = {'1', '1.0', '2', '2.0', '3', '3.0', '4', '4.0', '0', '0.0'}
    
    def validate_hero_data(self, heroes_data: List[Dict]) -> ValidationResult:
        """验证英雄数据完整性"""
        result = ValidationResult()
        
        if not heroes_data:
            result.add_error("英雄数据为空")
            return result
        
        # 检查必需字段
        required_fields = config.data.required_hero_fields
        self._check_required_fields(heroes_data, required_fields, 'heroes', result)
        
        # 验证数据有效性
        self._validate_hero_values(heroes_data, result)
        
        # 检查职业有效性
        self._validate_hero_roles(heroes_data, result)
        
        # 检查等级范围
        self._validate_level_ranges(heroes_data, result)
        
        return result
    
    def validate_skill_data(self, skills_data: List[Dict]) -> ValidationResult:
        """验证技能数据完整性"""
        result = ValidationResult()
        
        if not skills_data:
            result.add_warning("技能数据为空")
            return result
        
        # 检查必需字段
        required_fields = config.data.required_skill_fields
        self._check_required_fields(skills_data, required_fields, 'skills', result)
        
        # 验证技能类型
        self._validate_skill_types(skills_data, result)
        
        # 验证技能数值
        self._validate_skill_values(skills_data, result)
        
        return result
    
    def _check_required_fields(self, data: List[Dict], required_fields: List[str], 
                              data_type: str, result: ValidationResult):
        """检查必需字段是否存在"""
        missing_fields = set(required_fields)
        
        for item in data:
            for field in required_fields:
                if field in item and pd.notna(item[field]):
                    missing_fields.discard(field)
        
        if missing_fields:
            result.add_error(f"{data_type}数据缺少必需字段: {sorted(missing_fields)}")
            result.missing_fields[data_type].extend(sorted(missing_fields))
    
    def _validate_hero_values(self, heroes_data: List[Dict], result: ValidationResult):
        """验证英雄数值有效性"""
        invalid_records = []
        
        for i, hero in enumerate(heroes_data):
            hero_name = hero.get('英雄名称', f'未知英雄_{i}')
            
            # 检查数值范围
            for attr, (min_val, max_val) in self.hero_attribute_ranges.items():
                if attr in hero and pd.notna(hero[attr]):
                    try:
                        value = float(hero[attr])
                        if not (min_val <= value <= max_val):
                            invalid_records.append((
                                hero_name, attr, hero[attr], f"超出范围 {min_val}-{max_val}"
                            ))
                    except (ValueError, TypeError):
                        invalid_records.append((hero_name, attr, hero[attr], "无效数值"))
            
            # 检查等级
            level = hero.get('Level')
            if pd.notna(level):
                try:
                    level_int = int(level)
                    if level_int <= 0 or level_int > 100:
                        invalid_records.append((hero_name, 'Level', level, "等级应在1-100之间"))
                except (ValueError, TypeError):
                    invalid_records.append((hero_name, 'Level', level, "无效等级"))
        
        if invalid_records:
            result.invalid_values['heroes'].extend(invalid_records)
            result.add_warning(f"发现 {len(invalid_records)} 条无效的英雄数值记录")
    
    def _validate_hero_roles(self, heroes_data: List[Dict], result: ValidationResult):
        """验证英雄职业有效性"""
        invalid_roles = []
        
        for hero in heroes_data:
            role = hero.get('职业')
            if pd.notna(role) and role not in self.valid_roles:
                invalid_roles.append((hero.get('英雄名称', '未知英雄'), role))
        
        if invalid_roles:
            result.add_warning(f"发现 {len(invalid_roles)} 个无效职业: {invalid_roles}")
    
    def _validate_level_ranges(self, heroes_data: List[Dict], result: ValidationResult):
        """验证等级范围一致性"""
        hero_levels = {}
        
        for hero in heroes_data:
            name = hero.get('英雄名称')
            level = hero.get('Level')
            if pd.notna(name) and pd.notna(level):
                if name not in hero_levels:
                    hero_levels[name] = []
                hero_levels[name].append(level)
        
        # 检查每个英雄是否有多个等级
        for name, levels in hero_levels.items():
            if len(levels) > 1:
                min_level = min(levels)
                max_level = max(levels)
                if max_level - min_level > 50:  # 等级跨度太大
                    result.add_warning(f"英雄 {name} 等级跨度过大: {min_level}-{max_level}")
    
    def _validate_skill_types(self, skills_data: List[Dict], result: ValidationResult):
        """验证技能类型有效性"""
        invalid_types = []
        
        for skill in skills_data:
            skill_type = skill.get('技能类型')
            if pd.notna(skill_type):
                skill_type_str = str(skill_type)
                if skill_type_str not in self.valid_skill_types:
                    invalid_types.append((
                        skill.get('技能名称', '未知技能'), 
                        skill.get('名称', '未知英雄'), 
                        skill_type
                    ))
        
        if invalid_types:
            result.add_warning(f"发现 {len(invalid_types)} 个无效技能类型")
    
    def _validate_skill_values(self, skills_data: List[Dict], result: ValidationResult):
        """验证技能数值有效性"""
        invalid_values = []
        
        for skill in skills_data:
            skill_name = skill.get('技能名称', '未知技能')
            hero_name = skill.get('名称', '未知英雄')
            
            # 检查技能CD
            cooldown = skill.get('技能CD')
            if pd.notna(cooldown):
                try:
                    cd = float(cooldown)
                    if cd < 0 or cd > 10:
                        invalid_values.append((f"{hero_name}-{skill_name}", '技能CD', cooldown, "CD应在0-10之间"))
                except (ValueError, TypeError):
                    invalid_values.append((f"{hero_name}-{skill_name}", '技能CD', cooldown, "无效CD值"))
            
            # 检查等级数值
            for level in range(1, 6):
                level_key = f'Level{level}'
                if level_key in skill and pd.notna(skill[level_key]):
                    try:
                        value = float(skill[level_key])
                        if value < 0 or value > 10000:
                            invalid_values.append((f"{hero_name}-{skill_name}", level_key, skill[level_key], "数值超出合理范围"))
                    except (ValueError, TypeError):
                        invalid_values.append((f"{hero_name}-{skill_name}", level_key, skill[level_key], "无效数值"))
        
        if invalid_values:
            result.invalid_values['skills'].extend(invalid_values)
            result.add_warning(f"发现 {len(invalid_values)} 条无效的技能数值记录")
    
    def generate_validation_report(self, hero_result: ValidationResult, 
                                 skill_result: ValidationResult) -> str:
        """生成验证报告"""
        report = []
        report.append("=" * 60)
        report.append("数据验证报告")
        report.append("=" * 60)
        
        # 英雄数据验证结果
        report.append(f"\n英雄数据验证: {'通过' if hero_result.is_valid else '失败'}")
        report.append(f"错误数: {len(hero_result.errors)}")
        report.append(f"警告数: {len(hero_result.warnings)}")
        
        if hero_result.errors:
            report.append("\n错误详情:")
            for error in hero_result.errors:
                report.append(f"  - {error}")
        
        if hero_result.warnings:
            report.append("\n警告详情:")
            for warning in hero_result.warnings:
                report.append(f"  - {warning}")
        
        # 技能数据验证结果
        report.append(f"\n技能数据验证: {'通过' if skill_result.is_valid else '失败'}")
        report.append(f"错误数: {len(skill_result.errors)}")
        report.append(f"警告数: {len(skill_result.warnings)}")
        
        if skill_result.errors:
            report.append("\n错误详情:")
            for error in skill_result.errors:
                report.append(f"  - {error}")
        
        if skill_result.warnings:
            report.append("\n警告详情:")
            for warning in skill_result.warnings:
                report.append(f"  - {warning}")
        
        report.append("=" * 60)
        return '\n'.join(report)