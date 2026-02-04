#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英雄对战模拟系统 - 主程序入口
基于Excel数据的英雄对战模拟器
"""

import sys
from typing import Dict, List, Optional
from data.data_loader import HeroDataLoader
from core.hero import Hero
from battle.simulator import BattleSimulator
from core.config_manager import config
from core.cache_manager import cache_manager


def main():
    """主函数"""
    print("英雄对战模拟系统启动...")
    
    # 配置验证
    if not config.validate_config():
        print("配置验证失败，请检查配置文件")
        return
    
    # 加载数据
    excel_path = config.excel_path
    heroes_data = HeroDataLoader.load_hero_data(excel_path)
    
    if not heroes_data:
        print("无法加载英雄数据，程序退出")
        return
    
    skills_data = HeroDataLoader.load_skills_data(excel_path)
    
    if not heroes_data:
        print("无法加载英雄数据，程序退出")
        return
    
    # 获取基础英雄列表
    base_heroes = HeroDataLoader.get_base_heroes(heroes_data)
    print(f"已加载 {len(base_heroes)} 个基础英雄，每个英雄有多个等级版本")
    
    print("\n可用基础英雄:")
    for i, hero_name in enumerate(base_heroes, 1):
        level_range = HeroDataLoader.get_hero_level_range(hero_name, heroes_data)
        print(f"{i}. {hero_name} (等级范围: {level_range['min']}-{level_range['max']})")
    
    while True:
        print("\n" + "=" * 50)
        print("1. 选择英雄和等级对战")
        print("2. 退出")
        
        choice = input("请选择操作 (1-2): ").strip()
        
        if choice == '1':
            # 选择英雄对战
            run_battle_mode(heroes_data, skills_data, base_heroes)
        elif choice == '2':
            print("感谢使用英雄对战模拟系统!")
            break
        else:
            print("无效选择，请重新输入")


def run_battle_mode(heroes_data: List[Dict], skills_data: List[Dict], base_heroes: List[str]):
    """运行对战模式"""
    print("\n=== 选择英雄对战 ===")
    
    # 选择第一个英雄
    print("\n选择第一个英雄:")
    hero1_data = select_hero(heroes_data, base_heroes, "第一个")
    if not hero1_data:
        return
    
    # 选择第二个英雄
    print("\n选择第二个英雄:")
    hero2_data = select_hero(heroes_data, base_heroes, "第二个")
    if not hero2_data:
        return
    
    # 创建英雄实例
    try:
        hero1 = Hero(hero1_data, skills_data)
        hero2 = Hero(hero2_data, skills_data)
        
        print(f"\n英雄创建成功!")
        print(f"玩家1: {hero1}")
        print(f"玩家2: {hero2}")
        
        # 显示英雄详细信息（包括职业）
        print(f"\n=== 英雄详细信息 ===")
        print(f"{hero1.name} - 职业: {hero1.role}, 等级: {hero1.level}, 品阶: {hero1.rank}")
        print(f"生命值: {hero1.health}/{hero1.max_health}, 攻击力: {hero1.attack}, 防御力: {hero1.defense}")
        print(f"暴击率: {hero1.crit_rate*100:.1f}%, 暴击伤害: {hero1.crit_damage}x, 速度: {hero1.speed}")
        
        print(f"\n{hero2.name} - 职业: {hero2.role}, 等级: {hero2.level}, 品阶: {hero2.rank}")
        print(f"生命值: {hero2.health}/{hero2.max_health}, 攻击力: {hero2.attack}, 防御力: {hero2.defense}")
        print(f"暴击率: {hero2.crit_rate*100:.1f}%, 暴击伤害: {hero2.crit_damage}x, 速度: {hero2.speed}")
        
        # 显示技能信息
        print(f"\n{hero1.name} 的技能:")
        for i, skill in enumerate(hero1.skills):
            print(f"  技能{i+1}: {skill['name']} (CD: {skill['cooldown']}回合)")
        
        print(f"\n{hero2.name} 的技能:")
        for i, skill in enumerate(hero2.skills):
            print(f"  技能{i+1}: {skill['name']} (CD: {skill['cooldown']}回合)")
        
        # 开始战斗
        input("\n按回车键开始战斗...")
        
        simulator = BattleSimulator()
        simulator.setup_battle(hero1, hero2)
        battle_result = simulator.run_battle()
        
        # 显示战斗结果
        print(f"\n=== 战斗结果 ===")
        print(f"胜利者: {battle_result['winner']}")
        print(f"战斗回合: {battle_result['turns']}")
        print(f"剩余生命: {battle_result['winner_health']}")
        
    except Exception as e:
        print(f"创建英雄失败: {e}")
        import traceback
        traceback.print_exc()


def select_hero(heroes_data: List[Dict], base_heroes: List[str], position: str) -> Optional[Dict]:
    """选择英雄"""
    print(f"\n{position}英雄选择:")
    for i, hero_name in enumerate(base_heroes, 1):
        level_range = HeroDataLoader.get_hero_level_range(hero_name, heroes_data)
        print(f"{i}. {hero_name} (等级范围: {level_range['min']}-{level_range['max']})")
    
    try:
        hero_choice = int(input("请选择英雄编号: ").strip())
        if hero_choice < 1 or hero_choice > len(base_heroes):
            print("无效的英雄选择")
            return None
        
        hero_name = base_heroes[hero_choice - 1]
        level_range = HeroDataLoader.get_hero_level_range(hero_name, heroes_data)
        
        level = int(input(f"选择 {hero_name} 的等级 ({level_range['min']}-{level_range['max']}): ").strip())
        if level < level_range['min'] or level > level_range['max']:
            print(f"等级必须在 {level_range['min']}-{level_range['max']} 之间")
            return None
        
        # 获取对应等级的英雄数据
        filtered_heroes = HeroDataLoader.filter_heroes_by_name_and_level(heroes_data, hero_name, level)
        if not filtered_heroes:
            print(f"找不到 {hero_name} 等级 {level} 的数据")
            return None
        
        return filtered_heroes[0]
        
    except ValueError:
        print("请输入有效的数字")
        return None
    except Exception as e:
        print(f"选择英雄时发生错误: {e}")
        return None


if __name__ == "__main__":
    main()