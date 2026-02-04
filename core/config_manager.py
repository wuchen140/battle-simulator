#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - 统一管理系统配置和常量
支持环境变量配置和类型验证
"""

import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging


@dataclass
class BattleConfig:
    """战斗系统配置"""
    max_battle_turns: int = 50
    defense_params: Tuple[int, int] = (5, 335)
    min_damage: int = 10
    job_counter_rate: float = 0.2
    default_critical_multiplier: float = 2.0
    default_dodge_chance: float = 0.1


@dataclass  
class StatusConfig:
    """状态效果配置"""
    durations: Dict[str, int] = None
    strengths: Dict[str, float] = None
    
    def __post_init__(self):
        if self.durations is None:
            self.durations = {
                'stun': 1, 'poison': 3, 'burn': 2, 'freeze': 1,
                'attack_up': 3, 'defense_up': 3, 'speed_up': 2
            }
        if self.strengths is None:
            self.strengths = {
                'poison': 0.05, 'burn': 0.08, 
                'attack_up': 0.2, 'defense_up': 0.2, 'speed_up': 0.15
            }


@dataclass
class CacheConfig:
    """缓存配置"""
    default_ttl: int = 300  # 默认缓存过期时间（秒）
    preload_enabled: bool = True  # 是否启用预加载
    cleanup_interval: int = 60  # 缓存清理间隔（秒）


@dataclass
class DataConfig:
    """数据配置"""
    excel_path: str = "/Users/diaoyuzhe/Desktop/模拟战斗/英雄类数据1.xlsx"
    hero_data_sheet: str = "英雄数值"
    skill_data_sheet: str = "英雄技能数值及描述"
    required_hero_fields: List[str] = None
    required_skill_fields: List[str] = None
    
    def __post_init__(self):
        if self.required_hero_fields is None:
            self.required_hero_fields = [
                '英雄名称', '职业', 'Level', 'HP', 'ATK', 'DEF', 'SPD', 'CRIT%', 'CRIT_DMG'
            ]
        if self.required_skill_fields is None:
            self.required_skill_fields = [
                '名称', '技能名称', '技能描述', '技能CD', '技能类型', '技能伤害类型',
                'Level1', 'Level2', 'Level3', 'Level4', 'Level5'
            ]


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置"""
        # 从环境变量加载配置
        self.excel_path = os.getenv('EXCEL_PATH', "/Users/diaoyuzhe/Desktop/模拟战斗/英雄类数据1.xlsx")
        self.debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        # 初始化配置对象
        self.battle = BattleConfig()
        self.status = StatusConfig()
        self.data = DataConfig()
        self.cache = CacheConfig()
        
        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/tmp/hero_battle.log') if self.debug_mode else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 检查Excel文件是否存在
            if not Path(self.excel_path).exists():
                self.logger.error(f"Excel文件不存在: {self.excel_path}")
                return False
            
            # 验证战斗配置
            if self.battle.max_battle_turns <= 0:
                self.logger.error("最大战斗回合数必须大于0")
                return False
            
            if self.battle.job_counter_rate <= 0:
                self.logger.error("职业克制率必须大于0")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'excel_path': self.excel_path,
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'battle_config': {
                'max_battle_turns': self.battle.max_battle_turns,
                'job_counter_rate': self.battle.job_counter_rate,
                'min_damage': self.battle.min_damage
            },
            'data_config': {
                'required_hero_fields': self.data.required_hero_fields,
                'required_skill_fields': self.data.required_skill_fields
            }
        }


# 全局配置实例
config = ConfigManager()