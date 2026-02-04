#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能链系统模块
支持技能组合和连招系统
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import os
import time
import logging
from enum import Enum
import random


class ChainType(Enum):
    """技能链类型枚举"""
    COMBO = "combo"        # 连招组合
    SEQUENCE = "sequence"  # 顺序释放
    SYNERGY = "synergy"    # 协同效果


@dataclass
class SkillChain:
    """技能链数据类"""
    name: str
    chain_type: ChainType
    skill_names: List[str]  # 技能名称列表
    description: str
    cooldown: int = 0
    damage_multiplier: float = 1.0  # 伤害倍率
    effect_multiplier: float = 1.0  # 效果倍率
    trigger_chance: float = 1.0    # 触发概率
    requirements: Dict[str, Any] = None  # 触发条件
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = {}


class SkillChainManager:
    """技能链管理器"""
    
    def __init__(self, config_dir: str = "config/skill_chains"):
        self.config_dir = config_dir
        self.chains: Dict[str, SkillChain] = {}
        self.active_chains: Dict[str, Dict] = {}  # 正在进行的技能链
        self.logger = logging.getLogger(__name__)
        
        # 创建配置目录
        os.makedirs(config_dir, exist_ok=True)
    
    def load_chains(self) -> bool:
        """加载所有技能链配置"""
        try:
            chain_files = [f for f in os.listdir(self.config_dir) 
                          if f.endswith('.json')]
            
            for chain_file in chain_files:
                chain_path = os.path.join(self.config_dir, chain_file)
                with open(chain_path, 'r', encoding='utf-8') as f:
                    chain_data = json.load(f)
                
                chain = SkillChain(
                    name=chain_data['name'],
                    chain_type=ChainType(chain_data['chain_type']),
                    skill_names=chain_data['skill_names'],
                    description=chain_data['description'],
                    cooldown=chain_data.get('cooldown', 0),
                    damage_multiplier=chain_data.get('damage_multiplier', 1.0),
                    effect_multiplier=chain_data.get('effect_multiplier', 1.0),
                    trigger_chance=chain_data.get('trigger_chance', 1.0),
                    requirements=chain_data.get('requirements', {})
                )
                
                self.chains[chain.name] = chain
            
            self.logger.info(f"成功加载 {len(self.chains)} 个技能链")
            return True
            
        except Exception as e:
            self.logger.error(f"加载技能链失败: {e}")
            return False
    
    def save_chain(self, chain: SkillChain) -> bool:
        """保存技能链配置"""
        try:
            chain_data = {
                'name': chain.name,
                'chain_type': chain.chain_type.value,
                'skill_names': chain.skill_names,
                'description': chain.description,
                'cooldown': chain.cooldown,
                'damage_multiplier': chain.damage_multiplier,
                'effect_multiplier': chain.effect_multiplier,
                'trigger_chance': chain.trigger_chance,
                'requirements': chain.requirements
            }
            
            chain_path = os.path.join(self.config_dir, f"{chain.name}.json")
            with open(chain_path, 'w', encoding='utf-8') as f:
                json.dump(chain_data, f, indent=2, ensure_ascii=False)
            
            self.chains[chain.name] = chain
            return True
            
        except Exception as e:
            self.logger.error(f"保存技能链失败 {chain.name}: {e}")
            return False
    
    def check_chain_trigger(self, hero: Any, used_skill_name: str, 
                           available_skills: List[str]) -> Optional[SkillChain]:
        """检查技能链触发条件"""
        for chain in self.chains.values():
            if self._can_trigger_chain(chain, hero, used_skill_name, available_skills):
                return chain
        return None
    
    def _can_trigger_chain(self, chain: SkillChain, hero: Any, 
                         used_skill_name: str, available_skills: List[str]) -> bool:
        """检查是否可以触发技能链"""
        # 检查技能链是否在冷却中
        if chain.name in self.active_chains:
            chain_info = self.active_chains[chain.name]
            if chain_info['remaining_cooldown'] > 0:
                return False
        
        # 检查技能名称匹配
        if used_skill_name not in chain.skill_names:
            return False
        
        # 检查触发概率
        if random.random() > chain.trigger_chance:
            return False
        
        # 检查技能可用性
        for skill_name in chain.skill_names:
            if skill_name != used_skill_name and skill_name not in available_skills:
                return False
        
        # 检查额外条件
        return self._check_requirements(chain.requirements, hero)
    
    def _check_requirements(self, requirements: Dict[str, Any], hero: Any) -> bool:
        """检查技能链触发条件"""
        if not requirements:
            return True
        
        # 检查血量条件
        if 'health_percent' in requirements:
            health_percent = hero.health / hero.max_health
            req_percent = requirements['health_percent']
            if health_percent > req_percent:
                return False
        
        # 检查状态条件
        if 'status_effects' in requirements:
            required_status = requirements['status_effects']
            hero_status = [effect['type'] for effect in hero.status_effects]
            if not all(status in hero_status for status in required_status):
                return False
        
        # 检查职业条件
        if 'role' in requirements and hero.role != requirements['role']:
            return False
        
        return True
    
    def execute_chain(self, chain: SkillChain, hero: Any, target: Any) -> Dict:
        """执行技能链效果"""
        result = {
            'chain_name': chain.name,
            'damage_multiplier': chain.damage_multiplier,
            'effect_multiplier': chain.effect_multiplier,
            'extra_effects': [],
            'message': f"触发技能链: {chain.name} - {chain.description}"
        }
        
        # 根据技能链类型执行不同效果
        if chain.chain_type == ChainType.COMBO:
            result.update(self._execute_combo_chain(chain, hero, target))
        elif chain.chain_type == ChainType.SEQUENCE:
            result.update(self._execute_sequence_chain(chain, hero, target))
        elif chain.chain_type == ChainType.SYNERGY:
            result.update(self._execute_synergy_chain(chain, hero, target))
        
        # 设置冷却时间
        self.active_chains[chain.name] = {
            'remaining_cooldown': chain.cooldown,
            'last_used': time.time()
        }
        
        return result
    
    def _execute_combo_chain(self, chain: SkillChain, hero: Any, target: Any) -> Dict:
        """执行连招组合效果"""
        # 连招组合：一次性释放所有技能，伤害和效果叠加
        total_damage = 0
        extra_effects = []
        
        for skill_name in chain.skill_names:
            # 这里应该调用实际的技能执行逻辑
            # 简化实现：假设每个技能造成基础伤害
            skill_result = self._simulate_skill_effect(skill_name, hero, target)
            total_damage += skill_result.get('damage', 0)
            extra_effects.extend(skill_result.get('extra_effects', []))
        
        return {
            'damage': int(total_damage * chain.damage_multiplier),
            'extra_effects': extra_effects
        }
    
    def _execute_sequence_chain(self, chain: SkillChain, hero: Any, target: Any) -> Dict:
        """执行顺序释放效果"""
        # 顺序释放：按顺序释放技能，每个技能有独立效果
        # 这里简化实现，实际应该记录释放顺序
        return self._execute_combo_chain(chain, hero, target)  # 暂时使用相同逻辑
    
    def _execute_synergy_chain(self, chain: SkillChain, hero: Any, target: Any) -> Dict:
        """执行协同效果"""
        # 协同效果：技能之间产生特殊互动效果
        extra_effects = []
        
        # 示例：如果包含火系和水系技能，产生蒸汽效果
        if any('fire' in skill.lower() for skill in chain.skill_names) and \
           any('water' in skill.lower() for skill in chain.skill_names):
            extra_effects.append({
                'type': 'steam',
                'duration': 2,
                'damage_per_turn': 50,
                'message': '蒸汽效果：每回合造成50点伤害'
            })
        
        return {
            'damage': 0,  # 协同效果可能不直接造成伤害
            'extra_effects': extra_effects
        }
    
    def _simulate_skill_effect(self, skill_name: str, hero: Any, target: Any) -> Dict:
        """模拟技能效果（简化实现）"""
        # 这里应该调用实际的技能执行逻辑
        # 简化实现：根据技能名称猜测效果
        skill_name_lower = skill_name.lower()
        
        if 'fire' in skill_name_lower:
            return {
                'damage': 100,
                'extra_effects': [{'type': 'burn', 'duration': 2, 'damage_per_turn': 30}]
            }
        elif 'ice' in skill_name_lower:
            return {
                'damage': 80,
                'extra_effects': [{'type': 'freeze', 'duration': 1}]
            }
        elif 'heal' in skill_name_lower:
            return {
                'damage': -150,  # 负伤害表示治疗
                'extra_effects': []
            }
        else:
            return {
                'damage': 120,
                'extra_effects': []
            }
    
    def update_cooldowns(self):
        """更新所有技能链的冷却时间"""
        current_time = time.time()
        chains_to_remove = []
        
        for chain_name, chain_info in self.active_chains.items():
            # 简化实现：每回合减少1冷却
            chain_info['remaining_cooldown'] = max(0, chain_info['remaining_cooldown'] - 1)
            
            if chain_info['remaining_cooldown'] == 0:
                chains_to_remove.append(chain_name)
        
        # 移除冷却完成的技能链
        for chain_name in chains_to_remove:
            del self.active_chains[chain_name]
    
    def get_available_chains(self, hero: Any, available_skills: List[str]) -> List[SkillChain]:
        """获取当前可用的技能链"""
        available_chains = []
        
        for chain in self.chains.values():
            # 检查技能链是否在冷却中
            if chain.name in self.active_chains:
                continue
            
            # 检查技能是否可用
            if all(skill_name in available_skills for skill_name in chain.skill_names):
                # 检查触发条件
                if self._check_requirements(chain.requirements, hero):
                    available_chains.append(chain)
        
        return available_chains


# 全局技能链管理器实例
skill_chain_manager = SkillChainManager()


# 预定义技能链配置
def create_default_chains():
    """创建默认技能链配置"""
    default_chains = [
        SkillChain(
            name="fire_combo",
            chain_type=ChainType.COMBO,
            skill_names=["火球术", "烈焰冲击"],
            description="火焰连招：连续释放火系技能造成额外伤害",
            cooldown=3,
            damage_multiplier=1.5,
            requirements={"role": "DPS"}
        ),
        SkillChain(
            name="ice_sequence",
            chain_type=ChainType.SEQUENCE,
            skill_names=["寒冰箭", "冰霜新星"],
            description="冰霜序列：按顺序释放冰系技能产生控制效果",
            cooldown=2,
            effect_multiplier=2.0,
            requirements={"health_percent": 0.7}
        ),
        SkillChain(
            name="heal_protection",
            chain_type=ChainType.SYNERGY,
            skill_names=["治疗术", "圣光护盾"],
            description="治疗保护：治疗和护盾技能产生协同效果",
            cooldown=4,
            trigger_chance=0.8,
            requirements={"role": "SUPPORT"}
        )
    ]
    
    manager = SkillChainManager()
    for chain in default_chains:
        manager.save_chain(chain)
    
    return manager.load_chains()