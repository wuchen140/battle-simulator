#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态管理器模块
处理英雄状态效果和状态更新
"""

from typing import Dict, List


class StatusManager:
    """状态管理器"""
    
    @staticmethod
    def update_hero_status(hero, display_name=None):
        """更新英雄状态效果"""
        # 使用显示名称，如果没有提供则使用原始名称
        hero_name = display_name if display_name else hero.name
        
        # 更新状态效果持续时间
        new_effects = []
        
        for effect in hero.status_effects:
            effect['duration'] -= 1
            if effect['duration'] > 0:
                new_effects.append(effect)
            else:
                # 效果结束，清除对应状态
                if effect['type'] == 'freeze':
                    hero.is_frozen = False
                    print(f"{hero_name} 的冻结状态结束!")
                elif effect['type'] == 'stun':
                    hero.is_stunned = False
                    print(f"{hero_name} 的眩晕状态结束!")
                elif effect['type'] == 'taunt':
                    hero.is_taunted = False
                    print(f"{hero_name} 的嘲讽状态结束!")
                elif effect['type'] == 'paralyze':
                    hero.is_paralyzed = False
                    print(f"{hero_name} 的麻痹状态结束!")
                elif effect['type'] == 'armor_reduction':
                    # 恢复防御值
                    if 'original_defense' in effect:
                        hero.defense = effect['original_defense']
                    print(f"{hero_name} 的防御值降低状态结束!")
                    print(f"{hero_name} 防御值恢复至: {hero.defense}")
                elif effect['type'] == 'shield':
                    # 护盾效果结束
                    hero.shield_amount = 0
                    hero.max_shield = 0
                    print(f"{hero_name} 的护盾效果结束!")
                elif effect['type'] == 'buff':
                    # 移除增益效果
                    StatusManager._remove_buff_effect(hero, effect, hero_name)
                elif effect['type'] == 'debuff':
                    # 移除减益效果
                    StatusManager._remove_debuff_effect(hero, effect, hero_name)
        
        hero.status_effects = new_effects
        
        # 更新被动技能状态
        StatusManager._update_passive_states(hero, hero_name)

    @staticmethod
    def _remove_buff_effect(hero, effect, hero_name):
        """移除增益效果"""
        buff_type = effect['buff_type']
        
        if buff_type == 'attack':
            boost_amount = effect.get('boost_amount', 0)
            hero.attack -= boost_amount
            print(f"{hero_name} 的攻击力提升效果结束，攻击力减少 {boost_amount} 点!")
        elif buff_type == 'defense':
            boost_amount = effect.get('boost_amount', 0)
            hero.defense -= boost_amount
            print(f"{hero_name} 的防御力提升效果结束，防御力减少 {boost_amount} 点!")
        elif buff_type == 'crit_rate':
            hero.crit_rate -= effect['value']
            print(f"{hero_name} 的暴击率提升效果结束，暴击率减少 {effect['value']*100}%!")
        elif buff_type == 'crit_damage':
            hero.crit_damage -= effect['value']
            print(f"{hero_name} 的暴击伤害提升效果结束，暴击伤害减少 {effect['value']*100}%!")
        elif buff_type == 'max_health':
            boost_amount = effect.get('boost_amount', 0)
            hero.max_health -= boost_amount
            hero.health = min(hero.health, hero.max_health)  # 确保当前生命值不超过最大生命值
            print(f"{hero_name} 的最大生命值提升效果结束，最大生命值减少 {boost_amount} 点!")

    @staticmethod
    def _remove_debuff_effect(hero, effect, hero_name):
        """移除减益效果"""
        debuff_type = effect['debuff_type']
        
        if debuff_type == 'attack':
            reduction_amount = effect.get('reduction_amount', 0)
            hero.attack += reduction_amount
            print(f"{hero_name} 的攻击力降低效果结束，攻击力恢复 {reduction_amount} 点!")
        elif debuff_type == 'defense':
            reduction_amount = effect.get('reduction_amount', 0)
            hero.defense += reduction_amount
            print(f"{hero_name} 的防御力降低效果结束，防御力恢复 {reduction_amount} 点!")
        elif debuff_type == 'crit_rate':
            hero.crit_rate += effect['value']
            print(f"{hero_name} 的暴击率降低效果结束，暴击率恢复 {effect['value']*100}%!")
        elif debuff_type == 'crit_damage':
            hero.crit_damage += effect['value']
            print(f"{hero_name} 的暴击伤害降低效果结束，暴击伤害恢复 {effect['value']*100}%!")
    
    @staticmethod
    def _update_passive_states(hero, hero_name):
        """更新被动技能状态"""
        # 更新不屈意志攻击力提升剩余回合（仅当英雄拥有该被动技能时）
        if 'unyielding_will' in hero.passive_states and hero.passive_states['unyielding_will']['attack_boost_remaining'] > 0:
            hero.passive_states['unyielding_will']['attack_boost_remaining'] -= 1
            if hero.passive_states['unyielding_will']['attack_boost_remaining'] == 0:
                # 攻击力提升效果结束
                boost_amount = hero.passive_states['unyielding_will']['attack_boost_amount']
                hero.attack -= boost_amount
                hero.passive_states['unyielding_will']['attack_boost_amount'] = 0
                print(f"{hero_name} 的不屈意志攻击力提升效果结束!")
        
        # 更新寒冰血脉减速效果
        if hero.passive_states['frost_blood']['slow_effects']:
            new_slow_effects = []
            for slow_effect in hero.passive_states['frost_blood']['slow_effects']:
                slow_effect['remaining'] -= 1
                if slow_effect['remaining'] > 0:
                    new_slow_effects.append(slow_effect)
            hero.passive_states['frost_blood']['slow_effects'] = new_slow_effects
    
    @staticmethod
    def apply_status_effect(hero, effect_type: str, duration: int, display_name=None, **kwargs):
        """应用状态效果"""
        # 使用显示名称，如果没有提供则使用原始名称
        hero_name = display_name if display_name else hero.name
        
        effect = {
            'type': effect_type,
            'duration': duration,
            **kwargs
        }
        
        # 移除同类型的旧效果
        hero.status_effects = [eff for eff in hero.status_effects if eff['type'] != effect_type]
        
        # 添加新效果
        hero.status_effects.append(effect)
        
        # 立即设置对应状态
        if effect_type == 'freeze':
            hero.is_frozen = True
        elif effect_type == 'stun':
            hero.is_stunned = True
        elif effect_type == 'taunt':
            hero.is_taunted = True
        elif effect_type == 'paralyze':
            hero.is_paralyzed = True
        
        print(f"{hero_name} 被施加 {effect_type} 效果，持续 {duration} 回合!")

    @staticmethod
    def apply_buff_effect(hero, buff_type: str, value: float, duration: int, display_name=None, 
                       source=None, is_percentage=True):
        """应用增益效果"""
        hero_name = display_name if display_name else hero.name
        
        effect = {
            'type': 'buff',
            'buff_type': buff_type,
            'value': value,
            'duration': duration,
            'is_percentage': is_percentage,
            'source': source
        }
        
        # 应用增益效果
        if buff_type == 'attack':
            if is_percentage:
                boost_amount = int(hero.attack * value)
            else:
                boost_amount = int(value)
            hero.attack += boost_amount
            effect['boost_amount'] = boost_amount
            print(f"{hero_name} 攻击力提升 {boost_amount} 点，持续 {duration} 回合!")
            
        elif buff_type == 'defense':
            if is_percentage:
                boost_amount = int(hero.defense * value)
            else:
                boost_amount = int(value)
            hero.defense += boost_amount
            effect['boost_amount'] = boost_amount
            print(f"{hero_name} 防御力提升 {boost_amount} 点，持续 {duration} 回合!")
            
        elif buff_type == 'crit_rate':
            hero.crit_rate += value
            print(f"{hero_name} 暴击率提升 {value*100}%，持续 {duration} 回合!")
            
        elif buff_type == 'crit_damage':
            hero.crit_damage += value
            print(f"{hero_name} 暴击伤害提升 {value*100}%，持续 {duration} 回合!")
            
        elif buff_type == 'max_health':
            if is_percentage:
                boost_amount = int(hero.max_health * value)
            else:
                boost_amount = int(value)
            hero.max_health += boost_amount
            hero.health += boost_amount  # 同时增加当前生命值
            effect['boost_amount'] = boost_amount
            print(f"{hero_name} 最大生命值提升 {boost_amount} 点，持续 {duration} 回合!")
        
        # 添加到状态效果列表
        hero.status_effects.append(effect)

    @staticmethod
    def apply_debuff_effect(hero, debuff_type: str, value: float, duration: int, display_name=None,
                          source=None, is_percentage=True):
        """应用减益效果"""
        hero_name = display_name if display_name else hero.name
        
        effect = {
            'type': 'debuff',
            'debuff_type': debuff_type,
            'value': value,
            'duration': duration,
            'is_percentage': is_percentage,
            'source': source
        }
        
        # 应用减益效果
        if debuff_type == 'attack':
            if is_percentage:
                reduction_amount = int(hero.attack * value)
            else:
                reduction_amount = int(value)
            hero.attack = max(0, hero.attack - reduction_amount)
            effect['reduction_amount'] = reduction_amount
            print(f"{hero_name} 攻击力降低 {reduction_amount} 点，持续 {duration} 回合!")
            
        elif debuff_type == 'defense':
            if is_percentage:
                reduction_amount = int(hero.defense * value)
            else:
                reduction_amount = int(value)
            hero.defense = max(0, hero.defense - reduction_amount)
            effect['reduction_amount'] = reduction_amount
            print(f"{hero_name} 防御力降低 {reduction_amount} 点，持续 {duration} 回合!")
            
        elif debuff_type == 'crit_rate':
            hero.crit_rate = max(0, hero.crit_rate - value)
            print(f"{hero_name} 暴击率降低 {value*100}%，持续 {duration} 回合!")
            
        elif debuff_type == 'crit_damage':
            hero.crit_damage = max(1.0, hero.crit_damage - value)
            print(f"{hero_name} 暴击伤害降低 {value*100}%，持续 {duration} 回合!")
        
        # 添加到状态效果列表
        hero.status_effects.append(effect)

    @staticmethod
    def apply_shield_effect(hero, shield_amount: int, duration: int, display_name=None, source=None):
        """应用护盾效果"""
        hero_name = display_name if display_name else hero.name
        
        effect = {
            'type': 'shield',
            'amount': shield_amount,
            'duration': duration,
            'source': source
        }
        
        # 设置护盾值
        hero.shield_amount = shield_amount
        hero.max_shield = shield_amount
        
        print(f"{hero_name} 获得 {shield_amount} 点护盾，持续 {duration} 回合!")
        
        # 添加到状态效果列表
        hero.status_effects.append(effect)
    
    @staticmethod
    def clear_all_status_effects(hero, display_name=None):
        """清除所有状态效果"""
        # 使用显示名称，如果没有提供则使用原始名称
        hero_name = display_name if display_name else hero.name
        
        hero.status_effects = []
        hero.is_frozen = False
        hero.is_stunned = False
        print(f"{hero_name} 的所有状态效果已被清除!")
    
    @staticmethod
    def has_status_effect(hero, effect_type: str) -> bool:
        """检查是否具有特定状态效果"""
        return any(eff['type'] == effect_type for eff in hero.status_effects)
    
    @staticmethod
    def get_status_effect_duration(hero, effect_type: str) -> int:
        """获取特定状态效果的剩余持续时间"""
        for effect in hero.status_effects:
            if effect['type'] == effect_type:
                return effect['duration']
        return 0
    
    @staticmethod
    def get_active_effects(hero_name: str) -> List[Dict]:
        """获取指定英雄的当前活跃状态效果"""
        # 这个方法需要从全局状态管理器中获取效果，但目前我们简化实现
        # 在实际应用中，这里应该查询全局状态管理器
        # 暂时返回空列表，避免错误
        return []