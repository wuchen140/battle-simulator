#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能编辑器模块
提供强大的技能自定义功能，支持多种效果组合和条件触发
"""

import json
import os
import random
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum


class SkillType(Enum):
    """技能类型枚举"""
    DAMAGE = "damage"        # 伤害类技能
    HEAL = "heal"           # 治疗类技能  
    BUFF = "buff"           # 增益类技能
    DEBUFF = "debuff"       # 减益类技能
    CONTROL = "control"     # 控制类技能
    SUMMON = "summon"       # 召唤类技能
    TRANSFORM = "transform" # 变形类技能
    CUSTOM = "custom"       # 自定义类技能


class DamageType(Enum):
    """伤害类型枚举"""
    PHYSICAL = "physical"   # 物理伤害
    MAGICAL = "magical"     # 魔法伤害
    TRUE = "true"           # 真实伤害
    FIRE = "fire"           # 火焰伤害
    ICE = "ice"             # 冰霜伤害
    LIGHTNING = "lightning" # 闪电伤害
    POISON = "poison"       # 毒素伤害
    HOLY = "holy"           # 神圣伤害
    DARK = "dark"           # 暗影伤害


class TargetType(Enum):
    """目标类型枚举"""
    SELF = "self"               # 自身
    SINGLE_ENEMY = "single_enemy"       # 单个敌人
    SINGLE_ALLY = "single_ally"         # 单个友方
    ALL_ENEMIES = "all_enemies"         # 所有敌人
    ALL_ALLIES = "all_allies"           # 所有友方
    RANDOM_ENEMY = "random_enemy"       # 随机敌人
    RANDOM_ALLY = "random_ally"         # 随机友方


class BuffType(Enum):
    """增益类型枚举"""
    ATTACK = "attack"           # 攻击力
    DEFENSE = "defense"         # 防御力
    SPEED = "speed"             # 速度
    CRIT_RATE = "crit_rate"     # 暴击率
    CRIT_DAMAGE = "crit_damage" # 暴击伤害
    DODGE = "dodge"             # 闪避率
    ACCURACY = "accuracy"       # 命中率
    MAX_HEALTH = "max_health"   # 最大生命值
    SHIELD = "shield"           # 护盾


class ControlType(Enum):
    """控制类型枚举"""
    STUN = "stun"               # 眩晕
    FREEZE = "freeze"           # 冰冻
    SILENCE = "silence"         # 沉默
    PARALYZE = "paralyze"       # 麻痹
    CONFUSE = "confuse"         # 混乱
    CHARM = "charm"             # 魅惑
    FEAR = "fear"               # 恐惧
    SLEEP = "sleep"             # 睡眠


class StatusType(Enum):
    """状态类型枚举"""
    BURN = "burn"               # 燃烧
    POISON = "poison"           # 中毒
    BLEED = "bleed"             # 流血
    CURSE = "curse"             # 诅咒
    REGENERATION = "regeneration" # 再生


class EffectTrigger(Enum):
    """效果触发时机枚举"""
    ON_CAST = "on_cast"         # 施放时
    ON_HIT = "on_hit"           # 命中时
    ON_CRIT = "on_crit"         # 暴击时
    ON_KILL = "on_kill"         # 击杀时
    ON_TAKE_DAMAGE = "on_take_damage" # 受到伤害时
    ON_LOW_HEALTH = "on_low_health"   # 低生命值时
    ON_TURN_START = "on_turn_start"   # 回合开始时
    ON_TURN_END = "on_turn_end"       # 回合结束时


@dataclass
class SkillEffect:
    """技能效果基类"""
    type: str = ""              # 效果类型
    trigger: str = EffectTrigger.ON_CAST.value  # 触发时机
    probability: float = 1.0    # 触发概率 (0.0-1.0)
    duration: int = 0           # 持续时间(回合数)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class DamageEffect(SkillEffect):
    """伤害效果"""
    damage_type: str = DamageType.PHYSICAL.value
    base_damage: int = 0                    # 基础伤害值
    damage_multiplier: float = 1.0          # 伤害系数
    ignore_defense: bool = False            # 是否无视防御
    can_crit: bool = True                   # 是否可以暴击
    
    def __post_init__(self):
        self.type = "damage"


@dataclass
class HealEffect(SkillEffect):
    """治疗效果"""
    base_heal: int = 0                      # 基础治疗值
    heal_multiplier: float = 1.0            # 治疗系数
    is_percentage: bool = False             # 是否按百分比治疗
    
    def __post_init__(self):
        self.type = "heal"


@dataclass
class BuffEffect(SkillEffect):
    """增益效果"""
    buff_type: str = BuffType.ATTACK.value
    value: float = 0.0                      # 增益数值
    is_percentage: bool = True              # 是否为百分比增益
    
    def __post_init__(self):
        self.type = "buff"


@dataclass
class DebuffEffect(SkillEffect):
    """减益效果"""
    debuff_type: str = BuffType.ATTACK.value
    value: float = 0.0                      # 减益数值
    is_percentage: bool = True              # 是否为百分比减益
    
    def __post_init__(self):
        self.type = "debuff"


@dataclass
class ControlEffect(SkillEffect):
    """控制效果"""
    control_type: str = ControlType.STUN.value
    
    def __post_init__(self):
        self.type = "control"


@dataclass
class ShieldEffect(SkillEffect):
    """护盾效果"""
    shield_amount: int = 0                  # 护盾值
    is_percentage: bool = False             # 是否按百分比计算
    
    def __post_init__(self):
        self.type = "shield"


@dataclass
class StatusEffect(SkillEffect):
    """状态效果"""
    status_type: str = ""                   # 状态类型
    value: float = 0.0                      # 状态数值
    
    def __post_init__(self):
        self.type = "status"


class SkillEditor:
    """技能编辑器类"""
    
    def __init__(self, config_path: str = None):
        """初始化技能编辑器"""
        self.config_path = config_path or "/Users/diaoyuzhe/Desktop/模拟战斗/config/plugins/技能编辑器.json"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"加载技能编辑器配置失败: {e}")
            return {}
    
    def create_custom_skill(self, skill_data: Dict) -> Dict:
        """创建自定义技能
        
        Args:
            skill_data: 技能数据字典，包含技能名称、描述、效果等
            
        Returns:
            完整的技能配置字典
        """
        # 基础技能信息
        skill_config = {
            "name": skill_data.get("name", "自定义技能"),
            "description": skill_data.get("description", "自定义技能效果"),
            "skill_type": skill_data.get("skill_type", "custom"),
            "cooldown": skill_data.get("cooldown", 3),
            "mana_cost": skill_data.get("mana_cost", 0),
            "target_type": skill_data.get("target_type", TargetType.SINGLE_ENEMY.value),
            "level_values": skill_data.get("level_values", {1: 0.2, 2: 0.3, 3: 0.4, 4: 0.5, 5: 0.6}),
            "effects": []
        }
        
        # 添加效果
        effects = skill_data.get("effects", [])
        for effect_data in effects:
            effect = self._create_effect(effect_data)
            if effect:
                skill_config["effects"].append(effect.to_dict())
        
        return skill_config
    
    def _create_effect(self, effect_data: Dict) -> Optional[SkillEffect]:
        """创建技能效果对象"""
        effect_type = effect_data.get("type")
        
        if effect_type == "damage":
            return DamageEffect(
                trigger=effect_data.get("trigger", EffectTrigger.ON_CAST.value),
                probability=effect_data.get("probability", 1.0),
                duration=effect_data.get("duration", 0),
                damage_type=effect_data.get("damage_type", DamageType.PHYSICAL.value),
                base_damage=effect_data.get("base_damage", 0),
                damage_multiplier=effect_data.get("damage_multiplier", 1.0),
                ignore_defense=effect_data.get("ignore_defense", False),
                can_crit=effect_data.get("can_crit", True)
            )
            
        elif effect_type == "heal":
            return HealEffect(
                trigger=effect_data.get("trigger", EffectTrigger.ON_CAST.value),
                probability=effect_data.get("probability", 1.0),
                duration=effect_data.get("duration", 0),
                base_heal=effect_data.get("base_heal", 0),
                heal_multiplier=effect_data.get("heal_multiplier", 1.0),
                is_percentage=effect_data.get("is_percentage", False)
            )
            
        elif effect_type == "buff":
            return BuffEffect(
                trigger=effect_data.get("trigger", EffectTrigger.ON_CAST.value),
                probability=effect_data.get("probability", 1.0),
                duration=effect_data.get("duration", 0),
                buff_type=effect_data.get("buff_type", BuffType.ATTACK.value),
                value=effect_data.get("value", 0.0),
                is_percentage=effect_data.get("is_percentage", True)
            )
            
        elif effect_type == "debuff":
            return DebuffEffect(
                trigger=effect_data.get("trigger", EffectTrigger.ON_CAST.value),
                probability=effect_data.get("probability", 1.0),
                duration=effect_data.get("duration", 0),
                debuff_type=effect_data.get("debuff_type", BuffType.ATTACK.value),
                value=effect_data.get("value", 0.0),
                is_percentage=effect_data.get("is_percentage", True)
            )
            
        elif effect_type == "control":
            return ControlEffect(
                trigger=effect_data.get("trigger", EffectTrigger.ON_CAST.value),
                probability=effect_data.get("probability", 1.0),
                duration=effect_data.get("duration", 0),
                control_type=effect_data.get("control_type", ControlType.STUN.value)
            )
            
        elif effect_type == "shield":
            return ShieldEffect(
                trigger=effect_data.get("trigger", EffectTrigger.ON_CAST.value),
                probability=effect_data.get("probability", 1.0),
                duration=effect_data.get("duration", 0),
                shield_amount=effect_data.get("shield_amount", 0),
                is_percentage=effect_data.get("is_percentage", False)
            )
            
        elif effect_type == "status":
            return StatusEffect(
                trigger=effect_data.get("trigger", EffectTrigger.ON_CAST.value),
                probability=effect_data.get("probability", 1.0),
                duration=effect_data.get("duration", 0),
                status_type=effect_data.get("status_type", ""),
                value=effect_data.get("value", 0.0)
            )
            
        return None
    
    def save_skill_to_file(self, skill_config: Dict, filename: str) -> bool:
        """保存技能配置到文件"""
        try:
            plugins_dir = "/Users/diaoyuzhe/Desktop/模拟战斗/config/plugins"
            os.makedirs(plugins_dir, exist_ok=True)
            
            filepath = os.path.join(plugins_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(skill_config, f, ensure_ascii=False, indent=2)
            
            print(f"技能已保存到: {filepath}")
            return True
            
        except Exception as e:
            print(f"保存技能失败: {e}")
            return False
    
    def load_skill_from_file(self, filename: str) -> Optional[Dict]:
        """从文件加载技能配置"""
        try:
            filepath = os.path.join("/Users/diaoyuzhe/Desktop/模拟战斗/config/plugins", filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    skill_data = json.load(f)
                    
                    # 转换level_values中的字符串键为整数键
                    if 'level_values' in skill_data and isinstance(skill_data['level_values'], dict):
                        level_values = {}
                        for key, value in skill_data['level_values'].items():
                            try:
                                level_values[int(key)] = value
                            except (ValueError, TypeError):
                                level_values[key] = value
                        skill_data['level_values'] = level_values
                    
                    return skill_data
            return None
            
        except Exception as e:
            print(f"加载技能失败: {e}")
            return None
    
    def list_available_skills(self) -> List[str]:
        """列出所有可用的技能文件"""
        plugins_dir = "/Users/diaoyuzhe/Desktop/模拟战斗/config/plugins"
        if os.path.exists(plugins_dir):
            return [f for f in os.listdir(plugins_dir) if f.endswith('.json')]
        return []
    
    def generate_skill_template(self) -> Dict:
        """生成技能模板"""
        return {
            "name": "技能名称",
            "description": "技能描述",
            "skill_type": "damage",  # damage/heal/buff/debuff/control/summon/transform/custom
            "cooldown": 3,
            "mana_cost": 0,
            "target_type": "single_enemy",  # self/single_enemy/single_ally/all_enemies/all_allies/random_enemy/random_ally
            "level_values": {
                1: 0.2,
                2: 0.3, 
                3: 0.4,
                4: 0.5,
                5: 0.6
            },
            "effects": [
                # 效果列表，每个效果包含:
                # {
                #     "type": "damage",  # damage/heal/buff/debuff/control/shield/status
                #     "trigger": "on_cast",  # on_cast/on_hit/on_crit/on_kill/on_take_damage/on_low_health/on_turn_start/on_turn_end
                #     "probability": 1.0,  # 触发概率 (0.0-1.0)
                #     "duration": 0,       # 持续时间(回合数)
                #     # 其他效果特定参数...
                # }
            ]
        }
    
    def create_example_skills(self):
        """创建一些示例技能"""
        
        # 示例1: 多重火焰箭
        fire_arrow = {
            "name": "多重火焰箭",
            "description": "发射多支火焰箭矢，造成火焰伤害并有概率点燃目标",
            "skill_type": "damage",
            "cooldown": 2,
            "mana_cost": 20,
            "target_type": TargetType.ALL_ENEMIES.value,
            "level_values": {1: 0.3, 2: 0.4, 3: 0.5, 4: 0.6, 5: 0.7},
            "effects": [
                {
                    "type": "damage",
                    "trigger": EffectTrigger.ON_CAST.value,
                    "probability": 1.0,
                    "damage_type": DamageType.FIRE.value,
                    "base_damage": 100,
                    "damage_multiplier": 0.8,
                    "can_crit": True
                },
                {
                    "type": "status",
                    "trigger": EffectTrigger.ON_HIT.value,
                    "probability": 0.3,
                    "duration": 3,
                    "status_type": "burn",
                    "value": 30
                }
            ]
        }
        
        # 示例2: 神圣庇护
        holy_protection = {
            "name": "神圣庇护",
            "description": "为所有友方单位施加神圣护盾并提升防御力",
            "skill_type": "buff",
            "cooldown": 4,
            "mana_cost": 40,
            "target_type": TargetType.ALL_ALLIES.value,
            "level_values": {1: 0.2, 2: 0.25, 3: 0.3, 4: 0.35, 5: 0.4},
            "effects": [
                {
                    "type": "shield",
                    "trigger": EffectTrigger.ON_CAST.value,
                    "probability": 1.0,
                    "duration": 3,
                    "shield_amount": 200,
                    "is_percentage": False
                },
                {
                    "type": "buff",
                    "trigger": EffectTrigger.ON_CAST.value,
                    "probability": 1.0,
                    "duration": 3,
                    "buff_type": BuffType.DEFENSE.value,
                    "value": 0.2,
                    "is_percentage": True
                }
            ]
        }
        
        # 保存示例技能
        self.save_skill_to_file(self.create_custom_skill(fire_arrow), "多重火焰箭.json")
        self.save_skill_to_file(self.create_custom_skill(holy_protection), "神圣庇护.json")
        
        print("示例技能创建完成!")


def create_skill_template() -> Dict:
    """创建技能模板"""
    return {
        "name": "技能名称",
        "description": "技能描述",
        "skill_type": "damage",  # damage/heal/buff/debuff/control/summon/transform/custom
        "cooldown": 3,
        "mana_cost": 0,
        "target_type": "single_enemy",  # self/single_enemy/single_ally/all_enemies/all_allies/random_enemy/random_ally
        "level_values": {
            1: 0.2,
            2: 0.3, 
            3: 0.4,
            4: 0.5,
            5: 0.6
        },
        "effects": [
            # 效果列表，每个效果包含:
            # {
            #     "type": "damage",  # damage/heal/buff/debuff/control/shield/status
            #     "trigger": "on_cast",  # on_cast/on_hit/on_crit/on_kill/on_take_damage/on_low_health/on_turn_start/on_turn_end
            #     "probability": 1.0,  # 触发概率 (0.0-1.0)
            #     "duration": 0,       # 持续时间(回合数)
            #     # 其他效果特定参数...
            # }
        ]
    }


# 测试代码
if __name__ == "__main__":
    editor = SkillEditor()
    
    # 创建示例技能
    editor.create_example_skills()
    
    # 列出所有技能
    skills = editor.list_available_skills()
    print("可用技能文件:", skills)