#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
战斗模拟器模块
处理战斗逻辑和回合管理
"""

import random
from typing import Dict, List, Optional
from core.hero import Hero


class BattleSimulator:
    """战斗模拟器"""
    
    def __init__(self):
        """初始化战斗模拟器"""
        self.hero1 = None
        self.hero2 = None
        self.current_turn = 0
        self.battle_log = []
        self.detailed_log = []  # 详细的战斗过程日志
    
    def setup_battle(self, hero1: Hero, hero2: Hero):
        """设置战斗双方"""
        self.hero1 = hero1
        self.hero2 = hero2
        self.current_turn = 0
        self.battle_log = []
        self.detailed_log = []
        
        # 为相同名称的英雄添加标识符
        hero1_display_name = hero1.name
        hero2_display_name = hero2.name
        
        if hero1.name == hero2.name:
            hero1_display_name = f"{hero1.name} (1)"
            hero2_display_name = f"{hero2.name} (2)"
        
        battle_start_msg = f"战斗开始: {hero1_display_name} (Lv.{hero1.level}) vs {hero2_display_name} (Lv.{hero2.level})"
        print(battle_start_msg)
        self.detailed_log.append(battle_start_msg)
        self.detailed_log.append("=" * 60)
    
    def run_battle(self, max_turns: int = 100) -> Dict:
        """运行战斗直到结束
        
        Args:
            max_turns: 最大回合数，默认100回合
        """
        if not self.hero1 or not self.hero2:
            return {'winner': None, 'turns': 0, 'log': []}
        
        # 战斗前重置技能冷却
        self.hero1.reset_cooldowns()
        self.hero2.reset_cooldowns()
        
        while self.hero1.is_alive() and self.hero2.is_alive():
            self.current_turn += 1
            turn_msg = f"\n=== 第 {self.current_turn} 回合 ==="
            print(turn_msg)
            self.detailed_log.append(turn_msg)
            
            # 回合开始时更新状态效果
            from battle.status_manager import StatusManager
            hero1_name = self._get_display_name(self.hero1)
            hero2_name = self._get_display_name(self.hero2)
            StatusManager.update_hero_status(self.hero1, hero1_name)
            StatusManager.update_hero_status(self.hero2, hero2_name)
            
            # 即时战斗模式：双方同时行动
            hero1_action = self._choose_action(self.hero1)
            hero2_action = self._choose_action(self.hero2)
            
            # 获取显示名称
            hero1_name = self._get_display_name(self.hero1)
            hero2_name = self._get_display_name(self.hero2)
            
            # 检查控制状态
            hero1_can_act = not (self.hero1.is_frozen or self.hero1.is_stunned)
            hero2_can_act = not (self.hero2.is_frozen or self.hero2.is_stunned)
            
            # 英雄1行动
            if hero1_can_act:
                self._process_hero_action(self.hero1, self.hero2, hero1_action, hero1_name, hero2_name)
            else:
                control_type = "冻结" if self.hero1.is_frozen else "眩晕"
                control_msg = f"{hero1_name} 处于{control_type}状态，无法行动!"
                print(control_msg)
                self.detailed_log.append(control_msg)
            
            # 英雄2行动
            if hero2_can_act:
                self._process_hero_action(self.hero2, self.hero1, hero2_action, hero2_name, hero1_name)
            else:
                control_type = "冻结" if self.hero2.is_frozen else "眩晕"
                control_msg = f"{hero2_name} 处于{control_type}状态，无法行动!"
                print(control_msg)
                self.detailed_log.append(control_msg)
            
            # 回合结束处理
            self._end_of_turn()
            
            # 检查是否达到最大回合数
            if self.current_turn >= max_turns:
                max_turns_msg = f"战斗达到最大回合数 {max_turns}，强制结束!"
                print(max_turns_msg)
                self.detailed_log.append(max_turns_msg)
                
                # 比较双方生命值，生命较少的一方生命值降为0
                if self.hero1.health < self.hero2.health:
                    self.hero1.health = 0
                    end_msg = f"{self._get_display_name(self.hero1)} 生命值较少，生命值降为0"
                elif self.hero2.health < self.hero1.health:
                    self.hero2.health = 0
                    end_msg = f"{self._get_display_name(self.hero2)} 生命值较少，生命值降为0"
                else:
                    # 生命值相同，随机选择一方
                    import random
                    if random.random() < 0.5:
                        self.hero1.health = 0
                        end_msg = f"双方生命值相同，随机选择 {self._get_display_name(self.hero1)} 生命值降为0"
                    else:
                        self.hero2.health = 0
                        end_msg = f"双方生命值相同，随机选择 {self._get_display_name(self.hero2)} 生命值降为0"
                
                print(end_msg)
                self.detailed_log.append(end_msg)
                break
        
        # 确定胜利者
        winner = self.hero1 if self.hero1.is_alive() else self.hero2
        loser = self.hero2 if self.hero1.is_alive() else self.hero1
        
        battle_end_msg = f"\n战斗结束! 胜利者: {winner.name}"
        turns_msg = f"战斗回合: {self.current_turn}"
        print(battle_end_msg)
        print(turns_msg)
        self.detailed_log.append(battle_end_msg)
        self.detailed_log.append(turns_msg)
        
        return {
            'winner': winner.name,
            'loser': loser.name,
            'turns': self.current_turn,
            'winner_health': winner.health,
            'log': self.battle_log,
            'detailed_log': self.detailed_log  # 返回详细战斗日志
        }
    

    
    def _get_display_name(self, hero: Hero) -> str:
        """获取带标识符的英雄显示名称"""
        if self.hero1 and self.hero2 and self.hero1.name == self.hero2.name:
            if hero is self.hero1:
                return f"{hero.name} (1)"
            elif hero is self.hero2:
                return f"{hero.name} (2)"
        return hero.name
    
    def _choose_action(self, hero: Hero) -> str:
        """选择行动类型"""
        # 简单AI：有可用技能时70%概率使用技能
        available_skills = [i for i, skill in enumerate(hero.skills) 
                          if skill['current_cooldown'] == 0]
        
        # 检查是否有可用的插件技能
        available_plugin_skills = hero.get_plugin_skills()
        
        # 如果有插件技能，增加使用技能的概率
        skill_probability = 0.7
        if available_plugin_skills:
            skill_probability = 0.8  # 有插件技能时80%概率使用技能
        
        if (available_skills or available_plugin_skills) and random.random() < skill_probability:
            return 'skill'
        return 'attack'
    
    def _process_hero_action(self, attacker: Hero, defender: Hero, action: str, attacker_name: str, defender_name: str):
        """处理英雄行动"""
        # 初始化默认结果
        result = {'success': True, 'message': '行动执行成功'}
        
        if action == 'skill':
            # 随机选择可用技能（包括插件技能）
            available_skills = [i for i, skill in enumerate(attacker.skills) 
                              if skill['current_cooldown'] == 0]
            available_plugin_skills = attacker.get_plugin_skills()
            
            # 决定使用普通技能还是插件技能
            use_plugin_skill = False
            if available_plugin_skills and random.random() < 0.4:  # 40%概率使用插件技能
                use_plugin_skill = True
            
            if use_plugin_skill and available_plugin_skills:
                # 使用插件技能
                skill_name = random.choice(available_plugin_skills)
                result = attacker.use_plugin_skill(skill_name, defender)
                
                if result['success']:
                    skill_use_msg = f"{attacker_name} 使用插件技能: {skill_name}"
                    print(skill_use_msg)
                    self.detailed_log.append(skill_use_msg)
                    
                    # 处理插件技能效果
                    if 'message' in result:
                        message_msg = f"  - {result['message']}"
                        print(message_msg)
                        self.detailed_log.append(message_msg)
                    
                    # 处理伤害效果
                    if 'damage' in result:
                        damage_msg = f"  - 造成 {result['damage']} 点伤害"
                        print(damage_msg)
                        self.detailed_log.append(damage_msg)
                    elif 'heal_amount' in result:
                        heal_msg = f"  - 恢复 {result['heal_amount']} 点生命值"
                        print(heal_msg)
                        self.detailed_log.append(heal_msg)
                    
                    # 处理额外效果
                    for effect in result.get('effects', []):
                        self._process_skill_effect(effect, attacker, defender, attacker_name, defender_name)
                else:
                    fail_msg = f"{attacker_name} 插件技能使用失败: {result['message']}"
                    print(fail_msg)
                    self.detailed_log.append(fail_msg)
                    
            elif available_skills:
                # 使用普通技能
                skill_index = random.choice(available_skills)
                result = attacker.use_skill(skill_index, defender)
                
                if result['success']:
                    skill_name = result['skill_name']
                    skill_use_msg = f"{attacker_name} 使用 {skill_name}"
                    print(skill_use_msg)
                    self.detailed_log.append(skill_use_msg)
                    
                    # 处理技能效果，传递显示名称
                    for effect in result.get('effects', []):
                        # 更新效果中的目标名称为显示名称
                        if 'target' in effect and effect['target'] == defender.name:
                            effect['target'] = defender_name
                        elif 'target' in effect and effect['target'] == attacker.name:
                            effect['target'] = attacker_name
                        self._process_skill_effect(effect, attacker, defender, attacker_name, defender_name)
                else:
                    fail_msg = f"{attacker_name} 技能使用失败: {result['message']}"
                    print(fail_msg)
                    self.detailed_log.append(fail_msg)
            else:
                # 所有技能都在冷却，使用普通攻击
                cooldown_msg = f"{attacker_name} 所有技能冷却中，使用普通攻击"
                print(cooldown_msg)
                self.detailed_log.append(cooldown_msg)
                damage_result = attacker.attack_target(defender)
                damage_msg = f"{attacker_name} 对 {defender_name} 造成 {damage_result['damage']} 点伤害"
                print(damage_msg)
                self.detailed_log.append(damage_msg)
                
                # 检查是否有被动技能触发信息
                if 'extra_effects' in damage_result:
                    for effect in damage_result['extra_effects']:
                        if effect.get('type') == 'passive_trigger' and effect.get('passive_name') == 'unyielding_will':
                            passive_msg = f"{defender_name} 的不屈意志触发! 复活并恢复{effect.get('revive_health', 0)}点生命值，攻击力提升{effect.get('attack_boost_percent', 30)}%持续10秒"
                            print(passive_msg)
                            self.detailed_log.append(passive_msg)
        else:
            # 普通攻击
            attack_msg = f"{attacker_name} 使用普通攻击"
            print(attack_msg)
            self.detailed_log.append(attack_msg)
            damage_result = attacker.attack_target(defender)
            damage_msg = f"{attacker_name} 对 {defender_name} 造成 {damage_result['damage']} 点伤害"
            print(damage_msg)
            self.detailed_log.append(damage_msg)
            
            # 检查是否有被动技能触发信息
            if 'extra_effects' in damage_result:
                for effect in damage_result['extra_effects']:
                    if effect.get('type') == 'passive_trigger' and effect.get('passive_name') == 'unyielding_will':
                        passive_msg = f"{defender_name} 的不屈意志触发! 复活并恢复{effect.get('revive_health', 0)}点生命值，攻击力提升{effect.get('attack_boost_percent', 30)}%持续10秒"
                        print(passive_msg)
                        self.detailed_log.append(passive_msg)
        
        # 显示目标状态
        status_msg = f"{defender_name} 剩余生命: {defender.health}/{defender.max_health}"
        print(status_msg)
        self.detailed_log.append(status_msg)
    
    def _process_skill_effect(self, effect: Dict, attacker: Hero, defender: Hero, attacker_name: str, defender_name: str):
        """处理技能效果"""
        from battle.status_manager import StatusManager
        
        effect_type = effect.get('type')
        
        if effect_type == 'attack':
            damage = effect.get('damage', 0)
            is_crit = effect.get('is_crit', False)
            crit_text = " (暴击!)" if is_crit else ""
            damage_msg = f"  - 造成 {damage} 点伤害{crit_text}"
            print(damage_msg)
            self.detailed_log.append(damage_msg)
            
        elif effect_type == 'true_damage':
            damage = effect.get('damage', 0)
            true_damage_msg = f"  - 造成 {damage} 点真实伤害（无视防御）"
            print(true_damage_msg)
            self.detailed_log.append(true_damage_msg)
            
        elif effect_type == 'control':
            subtype = effect.get('subtype', 'stun')
            duration = effect.get('duration', 2)
            target_name = effect.get('target', defender_name)
            
            target = defender if target_name == defender_name else attacker
            target_display_name = defender_name if target_name == defender_name else attacker_name
            StatusManager.apply_status_effect(target, subtype, duration, target_display_name)
            control_msg = f"  - {target_display_name} 被施加 {subtype} 效果，持续 {duration} 回合!"
            print(control_msg)
            self.detailed_log.append(control_msg)
            
        elif effect_type == 'freeze':
            duration = effect.get('duration', 2)
            target_name = effect.get('target', defender_name)
            
            target = defender if target_name == defender_name else attacker
            target_display_name = defender_name if target_name == defender_name else attacker_name
            StatusManager.apply_status_effect(target, 'freeze', duration, target_display_name)
            freeze_msg = f"  - {target_display_name} 被施加 freeze 效果，持续 {duration} 回合!"
            print(freeze_msg)
            self.detailed_log.append(freeze_msg)
            
        elif effect_type == 'buff':
            subtype = effect.get('subtype', 'attack_boost')
            amount = effect.get('amount', 0)
            target_name = effect.get('target', attacker_name)
            
            target = attacker if target_name == attacker_name else defender
            target_display_name = attacker_name if target_name == attacker_name else defender_name
            buff_msg = f"  - {target_display_name} 获得 {subtype} 效果，数值: {amount}"
            print(buff_msg)
            self.detailed_log.append(buff_msg)
            
        elif effect_type == 'resist':
            skill_name = effect.get('skill_name', '技能')
            effect_type = effect.get('effect_type', '效果')
            target_name = effect.get('target', defender_name)
            
            target_display_name = defender_name if target_name == defender_name else attacker_name
            resist_msg = f"  - {target_display_name} 抵抗了 {skill_name} 的 {effect_type} 效果!"
            print(resist_msg)
            self.detailed_log.append(resist_msg)
    
    def _end_of_turn(self):
        """回合结束处理"""
        turn_end_msg = f"=== 回合 {self.current_turn} 结束 ==="
        print(turn_end_msg)
        self.detailed_log.append(turn_end_msg)
        
        # 减少技能冷却
        for hero in [self.hero1, self.hero2]:
            for skill in hero.skills:
                if skill['current_cooldown'] > 0:
                    skill['current_cooldown'] -= 1
        
        # 处理状态效果
        from battle.status_manager import StatusManager
        for hero in [self.hero1, self.hero2]:
            active_effects = StatusManager.get_active_effects(hero.name)
            if active_effects:
                effects_msg = f"{hero.name} 的状态效果:"
                print(effects_msg)
                self.detailed_log.append(effects_msg)
                for effect in active_effects:
                    remaining = effect['duration'] - 1
                    if remaining > 0:
                        effect_msg = f"  - {effect['type']}: 剩余 {remaining} 回合"
                        print(effect_msg)
                        self.detailed_log.append(effect_msg)
                    else:
                        end_msg = f"  - {effect['type']}: 效果结束"
                        print(end_msg)
                        self.detailed_log.append(end_msg)
        
        # 记录回合状态
        self.battle_log.append({
            'turn': self.current_turn,
            'hero1_health': self.hero1.health,
            'hero2_health': self.hero2.health,
            'hero1_effects': StatusManager.get_active_effects(self.hero1.name),
            'hero2_effects': StatusManager.get_active_effects(self.hero2.name)
        })