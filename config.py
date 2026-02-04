#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 系统配置和常量定义
"""

# Excel文件配置
EXCEL_FILE_PATH = "/Users/diaoyuzhe/Desktop/模拟战斗/英雄类数据1.xlsx"
HERO_DATA_SHEET = "英雄数值"
SKILL_DATA_SHEET = "英雄技能数值及描述"

# 技能类型常量 - 按使用方式分类
SKILL_TYPE_ACTIVE = ['1', '1.0']  # 主动技能
SKILL_TYPE_PASSIVE = ['2', '2.0']  # 被动技能
# 技能伤害类型常量 - 按效果分类
SKILL_DAMAGE_TYPE_DAMAGE = ['1', '1.0']  # 伤害类技能
SKILL_DAMAGE_TYPE_CONTROL = ['2', '2.0']  # 控制类技能
SKILL_DAMAGE_TYPE_BUFF = ['3', '3.0']  # BUFF类技能
SKILL_DAMAGE_TYPE_OTHER = ['4', '4.0', '0', '0.0']  # 其他类技能

# 技能效果关键词映射
SKILL_KEYWORDS_MAPPING = {
    # 伤害类技能关键词
    'damage': ['攻击', '伤害', '造成', '打击', '斩击', '射击', '魔法', '物理'],
    # 控制类技能关键词  
    'control': ['眩晕', '冻结', '沉默', '控制', '定身', '麻痹', '减速', '束缚'],
    # BUFF类技能关键词
    'buff': ['攻击提升', '防御提升', '暴击提升', '速度提升', '增益', '强化', '祝福', '护盾'],
    # 治疗类技能关键词
    'heal': ['治疗', '回复', '恢复', '生命', 'HP', '血量']
}

# 战斗配置
MAX_BATTLE_TURNS = 50  # 最大战斗回合数
DEFAULT_CRITICAL_MULTIPLIER = 1.5  # 默认暴击倍率
DEFAULT_DODGE_CHANCE = 0.1  # 默认闪避几率

# 伤害计算公式参数（可在GUI中实时调整）
DAMAGE_FORMULA_PARAMS = {
    'defense_param1': 15,  # 防御参数1
    'defense_param2': 600,  # 防御参数2
    'min_damage': 100,       # 最小伤害值
}

# 状态效果配置
STATUS_DURATION = {
    'stun': 1,  # 眩晕持续回合
    'poison': 3,  # 中毒持续回合
    'burn': 2,  # 灼烧持续回合
    'freeze': 1,  # 冰冻持续回合
    'attack_up': 3,  # 攻击提升持续回合
    'defense_up': 3,  # 防御提升持续回合
    'speed_up': 2,  # 速度提升持续回合
}

# 状态效果强度
STATUS_STRENGTH = {
    'poison': 0.05,  # 中毒每回合伤害比例
    'burn': 0.08,  # 灼烧每回合伤害比例
    'attack_up': 0.2,  # 攻击提升比例
    'defense_up': 0.2,  # 防御提升比例
    'speed_up': 0.15,  # 速度提升比例
}

# 技能效果配置
SKILL_EFFECTS = {
    'damage': {
        'min_multiplier': 0.8,
        'max_multiplier': 1.2,
    },
    'heal': {
        'min_multiplier': 0.6,
        'max_multiplier': 0.9,
    },
    'buff': {
        'duration_range': (2, 4),
    }
}

# 英雄属性范围
HERO_ATTRIBUTE_RANGES = {
    'health': (800, 5000),
    'attack': (50, 300),
    'defense': (30, 200),
    'speed': (80, 200),
    'critical_chance': (0.05, 0.3),
    'dodge_chance': (0.05, 0.2),
}

# 日志配置
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# 显示配置
DISPLAY_SETTINGS = {
    'show_detailed_logs': True,
    'show_skill_effects': True,
    'show_status_effects': True,
    'show_damage_calculations': False,
}

# 调试配置
DEBUG_SETTINGS = {
    'enable_debug_mode': False,
    'log_file_path': "/tmp/hero_battle_debug.log",
    'max_log_size': 10485760,  # 10MB
}