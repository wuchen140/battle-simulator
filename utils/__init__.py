#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块 - 提供通用工具函数
"""

import random
from typing import Any, Dict, List


def get_random_element(items: List[Any]) -> Any:
    """从列表中随机选择一个元素"""
    return random.choice(items) if items else None


def format_percentage(value: float) -> str:
    """格式化百分比显示"""
    return f"{value:.1%}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """限制数值在指定范围内"""
    return max(min_val, min(value, max_val))


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """深度合并两个字典"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def safe_get(dictionary: Dict, key: Any, default: Any = None) -> Any:
    """安全获取字典值，避免KeyError"""
    return dictionary.get(key, default)


def calculate_damage(base_damage: float, attack: float, defense: float, 
                    critical_chance: float = 0.0, critical_multiplier: float = 1.5) -> Dict:
    """
    计算伤害
    
    Args:
        base_damage: 基础伤害
        attack: 攻击力
        defense: 防御力
        critical_chance: 暴击率
        critical_multiplier: 暴击倍率
        
    Returns:
        伤害结果字典
    """
    # 计算基础伤害
    damage = base_damage * (attack / (attack + defense))
    
    # 判断是否暴击
    is_critical = random.random() < critical_chance
    if is_critical:
        damage *= critical_multiplier
    
    return {
        'damage': max(1, round(damage)),
        'is_critical': is_critical,
        'critical_multiplier': critical_multiplier if is_critical else 1.0
    }


def format_battle_log(message: str, indent_level: int = 0) -> str:
    """格式化战斗日志"""
    indent = "  " * indent_level
    return f"{indent}{message}"


def validate_skill_data(skill_data: Dict) -> bool:
    """验证技能数据完整性"""
    required_fields = ['name', 'skill_type', 'cooldown']
    return all(field in skill_data for field in required_fields)


def validate_hero_data(hero_data: Dict) -> bool:
    """验证英雄数据完整性"""
    required_fields = ['name', 'level', 'health', 'attack', 'defense', 'speed']
    return all(field in hero_data for field in required_fields)