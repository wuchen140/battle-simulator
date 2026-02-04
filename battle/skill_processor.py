#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能处理器模块
处理技能效果和逻辑
"""

import random
import os
import json
from typing import Dict, Optional, List, Any

# 全局DEBUG模式控制
DEBUG_MODE = False

# 尝试导入技能编辑器
SKILL_EDITOR_ENABLED = False
try:
    from battle.skill_editor import SkillEditor, SkillEffect, DamageEffect, HealEffect, BuffEffect, DebuffEffect, ControlEffect, ShieldEffect
    SKILL_EDITOR_ENABLED = True
except ImportError:
    print("技能编辑器模块未找到，自定义技能功能将不可用")
    SKILL_EDITOR_ENABLED = False


class SkillProcessor:
    """技能处理器"""
    
    @staticmethod
    def process_skill(hero, skill: Dict, target=None, display_name=None, target_display_name=None) -> Dict:
        """处理技能效果
        
        Args:
            hero: 使用技能的英雄对象
            skill: 技能字典
            target: 目标英雄对象（可选）
            display_name: 英雄的显示名称（带标识符）
            target_display_name: 目标的显示名称（带标识符）
            
        Returns:
            包含技能效果结果的字典
        """
        # 使用显示名称，如果没有提供则使用原始名称
        hero_name = display_name if display_name else hero.name
        target_name = target_display_name if target_display_name else (target.name if target else None)
        
        # 根据英雄等级获取技能数值（系数）
        skill_coefficient = SkillProcessor._get_skill_value(hero, skill)
        
        # 根据技能类型和描述模拟技能效果
        skill_desc = skill['description'].lower()
        result = {'success': True, 'skill_name': skill['name'], 'effects': []}
        
        # 首先检查是否为自定义技能（使用技能编辑器创建的技能）
        if SKILL_EDITOR_ENABLED and 'effects' in skill and isinstance(skill['effects'], list):
            return SkillProcessor._process_custom_skill(hero, skill, target, result, hero_name, target_name)
        
        # 特殊技能处理 - 永夜终焉（优先处理）
        if '永夜终焉' in skill['name']:
            return SkillProcessor._process_eternal_night(hero, skill, target, result, hero_name, target_name)
        
        # 特殊技能处理 - 毁灭重铸
        if '毁灭重铸' in skill['name']:
            return SkillProcessor._process_destruction_reforge(hero, skill, target, result, hero_name, target_name)
        
        # 特殊技能处理 - 超载穿透弹
        if '超载穿透弹' in skill['name']:
            return SkillProcessor._process_overload_penetration(hero, skill, target, result, hero_name, target_name)
        
        # 特殊技能处理 - 碎颅猛击
        if '碎颅猛击' in skill['name']:
            return SkillProcessor._process_skull_smash(hero, skill, target, result, hero_name, target_name)
        
        # 特殊技能处理 - 举盾防御
        if '举盾防御' in skill['name']:
            return SkillProcessor._process_shield_defense(hero, skill, result, hero_name)
        
        # 检查技能使用类型（主动/被动）
        from data.data_loader import HeroDataLoader
        skill_type = skill.get('技能类型', '')  # 从技能字典中获取技能类型
        usage_type = HeroDataLoader.get_skill_usage_type(skill_type)
        
        # 主动技能：全部生效
        if usage_type == 'active':
            # 技能类型1: 伤害类技能（攻击型）
            if str(skill_type) in ['1', '1.0'] or (('攻击' in skill_desc or '伤害' in skill_desc) and str(skill_type) not in ['3', '3.0']):
                return SkillProcessor._process_damage_skill(hero, skill, target, skill_coefficient, result)
            
            # 技能类型2: 控制类技能
            elif str(skill_type) in ['2', '2.0'] or ('眩晕' in skill_desc or '冻结' in skill_desc or '沉默' in skill_desc or '控制' in skill_desc):
                return SkillProcessor._process_control_skill(hero, skill, target, skill_coefficient, result, hero_name, target_name)
            
            # 技能类型3: BUFF类技能（增益效果）
            elif str(skill_type) in ['3', '3.0'] or ('攻击提升' in skill_desc or '防御提升' in skill_desc or '暴击提升' in skill_desc or '增益' in skill_desc):
                return SkillProcessor._process_buff_skill(hero, skill, skill_coefficient, result, hero_name)
            
            # 默认处理：普通攻击
            else:
                return SkillProcessor._process_default_attack(hero, target, result, hero_name, target_name)
        
        # 被动技能：只有控制类和BUFF类生效
        elif usage_type == 'passive':
            # 解析伤害类型
            damage_types = HeroDataLoader.parse_damage_types(skill.get('技能伤害类型'))
            
            # 被动技能中只有控制类和BUFF类生效
            if 'control' in damage_types or 'buff' in damage_types:
                # 控制类被动技能
                if 'control' in damage_types:
                    return SkillProcessor._process_control_skill(hero, skill, target, skill_coefficient, result, hero_name, target_name)
                # BUFF类被动技能  
                elif 'buff' in damage_types:
                    return SkillProcessor._process_buff_skill(hero, skill, skill_coefficient, result, hero_name)
            else:
                # 其他类型的被动技能不产生战斗效果
                print(f"    {hero_name} 被动技能: {skill['name']} 不产生战斗效果")
                return result
        
        # 未知类型的技能：使用默认攻击处理
        else:
            print(f"    {hero_name} 未知类型技能: {skill['name']}，使用默认攻击")
            return SkillProcessor._process_default_attack(hero, target, result, hero_name, target_name)

    @staticmethod
    def _process_shield_defense(hero, skill: Dict, result: Dict, hero_name: str) -> Dict:
        """处理举盾防御特殊技能
        
        技能效果：为自身施加持续4秒的护盾，吸收伤害值分别为：
        1级：500点，2级：1000点，3级：1500点，4级：2000点，5级：2500点
        """
        if DEBUG_MODE:
            print(f"DEBUG: 进入举盾防御特殊技能处理")
        
        # 检查是否处于控制状态
        if hero.is_frozen or hero.is_stunned:
            control_type = "冰冻" if hero.is_frozen else "眩晕"
            print(f"{hero_name} 处于{control_type}状态，无法使用技能!")
            return {'success': False, 'message': f"处于{control_type}状态"}

        # 获取技能等级，默认为1级
        skill_level = skill.get('level', 1)
        
        # 根据技能等级计算护盾吸收值
        shield_amounts = {1: 500, 2: 1000, 3: 1500, 4: 2000, 5: 2500}
        shield_value = shield_amounts.get(skill_level, 500)
        
        # 设置护盾值
        hero.shield_amount = shield_value
        hero.max_shield = shield_value
        
        # 添加护盾状态效果（持续4秒）
        from battle.status_manager import StatusManager
        StatusManager.apply_status_effect(hero, 'shield', 4, hero_name, 
                                       source=hero_name, amount=shield_value)
        
        # 记录技能效果
        result['effects'].append({
            'type': 'buff',
            'subtype': 'shield',
            'amount': shield_value,
            'duration': 4,
            'target': hero_name,
            'source': hero_name
        })
        
        print(f"{hero_name} 使用举盾防御！")
        print(f"获得 {shield_value} 点护盾，持续4秒！")
        print(f"{hero_name} 当前护盾值：{hero.shield_amount}/{hero.max_shield}")
        
        return result

    @staticmethod
    def _process_overload_penetration(hero, skill: Dict, target, result: Dict, hero_name: str, target_name: str) -> Dict:
        """处理超载穿透弹特殊技能
        
        技能效果：1级400点ATK伤害，2级450点ATK伤害，3级500点ATK伤害，4级550点ATK伤害，5级600点ATK伤害
        将基础伤害值带入攻击公式计算最终伤害
        30%概率使目标麻痹（无法行动）1.5秒
        """
        if DEBUG_MODE:
            print(f"DEBUG: 进入超载穿透弹特殊技能处理")
        
        # 检查是否处于控制状态
        if hero.is_frozen or hero.is_stunned or hero.is_paralyzed:
            control_type = "冰冻" if hero.is_frozen else "眩晕" if hero.is_stunned else "麻痹"
            print(f"{hero_name} 处于{control_type}状态，无法使用技能!")
            return {'success': False, 'message': f"处于{control_type}状态"}

        # 由于当前是1v1战斗，暂时只对目标生效
        if target:
            # 根据英雄等级获取基础伤害值
            level_values = skill.get('level_values', {})
            base_damage = level_values.get(hero.level, 400)  # 默认1级400点伤害
            
            # 使用攻击公式计算最终伤害
            damage_result = SkillProcessor.process_damage(
                base_damage=base_damage,
                defense=target.defense,
                crit_rate=hero.crit_rate,
                crit_damage=hero.crit_damage,
                target_level=target.level
            )
            
            final_damage = damage_result['damage']
            is_crit = damage_result['is_crit']
            
            # 应用伤害（优先消耗护盾）
            damage_after_shield = final_damage
            if target.shield_amount > 0:
                # 护盾吸收伤害
                shield_absorbed = min(final_damage, target.shield_amount)
                target.shield_amount -= shield_absorbed
                damage_after_shield = final_damage - shield_absorbed
                print(f"{target.name} 的护盾吸收了 {shield_absorbed} 点伤害!")
                if target.shield_amount == 0:
                    print(f"{target.name} 的护盾已被击破!")
            
            # 剩余伤害扣除生命值（使用标准伤害处理流程）
            if damage_after_shield > 0:
                damage_result = target.take_damage(damage_after_shield)
                
                # 检查是否有被动技能触发信息
                if damage_result.get('passive_triggered', False) and damage_result.get('triggered_passive') == 'unyielding_will':
                    print(f"🎉 {target_name} 触发不屈意志!")
                    result['effects'].append({
                        'type': 'passive_trigger',
                        'passive_name': 'unyielding_will',
                        'revive_health': damage_result.get('revive_health', 0),
                        'attack_boost_percent': int((damage_result.get('attack_boost_amount', 0) / (target.attack - damage_result.get('attack_boost_amount', 0))) * 100) if (target.attack - damage_result.get('attack_boost_amount', 0)) > 0 else 30
                    })
            
            # 30%概率触发麻痹效果
            if random.random() < 0.3:  # 30%概率
                # 添加麻痹效果（1.5秒，向上取整为2回合）
                from battle.status_manager import StatusManager
                StatusManager.apply_status_effect(target, 'paralyze', 2, target_name, source=hero_name)
                
                result['effects'].append({
                    'type': 'control',
                    'subtype': 'paralyze',
                    'duration': 2,
                    'target': target_name,
                    'source': hero_name
                })
            else:
                # 将抵抗信息添加到效果中
                result['effects'].append({
                    'type': 'resist',
                    'skill_name': '超载穿透弹',
                    'effect_type': 'paralyze',
                    'target': target_name
                })
            
            # 记录伤害效果
            result['effects'].append({
                'type': 'attack',
                'damage': final_damage,
                'is_crit': is_crit,
                'target': target_name,
                'base_damage': base_damage  # 记录基础伤害值用于调试
            })
            
            print(f"{hero_name} 使用超载穿透弹，造成 {final_damage} 点伤害！")
            if is_crit:
                print(f"暴击！伤害翻倍！")
            
            # 如果触发了麻痹效果，在状态管理器中已经打印了信息
        
        return result

    @staticmethod
    def _process_custom_skill(hero, skill: Dict, target, result: Dict, hero_name: str, target_name: str) -> Dict:
        """处理自定义技能（使用技能编辑器创建的技能）
        
        Args:
            hero: 使用技能的英雄对象
            skill: 技能字典（包含effects列表）
            target: 目标英雄对象
            result: 结果字典
            hero_name: 英雄显示名称
            target_name: 目标显示名称
            
        Returns:
            包含技能效果结果的字典
        """
        if DEBUG_MODE:
            print(f"DEBUG: 处理自定义技能: {skill['name']}")
        
        # 检查是否处于控制状态
        if hero.is_frozen or hero.is_stunned or hero.is_paralyzed:
            control_type = "冰冻" if hero.is_frozen else "眩晕" if hero.is_stunned else "麻痹"
            print(f"{hero_name} 处于{control_type}状态，无法使用技能!")
            return {'success': False, 'message': f"处于{control_type}状态"}
        
        # 处理所有效果
        for effect_data in skill.get('effects', []):
            SkillProcessor._process_custom_effect(hero, effect_data, target, result, hero_name, target_name)
        
        return result

    @staticmethod
    def _process_custom_effect(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义技能效果"""
        effect_type = effect_data.get('type')
        trigger = effect_data.get('trigger', 'on_cast')
        probability = effect_data.get('probability', 1.0)
        
        # 检查触发概率
        if random.random() > probability:
            if DEBUG_MODE:
                print(f"DEBUG: 效果 {effect_type} 未触发 (概率: {probability})")
            return
        
        # 根据效果类型处理
        if effect_type == 'damage':
            SkillProcessor._process_custom_damage(hero, effect_data, target, result, hero_name, target_name)
        elif effect_type == 'heal':
            SkillProcessor._process_custom_heal(hero, effect_data, target, result, hero_name, target_name)
        elif effect_type == 'buff':
            SkillProcessor._process_custom_buff(hero, effect_data, target, result, hero_name, target_name)
        elif effect_type == 'debuff':
            SkillProcessor._process_custom_debuff(hero, effect_data, target, result, hero_name, target_name)
        elif effect_type == 'control':
            SkillProcessor._process_custom_control(hero, effect_data, target, result, hero_name, target_name)
        elif effect_type == 'shield':
            SkillProcessor._process_custom_shield(hero, effect_data, target, result, hero_name, target_name)
        elif effect_type == 'status':
            SkillProcessor._process_custom_status(hero, effect_data, target, result, hero_name, target_name)
        else:
            if DEBUG_MODE:
                print(f"DEBUG: 未知效果类型: {effect_type}")

    @staticmethod
    def _process_custom_damage(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义伤害效果"""
        if not target:
            return
        
        base_damage = effect_data.get('base_damage', 0)
        damage_multiplier = effect_data.get('damage_multiplier', 1.0)
        ignore_defense = effect_data.get('ignore_defense', False)
        can_crit = effect_data.get('can_crit', True)
        
        # 计算最终伤害
        final_damage = int(base_damage * damage_multiplier)
        
        # 如果不无视防御，应用防御计算
        if not ignore_defense:
            damage_result = SkillProcessor.process_damage(
                base_damage=final_damage,
                defense=target.defense,
                crit_rate=hero.crit_rate if can_crit else 0.0,
                crit_damage=hero.crit_damage,
                target_level=target.level
            )
            final_damage = damage_result['damage']
            is_crit = damage_result['is_crit']
        else:
            is_crit = False
        
        # 应用职业克制关系和稀有度克制关系
        final_damage = SkillProcessor._calculate_job_counter_damage(hero.role, target.role, final_damage, hero.rank, target.rank)
        
        # 应用伤害（优先消耗护盾）
        damage_after_shield = final_damage
        if target.shield_amount > 0:
            shield_absorbed = min(final_damage, target.shield_amount)
            target.shield_amount -= shield_absorbed
            damage_after_shield = final_damage - shield_absorbed
            print(f"{target_name} 的护盾吸收了 {shield_absorbed} 点伤害!")
            if target.shield_amount == 0:
                print(f"{target_name} 的护盾已被击破!")
        
        # 剩余伤害扣除生命值
        if damage_after_shield > 0:
            target.health -= damage_after_shield
            target.health = max(0, target.health)
        
        # 记录效果
        result['effects'].append({
            'type': 'attack',
            'damage': final_damage,
            'is_crit': is_crit,
            'target': target_name,
            'damage_type': effect_data.get('damage_type', 'physical')
        })
        
        print(f"{hero_name} 造成 {final_damage} 点伤害！")
        if is_crit:
            print("暴击！")

    @staticmethod
    def _process_custom_heal(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义治疗效果"""
        heal_target = target if effect_data.get('target_type') == 'single_ally' else hero
        target_display = target_name if effect_data.get('target_type') == 'single_ally' else hero_name
        
        base_heal = effect_data.get('base_heal', 0)
        heal_multiplier = effect_data.get('heal_multiplier', 1.0)
        is_percentage = effect_data.get('is_percentage', False)
        
        if is_percentage:
            # 百分比治疗
            heal_amount = int(heal_target.max_health * base_heal * heal_multiplier)
        else:
            # 固定值治疗
            heal_amount = int(base_heal * heal_multiplier)
        
        # 应用治疗
        heal_target.health += heal_amount
        heal_target.health = min(heal_target.health, heal_target.max_health)
        
        # 记录效果
        result['effects'].append({
            'type': 'heal',
            'amount': heal_amount,
            'target': target_display,
            'source': hero_name
        })
        
        print(f"{hero_name} 治疗 {target_display} {heal_amount} 点生命值！")

    @staticmethod
    def _process_custom_buff(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义增益效果"""
        buff_target = target if effect_data.get('target_type') == 'single_ally' else hero
        target_display = target_name if effect_data.get('target_type') == 'single_ally' else hero_name
        
        buff_type = effect_data.get('buff_type', 'attack')
        value = effect_data.get('value', 0.0)
        is_percentage = effect_data.get('is_percentage', True)
        duration = effect_data.get('duration', 0)
        
        # 应用增益效果
        from battle.status_manager import StatusManager
        StatusManager.apply_buff_effect(buff_target, buff_type, value, duration, target_display, 
                                     source=hero_name, is_percentage=is_percentage)
        
        # 记录效果
        result['effects'].append({
            'type': 'buff',
            'subtype': buff_type,
            'value': value,
            'duration': duration,
            'target': target_display,
            'source': hero_name,
            'is_percentage': is_percentage
        })
        
        print(f"{hero_name} 为 {target_display} 施加 {buff_type} 增益效果！")

    @staticmethod
    def _process_custom_debuff(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义减益效果"""
        if not target:
            return
        
        debuff_type = effect_data.get('debuff_type', 'attack')
        value = effect_data.get('value', 0.0)
        is_percentage = effect_data.get('is_percentage', True)
        duration = effect_data.get('duration', 0)
        
        # 应用减益效果
        from battle.status_manager import StatusManager
        StatusManager.apply_debuff_effect(target, debuff_type, value, duration, target_name, 
                                       source=hero_name, is_percentage=is_percentage)
        
        # 记录效果
        result['effects'].append({
            'type': 'debuff',
            'subtype': debuff_type,
            'value': value,
            'duration': duration,
            'target': target_name,
            'source': hero_name,
            'is_percentage': is_percentage
        })
        
        print(f"{hero_name} 对 {target_name} 施加 {debuff_type} 减益效果！")

    @staticmethod
    def _process_custom_control(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义控制效果"""
        if not target:
            return
        
        control_type = effect_data.get('control_type', 'stun')
        duration = effect_data.get('duration', 2)
        
        # 应用控制效果
        from battle.status_manager import StatusManager
        StatusManager.apply_status_effect(target, control_type, duration, target_name, source=hero_name)
        
        # 记录效果
        result['effects'].append({
            'type': 'control',
            'subtype': control_type,
            'duration': duration,
            'target': target_name,
            'source': hero_name
        })
        
        print(f"{hero_name} 对 {target_name} 施加 {control_type} 控制效果，持续 {duration} 秒！")

    @staticmethod
    def _process_custom_shield(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义护盾效果"""
        shield_target = target if effect_data.get('target_type') == 'single_ally' else hero
        target_display = target_name if effect_data.get('target_type') == 'single_ally' else hero_name
        
        shield_amount = effect_data.get('shield_amount', 0)
        is_percentage = effect_data.get('is_percentage', False)
        duration = effect_data.get('duration', 0)
        
        if is_percentage:
            # 百分比护盾
            actual_shield = int(shield_target.max_health * shield_amount)
        else:
            # 固定值护盾
            actual_shield = shield_amount
        
        # 应用护盾效果
        from battle.status_manager import StatusManager
        StatusManager.apply_shield_effect(shield_target, actual_shield, duration, target_display, source=hero_name)
        
        # 记录效果
        result['effects'].append({
            'type': 'shield',
            'amount': actual_shield,
            'duration': duration,
            'target': target_display,
            'source': hero_name
        })
        
        print(f"{hero_name} 为 {target_display} 施加 {actual_shield} 点护盾，持续 {duration} 秒！")

    @staticmethod
    def _process_custom_status(hero, effect_data: Dict, target, result: Dict, hero_name: str, target_name: str):
        """处理自定义状态效果"""
        status_target = target if effect_data.get('target_type') == 'single_enemy' else hero
        target_display = target_name if effect_data.get('target_type') == 'single_enemy' else hero_name
        
        status_type = effect_data.get('status_type', '')
        value = effect_data.get('value', 0.0)
        duration = effect_data.get('duration', 0)
        
        # 应用状态效果
        from battle.status_manager import StatusManager
        StatusManager.apply_status_effect(status_target, status_type, duration, target_display, 
                                       source=hero_name, amount=value)
        
        # 记录效果
        result['effects'].append({
            'type': 'status',
            'subtype': status_type,
            'value': value,
            'duration': duration,
            'target': target_display,
            'source': hero_name
        })
        
        print(f"{hero_name} 对 {target_display} 施加 {status_type} 状态效果，持续 {duration} 秒！")

    @staticmethod
    def _get_skill_value(hero, skill: Dict) -> float:
        """根据英雄等级获取技能数值"""
        level_values = skill.get('level_values', {})
        
        # 尝试从level_values字典中获取对应等级的数值
        if isinstance(level_values, dict):
            return level_values.get(hero.level, 0.2)
        
        # 如果level_values不是字典，使用默认值
        return 0.2
    
    @staticmethod
    def _process_eternal_night(hero, skill: Dict, target, result: Dict, hero_name: str, target_name: str) -> Dict:
        """处理永夜终焉特殊技能"""
        if DEBUG_MODE:
            print(f"DEBUG: 进入永夜终焉特殊技能处理")
        
        # 检查是否处于控制状态
        if hero.is_frozen or hero.is_stunned:
            control_type = "冰冻" if hero.is_frozen else "眩晕"
            print(f"{hero_name} 处于{control_type}状态，无法使用技能!")
            return {'success': False, 'message': f"处于{control_type}状态"}

        # 由于当前是1v1战斗，暂时只对目标生效
        if target:
            # 直接从level_values获取技能数值（避免_get_skill_value的问题）
            eternal_night_coefficient = skill.get('level_values', {}).get(hero.level, 0.2)
            
            # 计算真实伤害（基于目标最大生命值的百分比）
            true_damage = int(target.max_health * eternal_night_coefficient)
            # 应用真实伤害（无视防御，但优先消耗护盾）
            damage_after_shield = true_damage
            if target.shield_amount > 0:
                # 护盾吸收真实伤害
                shield_absorbed = min(true_damage, target.shield_amount)
                target.shield_amount -= shield_absorbed
                damage_after_shield = true_damage - shield_absorbed
                print(f"{target.name} 的护盾吸收了 {shield_absorbed} 点真实伤害!")
                if target.shield_amount == 0:
                    print(f"{target.name} 的护盾已被击破!")
            
            # 剩余伤害扣除生命值（使用标准伤害处理流程）
            if damage_after_shield > 0:
                damage_result = target.take_damage(damage_after_shield)
                
                # 检查是否有被动技能触发信息
                if damage_result.get('passive_triggered', False) and damage_result.get('triggered_passive') == 'unyielding_will':
                    print(f"🎉 {target_name} 触发不屈意志!")
                    result['effects'].append({
                        'type': 'passive_trigger',
                        'passive_name': 'unyielding_will',
                        'revive_health': damage_result.get('revive_health', 0),
                        'attack_boost_percent': int((damage_result.get('attack_boost_amount', 0) / (target.attack - damage_result.get('attack_boost_amount', 0))) * 100) if (target.attack - damage_result.get('attack_boost_amount', 0)) > 0 else 30
                    })
            
            # 70%概率触发冰冻效果
            if random.random() < 0.7:  # 70%概率
                # 移除现有的冰冻效果
                target.status_effects = [effect for effect in target.status_effects if effect['type'] != 'freeze']
                
                # 添加新的冰冻效果
                freeze_effect = {
                    'type': 'freeze',
                    'duration': 2
                }
                target.status_effects.append(freeze_effect)
                target.is_frozen = True  # 立即设置冰冻状态
                
                result['effects'].append({
                    'type': 'freeze',
                    'duration': 2,
                    'target': target_name
                })
                # 立即更新目标的状态
                target.is_frozen = True
            else:
                # 将抵抗信息添加到效果中，由战斗模拟器统一处理显示
                result['effects'].append({
                    'type': 'resist',
                    'skill_name': '永夜终焉',
                    'effect_type': 'freeze',
                    'target': target_name
                })
            
            # 将伤害信息添加到效果中，由战斗模拟器统一处理显示
            result['effects'].append({
                'type': 'true_damage',
                'damage': true_damage,
                'target': target_name
            })
        
        return result
    
    @staticmethod
    def _process_control_skill(hero, skill: Dict, target, skill_coefficient: float, result: Dict, hero_name: str, target_name: str) -> Dict:
        """处理控制类技能"""
        if DEBUG_MODE:
            print(f"DEBUG: 进入技能类型2处理，技能名称={skill['name']}, 描述={skill['description']}")
        
        # 检查被动技能类型
        # 如果是控制类（类型2）或BUFF类（类型3）的被动技能，让它生效
        damage_type = skill.get('damage_type', 0)  # 获取技能伤害类型
        
        # 处理可能的多个伤害类型（例如"1,2"或"2,3"）
        damage_types = []
        if isinstance(damage_type, str):
            # 如果是字符串，按逗号分隔并转换为整数列表
            damage_types = [int(dt.strip()) for dt in damage_type.split(',') if dt.strip().isdigit()]
        elif isinstance(damage_type, (int, float)):
            # 如果是数字，直接加入列表
            damage_types = [int(damage_type)]

        # 检查是否包含控制类(2)或BUFF类(3)
        if any(dt in [2, 3] for dt in damage_types):
            if DEBUG_MODE:
                print(f"DEBUG: 被动技能 {skill['name']} 包含控制类或BUFF类效果，将会生效")
            # 继续执行后续的技能效果逻辑
        else:
            # 其他类型的被动技能不生效
            print(f"    {hero_name} 被动技能: {skill['name']} 不产生战斗效果")
            return result
        
        if DEBUG_MODE:
            print(f"DEBUG: 进入控制类技能处理")
        # 控制技能 - 基于技能系数计算控制效果
        if target:
            # 默认控制效果：眩晕2秒
            control_duration = int(2 * skill_coefficient)
            result['effects'].append({
                'type': 'control',
                'subtype': 'stun',  # 控制子类型：眩晕
                'duration': control_duration,
                'target': target_name
            })
            print(f"{target_name} 被控制 {control_duration} 秒!")
        
        return result
    
    @staticmethod
    def _calculate_job_counter_damage(attacker_role: str, target_role: str, base_damage: int, attacker_rank: str = '', target_rank: str = '') -> int:
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
            attacker_role: 攻击者职业
            target_role: 目标职业
            base_damage: 基础伤害值
            attacker_rank: 攻击者稀有度（可选）
            target_rank: 目标稀有度（可选）
            
        Returns:
            应用职业克制和稀有度克制后的伤害值
        """
        damage = base_damage
        
        # 职业克制关系检查
        if attacker_role == 'DPS' and target_role == 'SNIP':
            damage = int(damage * 1.2)
            print(f"职业克制! DPS对SNIP造成额外20%伤害")
        elif attacker_role == 'SNIP' and target_role == 'TANK':
            damage = int(damage * 1.2)
            print(f"职业克制! SNIP对TANK造成额外20%伤害")
        elif attacker_role == 'TANK' and target_role == 'DPS':
            damage = int(damage * 1.2)
            print(f"职业克制! TANK对DPS造成额外20%伤害")
        elif attacker_role == 'TANK' and target_role == 'TANK':
            damage = int(damage * 1.5)
            print(f"TANK对TANK! 伤害加成50%")
        
        # 稀有度克制关系检查（需要提供稀有度信息）
        if attacker_rank and target_rank:
            if attacker_rank == 'SSR' and target_rank == 'SR':
                damage = int(damage * 1.5)
                print(f"稀有度克制! SSR对SR造成额外50%伤害")
            elif attacker_rank == 'SSR' and target_rank == 'R':
                damage = int(damage * 2.0)
                print(f"稀有度克制! SSR对R造成额外100%伤害")
            elif attacker_rank == 'SR' and target_rank == 'R':
                damage = int(damage * 1.5)
                print(f"稀有度克制! SR对R造成额外50%伤害")
        
        return damage

    @staticmethod
    def _process_damage_skill(hero, skill: Dict, target, skill_coefficient: float, result: Dict) -> Dict:
        """处理伤害类技能"""
        if DEBUG_MODE:
            print(f"DEBUG: 进入伤害类技能处理")
        # 攻击型技能 - 基于攻击力计算伤害
        if target:
            base_damage = hero.attack * skill_coefficient
            damage = int(base_damage)
            
            # 应用职业克制关系和稀有度克制关系
            damage = SkillProcessor._calculate_job_counter_damage(hero.role, target.role, damage, hero.rank, target.rank)
            
            if damage > 0:
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
                
                # 剩余伤害扣除生命值
                if damage_after_shield > 0:
                    target.health -= damage_after_shield
                    target.health = max(0, target.health)
                result['effects'].append({
                    'type': 'attack',
                    'damage': damage,
                    'is_crit': False  # 技能攻击默认不暴击
                })
        
        return result
    
    @staticmethod
    def _process_buff_skill(hero, skill: Dict, skill_coefficient: float, result: Dict, hero_name: str) -> Dict:
        """处理BUFF类技能"""
        if DEBUG_MODE:
            print(f"DEBUG: 进入BUFF类技能处理")
        # BUFF技能 - 基于技能系数计算增益效果
        skill_desc = skill['description'].lower()
        buff_type = 'attack_boost'  # 默认攻击提升
        buff_amount = 0
        
        if DEBUG_MODE:
            print(f"DEBUG: 处理BUFF类技能，技能类型={skill.get('skill_type', '')}, 技能描述={skill_desc}")
            print(f"DEBUG: 当前攻击力={hero.attack}, 技能系数={skill_coefficient}")
        
        if '防御' in skill_desc or '防御值' in skill_desc:
            buff_type = 'defense_boost'
            buff_amount = int(hero.defense * skill_coefficient)
            hero.defense += buff_amount
            if DEBUG_MODE:
                print(f"DEBUG: 防御提升 {buff_amount}, 新防御={hero.defense}")
        elif '暴击' in skill_desc or '概率' in skill_desc:
            buff_type = 'crit_boost'
            buff_amount = skill_coefficient
            hero.crit_rate += buff_amount
            if DEBUG_MODE:
                print(f"DEBUG: 暴击率提升 {buff_amount}, 新暴击率={hero.crit_rate}")
        else:
            # 默认攻击提升
            buff_type = 'attack_boost'
            buff_amount = int(hero.attack * skill_coefficient)
            hero.attack += buff_amount
            if DEBUG_MODE:
                print(f"DEBUG: 攻击力提升 {buff_amount}, 新攻击力={hero.attack}")
        
        result['effects'].append({
            'type': 'buff',
            'subtype': buff_type,
            'amount': buff_amount,
            'target': hero_name
        })
        
        return result
    
    @staticmethod
    def _process_default_attack(hero, target, result: Dict, hero_name: str, target_name: str) -> Dict:
        """处理默认攻击"""
        # 默认处理：普通攻击
        if target:
            damage = hero.attack_target(target)
            result['effects'].append({
                'type': 'attack',
                'damage': damage['damage'],
                'is_crit': damage['is_crit'],
                'target': target_name
            })
        
        return result

    @staticmethod
    def process_damage(base_damage: int, defense: int, crit_rate: float, crit_damage: float, target_level: int = 1) -> Dict:
        """
        处理伤害计算
        
        Args:
            base_damage: 基础伤害值
            defense: 防御力
            crit_rate: 暴击率
            crit_damage: 暴击伤害倍率
            target_level: 目标等级（默认1级）
            
        Returns:
            包含伤害计算结果的字典
        """
        # 从配置中获取防御参数
        from config import DAMAGE_FORMULA_PARAMS
        defense_param1 = DAMAGE_FORMULA_PARAMS['defense_param1']
        defense_param2 = DAMAGE_FORMULA_PARAMS['defense_param2']
        min_damage = DAMAGE_FORMULA_PARAMS['min_damage']
        
        # 计算防御减伤比例：1 - (防御力 / (防御力 + (等级 * 参数1 + 参数2)))
        defense_reduction = (defense / (defense + (target_level * defense_param1 + defense_param2)))
        
        # 暴击判断
        is_crit = random.random() < crit_rate
        
        if is_crit:
            # 暴击伤害公式: 基础伤害 * 暴击倍率 * (1 - 防御减伤比例)
            damage = int(base_damage * crit_damage * (1 - defense_reduction))
        else:
            # 普通伤害公式: 基础伤害 * (1 - 防御减伤比例)
            damage = int(base_damage * (1 - defense_reduction))
        
        # 最小伤害保护
        damage = max(min_damage, damage)
        
        return {
            'damage': damage,
            'is_crit': is_crit,
            'defense_reduction': defense_reduction
        }

    @staticmethod
    def process_heal(base_heal: int, heal_coefficient: float) -> Dict:
        """
        处理治疗计算
        
        Args:
            base_heal: 基础治疗值
            heal_coefficient: 治疗系数
            
        Returns:
            包含治疗计算结果的字典
        """
        heal_amount = int(base_heal * heal_coefficient)
        
        return {
            'heal_amount': heal_amount
        }

    @staticmethod
    def _process_skull_smash(hero, skill: Dict, target, result: Dict, hero_name: str, target_name: str) -> Dict:
        """处理碎颅猛击特殊技能
        
        技能效果：造成基于技能等级的基础伤害（1级1500点，2级2000点ATK伤害），
        并降低目标20%防御值，持续5秒
        """
        if DEBUG_MODE:
            print(f"DEBUG: 进入碎颅猛击特殊技能处理")
        
        # 检查是否处于控制状态
        if hero.is_frozen or hero.is_stunned:
            control_type = "冰冻" if hero.is_frozen else "眩晕"
            print(f"{hero_name} 处于{control_type}状态，无法使用技能!")
            return {'success': False, 'message': f"处于{control_type}状态"}

        # 由于当前是1v1战斗，暂时只对目标生效
        if target:
            # 获取技能等级，默认为1级
            skill_level = skill.get('level', 1)
            
            # 根据技能等级计算基础伤害
            base_damage = 300  # 1级基础伤害
            if skill_level >= 2:
                base_damage = 350  # 2级基础伤害
            if skill_level >= 3:
                base_damage = 400  # 3级基础伤害
            if skill_level >= 4:
                base_damage = 450  # 4级基础伤害
            if skill_level >= 5:
                base_damage = 500  # 5级基础伤害
            
            # 使用攻击公式计算实际伤害
            damage_result = SkillProcessor.process_damage(
                base_damage=base_damage,
                defense=target.defense,
                crit_rate=hero.crit_rate,
                crit_damage=hero.crit_damage,
                target_level=target.level
            )
            
            # 应用职业克制关系和稀有度克制关系
            damage_result['damage'] = SkillProcessor._calculate_job_counter_damage(
                hero.role, target.role, damage_result['damage'], hero.rank, target.rank
            )
            
            # 应用伤害（优先消耗护盾）
            damage_after_shield = damage_result['damage']
            if target.shield_amount > 0:
                # 护盾吸收伤害
                shield_absorbed = min(damage_result['damage'], target.shield_amount)
                target.shield_amount -= shield_absorbed
                damage_after_shield = damage_result['damage'] - shield_absorbed
                print(f"{target.name} 的护盾吸收了 {shield_absorbed} 点伤害!")
                if target.shield_amount == 0:
                    print(f"{target.name} 的护盾已被击破!")
            
            # 剩余伤害扣除生命值
            if damage_after_shield > 0:
                target.health -= damage_after_shield
                target.health = max(0, target.health)
            
            # 降低目标20%防御值，持续5秒
            armor_reduction = int(target.defense * 0.2)
            original_defense = target.defense
            target.defense -= armor_reduction
            target.defense = max(0, target.defense)
            
            # 添加防御值降低状态效果
            from battle.status_manager import StatusManager
            StatusManager.apply_status_effect(target, 'armor_reduction', 5, target_name, 
                                           source=hero_name, amount=armor_reduction, original_defense=original_defense)
            
            # 记录技能效果
            result['effects'].extend([
                {
                    'type': 'attack',
                    'damage': damage_result['damage'],
                    'is_crit': damage_result['is_crit'],
                    'target': target_name
                },
                {
                    'type': 'debuff',
                    'subtype': 'armor_reduction',
                    'amount': armor_reduction,
                    'duration': 5,
                    'target': target_name,
                    'source': hero_name
                }
            ])
            
            print(f"{hero_name} 使用碎颅猛击！")
            print(f"造成 {damage_result['damage']} 点伤害！")
            if damage_result['is_crit']:
                print("暴击！")
            print(f"{target_name} 防御值降低 {armor_reduction} 点，持续5秒！")
            print(f"{target_name} 当前防御值：{target.defense}")
        
        return result

    @staticmethod
    def _process_destruction_reforge(hero, skill: Dict, target, result: Dict, hero_name: str, target_name: str) -> Dict:
        """处理毁灭重铸特殊技能
        
        技能效果：牺牲当前30%生命值，对目标造成基于牺牲生命值的伤害，
        并强制嘲讽目标5秒
        伤害计算：
          1级：牺牲生命值的40%
          2级：牺牲生命值的50%
          3级：牺牲生命值的60%
          4级：牺牲生命值的70%
          5级：牺牲生命值的80%
        """
        if DEBUG_MODE:
            print(f"DEBUG: 进入毁灭重铸特殊技能处理")

        # 检查是否处于控制状态
        if hero.is_frozen or hero.is_stunned:
            control_type = "冰冻" if hero.is_frozen else "眩晕"
            print(f"{hero_name} 处于{control_type}状态，无法使用技能!")
            return {'success': False, 'message': f"处于{control_type}状态"}

        # 由于当前是1v1战斗，暂时只对目标生效
        if target:
            # 牺牲当前30%生命值
            sacrifice_amount = int(hero.health * 0.3)
            hero.health -= sacrifice_amount
            hero.health = max(1, hero.health)  # 至少保留1点生命值
            
            # 获取技能等级，默认为1级
            skill_level = skill.get('level', 1)
            
            # 根据技能等级计算伤害系数
            damage_coefficients = {1: 0.4, 2: 0.5, 3: 0.6, 4: 0.7, 5: 0.8}
            damage_coefficient = damage_coefficients.get(skill_level, 0.4)
            
            # 基于牺牲生命值计算伤害
            damage = int(sacrifice_amount * damage_coefficient)
            
            # 使用标准伤害处理流程（调用take_damage方法才能触发被动技能）
            damage_result = target.take_damage(damage, hero)
            
            # 检查是否触发了不屈意志被动
            if damage_result.get('passive_triggered', False) and damage_result.get('triggered_passive') == 'unyielding_will':
                print(f"{target.name} 的不屈意志触发! 复活并恢复{damage_result.get('revive_health', 0)}点生命值")
                
            # 更新伤害值为实际造成的伤害（考虑护盾吸收）
            actual_damage = damage_result.get('damage_after_shield', damage)
            if actual_damage < damage:
                print(f"{target.name} 的护盾吸收了 {damage - actual_damage} 点伤害!")
                if target.shield_amount == 0:
                    print(f"{target.name} 的护盾已被击破!")
            
            # 添加嘲讽效果（5秒）
            from battle.status_manager import StatusManager
            StatusManager.apply_status_effect(target, 'taunt', 5, target_name, source=hero_name)
            
            # 记录技能效果
            result['effects'].extend([
                {
                    'type': 'sacrifice',
                    'amount': sacrifice_amount,
                    'target': hero_name
                },
                {
                    'type': 'attack',
                    'damage': damage,
                    'target': target_name,
                    'is_crit': False,
                    'damage_coefficient': damage_coefficient,
                    'sacrifice_amount': sacrifice_amount
                },
                {
                    'type': 'control',
                    'subtype': 'taunt',
                    'duration': 5,
                    'target': target_name,
                    'source': hero_name
                }
            ])
            
            print(f"{hero_name} 牺牲了 {sacrifice_amount} 点生命值！")
            print(f"{target_name} 受到 {damage} 点伤害（{damage_coefficient*100}% {hero_name}牺牲生命值）！")
            print(f"{target_name} 被强制嘲讽 5 秒！")
        
        return result