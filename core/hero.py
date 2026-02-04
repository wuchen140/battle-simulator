#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英雄类模块
定义英雄属性和技能相关功能
支持插件式技能系统
"""

import random
from typing import Dict, List, Optional, Any
from .plugin_config import plugin_config_manager, PluginConfig

# 全局DEBUG模式控制
DEBUG_MODE = False


class Hero:
    """英雄类"""
    
    def __init__(self, hero_data: Dict, skills_data: List[Dict] = None):
        """初始化英雄属性"""
        self.id = hero_data.get('英雄ID', '')
        self.name = hero_data.get('英雄名称', '')
        self.rank = hero_data.get('品阶', '')
        self.level = hero_data.get('Level', 1)
        self.role = hero_data.get('职业', '')  # 从Excel的'职业'列获取
        self.title = hero_data.get('英雄称号', '')
        self.keywords = self._extract_keywords_from_skills(hero_data, skills_data)  # 从技能数据提取关键词
        self.background = hero_data.get('英雄背景', '')
        self.quote = hero_data.get('英雄台词', '')
        
        # 技能信息
        self.skills = self._create_skills(hero_data, skills_data)
        
        # 插件技能系统
        self.plugin_skills: Dict[str, Any] = {}  # 插件技能字典 {技能名: 插件实例}
        
        # 根据Excel数据设置实际属性
        self._set_actual_attributes(hero_data)
        
        # 战斗状态
        self.health = self.max_health
        self.status_effects = []  # [{'type': 'freeze', 'duration': 2}, ...]
        self.is_frozen = False    # 是否处于冻结状态
        self.is_stunned = False   # 是否处于眩晕状态
        self.is_taunted = False   # 是否处于嘲讽状态
        self.is_paralyzed = False # 是否处于麻痹状态
        self.shield_amount = 0    # 当前护盾值
        self.max_shield = 0       # 最大护盾值
        
        # 被动技能状态跟踪
        self.passive_states = {
            'nano_devour': {
                'max_health_increase': 0,  # 纳米吞噬增加的最大生命值
                'max_health_increase_limit': 500  # 最大生命值增加上限
            },
            'frost_blood': {
                'slow_effects': []  # 寒冰血脉的减速效果列表
            }
        }
        
        # 只有拥有"不屈意志"关键词或技能的英雄才设置不屈意志被动状态
        has_unyielding_will_keyword = '不屈意志' in self.keywords
        has_unyielding_will_skill = self._has_unyielding_will_skill(skills_data)
        
        if has_unyielding_will_keyword or has_unyielding_will_skill:
            self.passive_states['unyielding_will'] = {
                'revived': False,  # 是否已经触发过不屈意志复活
                'attack_boost_remaining': 0,  # 不屈意志攻击力提升剩余回合
                'attack_boost_amount': 0  # 不屈意志攻击力提升数值
            }
    
    def _create_skills(self, hero_data: Dict, skills_data: List[Dict]) -> List[Dict]:
        """创建技能信息，使用实际的技能数值"""
        from data.data_loader import HeroDataLoader
        
        skills = []
        
        # 直接使用技能数据，不再尝试复用display_all_heroes逻辑
        if skills_data:
            # 如果复用逻辑失败，回退到原始逻辑
            hero_skills = []
            for skill_data in skills_data:
                if skill_data.get('名称') == self.name:
                    hero_skills.append(skill_data)
            
            # 过滤掉被动技能
            active_skills = []
            for skill_data in hero_skills:
                skill_desc = str(skill_data.get('技能描述', '')).lower()
                skill_type = str(skill_data.get('技能类型', '')).lower()
                skill_name = str(skill_data.get('技能名称', '')).lower()
                
                # 过滤掉被动技能（类型2为被动技能）
                # 注意：技能类型可能是'2'或'2.0'格式
                if skill_type in ['2', '2.0']:
                    continue
                
                active_skills.append(skill_data)
            
            # 为每个英雄技能创建技能信息
            for i, skill_data in enumerate(active_skills[:3]):  # 最多3个技能
                # 使用Excel中的实际技能名称，如果没有则使用默认名称
                actual_skill_name = skill_data.get('技能名称', '')
                skill_name = actual_skill_name if actual_skill_name else f"技能{i+1}"
                skill_desc = skill_data.get('技能描述', '')
                skill_cd = skill_data.get('技能CD', 0)
                skill_type = skill_data.get('技能类型', '')
                
                # 使用实际的技能数值
                skills.append({
                    'name': skill_name,
                    'description': skill_desc,
                    'cooldown': skill_cd,
                    'current_cooldown': 0,  # 当前冷却回合
                    'skill_type': skill_type,
                    'level1_value': skill_data.get('Level1', 0),
                    'level2_value': skill_data.get('Level2', 0),
                    'level3_value': skill_data.get('Level3', 0),
                    'level4_value': skill_data.get('Level4', 0),
                    'level5_value': skill_data.get('Level5', 0)
                })
        else:
            # 如果没有技能数据，使用默认的技能信息
            for i in range(3):
                skills.append({
                    'name': f"技能{i+1}",
                    'description': '普通攻击',
                    'cooldown': 0,
                    'current_cooldown': 0,
                    'skill_type': '普通技能',
                    'level1_value': 0,
                    'level2_value': 0,
                    'level3_value': 0,
                    'level4_value': 0,
                    'level5_value': 0
                })
        
        return skills

    def _extract_keywords_from_skills(self, hero_data: Dict, skills_data: List[Dict]) -> str:
        """从技能数据中提取被动技能关键词"""
        keywords = []
        
        if skills_data:
            # 获取该英雄的所有技能
            hero_skills = []
            for skill_data in skills_data:
                if skill_data.get('名称') == self.name:
                    hero_skills.append(skill_data)
            
            # 提取被动技能名称作为关键词
            for skill_data in hero_skills:
                skill_type = str(skill_data.get('技能类型', '')).lower()
                skill_name = str(skill_data.get('技能名称', '')).strip()
                
                # 被动技能（类型2）作为关键词
                if skill_type in ['2', '2.0'] and skill_name:
                    keywords.append(skill_name)
        
        # 将关键词列表转换为逗号分隔的字符串
        return ','.join(keywords)

    def _has_unyielding_will_skill(self, skills_data: List[Dict]) -> bool:
        """检查技能数据中是否有不屈意志技能"""
        if not skills_data:
            return False
        
        # 检查该英雄的所有技能中是否有不屈意志
        for skill_data in skills_data:
            if (skill_data.get('名称') == self.name and 
                str(skill_data.get('技能名称', '')).strip() == '不屈意志'):
                return True
        
        return False

    def _set_actual_attributes(self, hero_data: Dict):
        """根据Excel数据设置实际属性"""
        # 直接从Excel数据读取属性
        self.max_health = int(hero_data.get('HP', 1000))
        self.attack = int(hero_data.get('ATK', 100))
        self.defense = int(hero_data.get('DEF', 50))
        self.speed = int(hero_data.get('SPD', 80))
        self.crit_rate = float(hero_data.get('CRIT%', 0.1))
        self.crit_damage = float(hero_data.get('CRIT_DMG', 1.5))

    def _calculate_job_counter_damage(self, target: 'Hero', base_damage: int) -> int:
        """
        计算职业克制伤害加成和稀有度克制伤害加成
        
        职业克制关系：
        - DPS → SNIP: +20% 伤害
        - SNIP → TANK: +20% 伤害  
        - TANK → DPS: +20% 伤害
        - TANK → TANK: +50% 伤害（互相战斗时伤害加成）
        
        稀有度克制关系：
        - SSR → SR: +50% 伤害
        - SSR → R: +100% 伤害
        - SR → R: +50% 伤害
        
        Args:
            target: 目标英雄
            base_damage: 基础伤害值
            
        Returns:
            应用职业克制和稀有度克制后的伤害值
        """
        damage = base_damage
        
        # 职业克制关系检查
        if self.role == 'DPS' and target.role == 'SNIP':
            damage = int(damage * 1.2)
            print(f"职业克制! DPS对SNIP造成额外20%伤害")
        elif self.role == 'SNIP' and target.role == 'TANK':
            damage = int(damage * 1.2)
            print(f"职业克制! SNIP对TANK造成额外20%伤害")
        elif self.role == 'TANK' and target.role == 'DPS':
            damage = int(damage * 1.2)
            print(f"职业克制! TANK对DPS造成额外20%伤害")
        elif self.role == 'TANK' and target.role == 'TANK':
            damage = int(damage * 1.5)
            print(f"TANK对TANK! 伤害加成50%")
        
        # 稀有度克制关系检查
        if self.rank == 'SSR' and target.rank == 'SR':
            damage = int(damage * 1.5)
            print(f"稀有度克制! SSR对SR造成额外50%伤害")
        elif self.rank == 'SSR' and target.rank == 'R':
            damage = int(damage * 2.0)
            print(f"稀有度克制! SSR对R造成额外100%伤害")
        elif self.rank == 'SR' and target.rank == 'R':
            damage = int(damage * 1.5)
            print(f"稀有度克制! SR对R造成额外50%伤害")
        
        return damage

    def attack_target(self, target: 'Hero') -> Dict:
        """攻击目标英雄"""
        # 检查是否处于控制状态
        if self.is_frozen or self.is_stunned or self.is_paralyzed:
            control_type = "冻结" if self.is_frozen else "眩晕" if self.is_stunned else "麻痹"
            return {
                'damage': 0,
                'is_crit': False,
                'target_health': target.health,
                'extra_effects': [],
                'message': f"{self.name} 处于{control_type}状态，无法行动"
            }

        # 从配置中获取防御参数
        from config import DAMAGE_FORMULA_PARAMS
        defense_param1 = DAMAGE_FORMULA_PARAMS['defense_param1']
        defense_param2 = DAMAGE_FORMULA_PARAMS['defense_param2']
        min_damage = DAMAGE_FORMULA_PARAMS['min_damage']
        
        # 计算防御减伤比例：防御力 / (防御力 + (等级 * 参数1 + 参数2))
        defense_reduction = (target.defense / (target.defense + (target.level * defense_param1 + defense_param2)))
        
        # 暴击判断（实际是否触发暴击）
        is_crit = random.random() < self.crit_rate
        
        if is_crit:
            # 暴击伤害公式: 攻击力 * 暴击倍率 * (1 - 防御减伤比例)
            damage = int(self.attack * self.crit_damage * (1 - defense_reduction))
        else:
            # 普通伤害公式: 攻击力 * (1 - 防御减伤比例)
            damage = int(self.attack * (1 - defense_reduction))
        
        # 应用职业克制关系和稀有度克制关系
        damage = self._calculate_job_counter_damage(target, damage)
        
        # 最小伤害保护
        damage = max(min_damage, damage)
        
        # 初始化额外效果列表
        extra_effects = []
        
        # 应用伤害（优先消耗护盾）
        damage_after_shield = damage
        if target.shield_amount > 0:
            # 护盾吸收伤害
            shield_absorbed = min(damage, target.shield_amount)
            target.shield_amount -= shield_absorbed
            damage_after_shield = damage - shield_absorbed
            print(f"{target.name} 的护盾吸收了 {shield_absorbed} 点伤害!")
            if target.shield_amount == 0:
                print(f"{target.name} 的护盾已被击破!")
        
        # 剩余伤害扣除生命值（使用take_damage方法处理被动技能触发）
        if damage_after_shield > 0:
            damage_result = target.take_damage(damage_after_shield, self)
            
            # 如果触发了不屈意志被动，更新伤害结果
            if damage_result.get('passive_triggered', False):
                extra_effects.append({
                    'type': 'passive_trigger',
                    'passive_name': 'unyielding_will',
                    'revive_health': damage_result.get('revive_health', 0),
                    'attack_boost': damage_result.get('attack_boost_amount', 0.0),
                    'attack_boost_percent': int((damage_result.get('attack_boost_amount', 0.0) / (target.attack - damage_result.get('attack_boost_amount', 0.0))) * 100) if (target.attack - damage_result.get('attack_boost_amount', 0.0)) > 0 else 0,
                    'duration': damage_result.get('attack_boost_remaining', 0)
                })
        
        # 寒冰血脉被动效果处理
        if '寒冰血脉' in self.keywords:
            # 20%概率触发减速效果
            if random.random() < 0.2:
                slow_duration = 5  # 减速5秒
                extra_effects.append({
                    'type': 'slow',
                    'duration': slow_duration,
                    'target': target.name
                })
                print(f"{self.name} 的寒冰血脉触发，{target.name} 被减速 {slow_duration} 秒!")
            
            # 检查目标是否已被冻结，如果已冻结则造成额外伤害
            frozen_effects = [eff for eff in target.status_effects if eff.get('type') == 'freeze']
            if frozen_effects:
                extra_damage = int(damage * 0.3)  # 额外30%伤害
                if extra_damage > 0:
                    target.health -= extra_damage
                    target.health = max(0, target.health)
                    extra_effects.append({
                        'type': 'attack',
                        'damage': extra_damage,
                        'is_crit': False,
                        'description': '寒冰血脉对冻结目标的额外伤害'
                    })
                    print(f"{self.name} 的寒冰血脉触发，对冻结的 {target.name} 造成额外 {extra_damage} 点伤害!")
        
        return {
            'damage': damage,
            'is_crit': is_crit,
            'target_health': target.health,
            'extra_effects': extra_effects  # 添加额外效果
        }
    
    def use_skill(self, skill_index: int, target: Optional['Hero'] = None) -> Dict:
        """使用技能"""
        from battle.skill_processor import SkillProcessor
        
        # 检查是否处于控制状态
        if self.is_frozen or self.is_stunned or self.is_paralyzed:
            control_type = "冻结" if self.is_frozen else "眩晕" if self.is_stunned else "麻痹"
            return {'success': False, 'message': f"{self.name} 处于{control_type}状态，无法使用技能"}
            
        if skill_index < 0 or skill_index >= len(self.skills):
            return {'success': False, 'message': '无效的技能索引'}
        
        skill = self.skills[skill_index]
        
        # 检查技能冷却
        if skill['current_cooldown'] > 0:
            return {'success': False, 'message': f"技能冷却中，剩余{skill['current_cooldown']}回合"}
        
        # 设置技能冷却
        if skill['cooldown'] > 0:
            skill['current_cooldown'] = skill['cooldown']
        
        # 使用技能处理器处理技能效果
        return SkillProcessor.process_skill(self, skill, target, self.name, target.name if target else None)
    
    def update_status_effects(self):
        """更新状态效果"""
        from battle.status_manager import StatusManager
        StatusManager.update_hero_status(self)
    
    def get_skill_info(self, skill_index: int) -> Optional[Dict]:
        """获取技能信息"""
        if 0 <= skill_index < len(self.skills):
            return self.skills[skill_index]
        return None
    
    def is_alive(self) -> bool:
        """检查英雄是否存活"""
        return self.health > 0
    
    def reset_cooldowns(self):
        """重置所有技能冷却"""
        for skill in self.skills:
            skill['current_cooldown'] = 0
    
    def add_plugin_skill(self, skill_name: str, plugin_instance: Any) -> bool:
        """添加插件技能"""
        if skill_name in self.plugin_skills:
            return False
        self.plugin_skills[skill_name] = plugin_instance
        return True
    
    def remove_plugin_skill(self, skill_name: str) -> bool:
        """移除插件技能"""
        if skill_name in self.plugin_skills:
            del self.plugin_skills[skill_name]
            return True
        return False
    
    def use_plugin_skill(self, skill_name: str, target: Optional['Hero'] = None, **kwargs) -> Dict:
        """使用插件技能"""
        if skill_name not in self.plugin_skills:
            return {'success': False, 'message': f"未找到插件技能: {skill_name}"}
        
        # 检查是否处于控制状态
        if self.is_frozen or self.is_stunned or self.is_paralyzed:
            control_type = "冻结" if self.is_frozen else "眩晕" if self.is_stunned else "麻痹"
            return {'success': False, 'message': f"{self.name} 处于{control_type}状态，无法使用技能"}
        
        try:
            plugin = self.plugin_skills[skill_name]
            result = plugin.execute(self, target, **kwargs)
            return result
        except Exception as e:
            return {'success': False, 'message': f"执行插件技能失败: {str(e)}"}
    
    def get_plugin_skills(self) -> List[str]:
        """获取所有插件技能名称"""
        return list(self.plugin_skills.keys())
    
    def take_damage(self, damage: int, attacker: Optional['Hero'] = None) -> Dict:
        """
        英雄受到伤害处理，包含被动技能触发逻辑
        
        Args:
            damage: 受到的伤害值
            attacker: 攻击者英雄对象（可选）
            
        Returns:
            包含伤害处理结果的字典
        """
        result = {
            'damage_taken': damage,
            'original_health': self.health,
            'is_alive': True,
            'passive_triggered': False,
            'triggered_passive': None,
            'revived': False
        }
        
        # 优先消耗护盾
        damage_after_shield = damage
        if self.shield_amount > 0:
            shield_absorbed = min(damage, self.shield_amount)
            self.shield_amount -= shield_absorbed
            damage_after_shield = damage - shield_absorbed
            result['shield_absorbed'] = shield_absorbed
            
            if self.shield_amount == 0:
                result['shield_broken'] = True
        
        # 剩余伤害扣除生命值
        if damage_after_shield > 0:
            old_health = self.health
            self.health -= damage_after_shield
            self.health = max(0, self.health)
            result['damage_after_shield'] = damage_after_shield
            result['health_after_damage'] = self.health
            
            # 检查是否死亡并触发被动技能
            if old_health > 0 and self.health == 0:
                # 检查"不屈意志"被动技能
                if 'unyielding_will' in self.passive_states:
                    passive_state = self.passive_states['unyielding_will']
                    # 首次阵亡时触发复活
                    if not passive_state.get('revived', False):
                        # 复活并恢复40%最大生命值
                        revive_health = int(self.max_health * 0.4)
                        self.health = revive_health
                        passive_state['revived'] = True
                        passive_state['attack_boost_remaining'] = 10  # 10秒攻击力提升
                        # 根据技能等级计算攻击力提升比例：一级60%，二级65%，以此类推
                        attack_boost_percent = 0.55 + self.level * 0.05  # 基础55% + 每级5%
                        passive_state['attack_boost_amount'] = int(self.attack * attack_boost_percent)
                        
                        # 立即增加攻击力
                        self.attack += passive_state['attack_boost_amount']
                        
                        result.update({
                            'passive_triggered': True,
                            'triggered_passive': 'unyielding_will',
                            'revived': True,
                            'revive_health': revive_health,
                            'attack_boost_remaining': 10,
                            'attack_boost_amount': passive_state['attack_boost_amount']  # 使用实际的攻击力提升数值
                        })
                        
                        print(f"{self.name} 的不屈意志触发! 复活并恢复{revive_health}点生命值，攻击力提升{int(attack_boost_percent*100)}%持续10秒")
        
        result['is_alive'] = self.health > 0
        return result

    def __str__(self) -> str:
        """返回英雄信息字符串"""
        plugin_skills_info = f" | 插件技能: {len(self.plugin_skills)}个" if self.plugin_skills else ""
        return (f"英雄: {self.name} (Lv.{self.level}) | "
                f"HP: {self.health}/{self.max_health} | "
                f"ATK: {self.attack} | DEF: {self.defense}"
                f"{plugin_skills_info}")