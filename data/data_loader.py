#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载器模块
负责从Excel文件加载英雄和技能数据，包含数据验证功能
"""

import pandas as pd
from typing import Dict, List, Optional
import json
from pathlib import Path
from data.data_validator import DataValidator
from core.config_manager import config
from core.cache_manager import cache_manager


class HeroDataLoader:
    """英雄数据加载器"""
    
    @staticmethod
    def load_hero_data(excel_path: str, validate: bool = True, use_cache: bool = True) -> List[Dict]:
        """
        从Excel加载英雄数据，支持缓存
        
        Args:
            excel_path: Excel文件路径
            validate: 是否进行数据验证
            use_cache: 是否使用缓存
            
        Returns:
            英雄数据列表，如果验证失败可能返回空列表
        """
        # 检查缓存
        if use_cache:
            cached_data = cache_manager.get_cached_heroes()
            if cached_data is not None:
                print("从缓存加载英雄数据")
                return cached_data
        
        try:
            # 读取英雄数值工作表，跳过前两行表头
            df = pd.read_excel(excel_path, sheet_name=config.data.hero_data_sheet)
            df = df.iloc[2:].reset_index(drop=True)  # 跳过表头行
            
            # 确保数据格式正确，处理可能的NaN值
            for col in df.columns:
                if col in ['HP', 'ATK', 'DEF', 'Level', 'SPD', 'CRIT%', 'CRIT_DMG']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            heroes = df.to_dict('records')
            
            if validate:
                # 数据验证
                validator = DataValidator()
                validation_result = validator.validate_hero_data(heroes)
                
                if not validation_result.is_valid:
                    print(f"英雄数据验证失败: {len(validation_result.errors)} 个错误")
                    for error in validation_result.errors:
                        print(f"  - {error}")
                    return []
                
                if validation_result.warnings:
                    print(f"英雄数据验证警告: {len(validation_result.warnings)} 个警告")
                    for warning in validation_result.warnings:
                        print(f"  - {warning}")
            
            print(f"成功加载 {len(heroes)} 条英雄数据")
            
            # 打印职业信息用于调试
            job_counts = {}
            for hero in heroes:
                job = hero.get('职业', '未知')
                job_counts[job] = job_counts.get(job, 0) + 1
            
            print(f"职业分布: {job_counts}")
            
            # 缓存数据
            if use_cache:
                cache_manager.set('all_heroes', 'heroes', heroes)
            
            return heroes
        except Exception as e:
            print(f"加载英雄数据失败: {e}")
            return []
    
    @staticmethod
    def load_skills_data(excel_path: str, validate: bool = True, use_cache: bool = True) -> List[Dict]:
        """
        从Excel加载技能数据，支持缓存
        
        Args:
            excel_path: Excel文件路径
            validate: 是否进行数据验证
            use_cache: 是否使用缓存
            
        Returns:
            技能数据列表
        """
        # 检查缓存
        if use_cache:
            cached_data = cache_manager.get_cached_skills()
            if cached_data is not None:
                print("从缓存加载技能数据")
                return cached_data
        
        try:
            df = pd.read_excel(excel_path, sheet_name=config.data.skill_data_sheet)
            skills = df.to_dict('records')
            
            # 将Level1-5列转换为level_values字典
            for skill in skills:
                level_values = {}
                for level in range(1, 6):
                    level_key = f'Level{level}'
                    if level_key in skill and pd.notna(skill[level_key]):
                        try:
                            level_values[level] = float(skill[level_key])
                        except (ValueError, TypeError):
                            level_values[level] = 0.0
                
                # 如果存在有效的等级数值，添加到技能数据中
                if level_values:
                    skill['level_values'] = level_values
            
            if validate:
                # 数据验证
                validator = DataValidator()
                validation_result = validator.validate_skill_data(skills)
                
                if validation_result.warnings:
                    print(f"技能数据验证警告: {len(validation_result.warnings)} 个警告")
                    for warning in validation_result.warnings:
                        print(f"  - {warning}")
            
            print(f"成功加载 {len(skills)} 条技能数据")
            
            # 缓存数据
            if use_cache:
                cache_manager.set('all_skills', 'skills', skills)
            
            return skills
        except Exception as e:
            print(f"加载技能数据失败: {e}")
            return []
    
    @staticmethod
    def get_hero_skills_from_display_logic(hero_name: str, excel_path: str) -> Optional[List[Dict]]:
        """
        获取英雄技能数据（已移除display_all_heroes依赖）
        返回None，强制使用回退逻辑
        """
        return None
    
    @staticmethod
    def get_hero_data_by_name(hero_name: str, heroes_data: List[Dict]) -> Optional[Dict]:
        """根据英雄名称获取英雄数据"""
        for hero in heroes_data:
            if hero.get('英雄名称') == hero_name:
                return hero
        return None
    
    @staticmethod
    def get_base_heroes(heroes_data: List[Dict]) -> List[str]:
        """获取基础英雄列表（去重）"""
        base_heroes = set()
        for hero in heroes_data:
            hero_name = hero.get('英雄名称')
            if hero_name:
                base_heroes.add(hero_name)
        return sorted(list(base_heroes))
    
    @staticmethod
    def get_hero_level_range(hero_name: str, heroes_data: List[Dict]) -> Dict[str, int]:
        """获取英雄的等级范围"""
        levels = []
        for hero in heroes_data:
            if hero.get('英雄名称') == hero_name:
                level = hero.get('Level', 0)
                if level > 0:
                    levels.append(level)
        
        if levels:
            return {'min': min(levels), 'max': max(levels)}
        return {'min': 1, 'max': 1}
    
    @staticmethod
    def filter_heroes_by_name_and_level(heroes_data: List[Dict], hero_name: str, level: int) -> List[Dict]:
        """根据名称和等级过滤英雄"""
        return [hero for hero in heroes_data 
                if hero.get('英雄名称') == hero_name and hero.get('Level') == level]

    @staticmethod
    def get_skill_usage_type(skill_type_value) -> str:
        """
        根据技能类型值获取技能使用方式
        
        Args:
            skill_type_value: 技能类型值（来自Excel第5列）
            
        Returns:
            'active' - 主动技能
            'passive' - 被动技能
            'unknown' - 未知类型
        """
        if pd.isna(skill_type_value):
            return 'unknown'
        
        # 转换为字符串进行比较
        skill_type_str = str(skill_type_value)
        
        if skill_type_str in ['1', '1.0']:
            return 'active'
        elif skill_type_str in ['2', '2.0']:
            return 'passive'
        else:
            return 'unknown'

    @staticmethod
    def analyze_skills_by_type(skills_data: List[Dict]) -> Dict:
        """
        分析技能数据，按类型统计
        
        Args:
            skills_data: 技能数据列表
            
        Returns:
            包含技能类型统计信息的字典
        """
        result = {
            'active_skills': [],
            'passive_skills': [],
            'unknown_skills': [],
            'counts': {
                'active': 0,
                'passive': 0,
                'unknown': 0,
                'total': len(skills_data)
            }
        }
        
        for skill in skills_data:
            skill_type = skill.get('技能类型')
            usage_type = HeroDataLoader.get_skill_usage_type(skill_type)
            
            skill_info = {
                'name': skill.get('技能名称'),
                'hero': skill.get('名称'),
                'type_code': skill_type,
                'usage_type': usage_type,
                'description': str(skill.get('技能描述', ''))[:50] + '...' if skill.get('技能描述') else '',
                'damage_types': HeroDataLoader.parse_damage_types(skill.get('技能伤害类型'))
            }
            
            if usage_type == 'active':
                result['active_skills'].append(skill_info)
                result['counts']['active'] += 1
            elif usage_type == 'passive':
                result['passive_skills'].append(skill_info)
                result['counts']['passive'] += 1
            else:
                result['unknown_skills'].append(skill_info)
                result['counts']['unknown'] += 1
        
        return result

    @staticmethod
    def parse_damage_types(damage_type_value) -> List[str]:
        """
        解析技能伤害类型
        
        Args:
            damage_type_value: 技能伤害类型值（来自Excel第6列）
            
        Returns:
            伤害类型列表，可能包含多个类型
        """
        if pd.isna(damage_type_value):
            return []
        
        # 转换为字符串并分割多个类型
        damage_type_str = str(damage_type_value)
        type_codes = [code.strip() for code in damage_type_str.split(',')]
        
        result = []
        type_mapping = {
            '1': 'damage',      # 伤害类技能
            '2': 'control',     # 控制类技能  
            '3': 'buff',        # BUFF类技能
            '4': 'other'        # 其他类技能
        }
        
        for code in type_codes:
            if code in type_mapping:
                result.append(type_mapping[code])
        
        return result

    @staticmethod
    def analyze_skills_by_damage_type(skills_data: List[Dict]) -> Dict:
        """
        分析技能数据，按伤害类型统计
        
        Args:
            skills_data: 技能数据列表
            
        Returns:
            包含伤害类型统计信息的字典
        """
        result = {
            'damage_skills': [],    # 伤害类技能
            'control_skills': [],   # 控制类技能
            'buff_skills': [],      # BUFF类技能
            'other_skills': [],     # 其他类技能
            'mixed_skills': [],     # 混合类型技能
            'counts': {
                'damage': 0,
                'control': 0,
                'buff': 0,
                'other': 0,
                'mixed': 0,
                'total': len(skills_data)
            }
        }
        
        for skill in skills_data:
            damage_types = HeroDataLoader.parse_damage_types(skill.get('技能伤害类型'))
            
            skill_info = {
                'name': skill.get('技能名称'),
                'hero': skill.get('名称'),
                'damage_type_codes': str(skill.get('技能伤害类型', '')),
                'damage_types': damage_types,
                'description': str(skill.get('技能描述', ''))[:50] + '...' if skill.get('技能描述') else ''
            }
            
            # 分类统计
            if len(damage_types) > 1:
                result['mixed_skills'].append(skill_info)
                result['counts']['mixed'] += 1
            elif len(damage_types) == 1:
                damage_type = damage_types[0]
                if damage_type == 'damage':
                    result['damage_skills'].append(skill_info)
                    result['counts']['damage'] += 1
                elif damage_type == 'control':
                    result['control_skills'].append(skill_info)
                    result['counts']['control'] += 1
                elif damage_type == 'buff':
                    result['buff_skills'].append(skill_info)
                    result['counts']['buff'] += 1
                elif damage_type == 'other':
                    result['other_skills'].append(skill_info)
                    result['counts']['other'] += 1
        
        return result