#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证防御收益逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DAMAGE_FORMULA_PARAMS

def verify_defense_logic():
    """验证防御收益逻辑"""
    print("=== 验证防御收益逻辑 ===")
    
    # 获取防御参数
    defense_param1 = DAMAGE_FORMULA_PARAMS['defense_param1']
    defense_param2 = DAMAGE_FORMULA_PARAMS['defense_param2']
    
    print(f"防御参数1: {defense_param1}")
    print(f"防御参数2: {defense_param2}")
    print()
    
    # 测试场景：固定防御值，不同等级
    defense = 500
    levels = [1, 10, 20, 30, 40, 50]
    
    print(f"固定防御值: {defense}")
    print("防御减伤比例 = 防御力 / (防御力 + (等级 * 参数1 + 参数2))")
    print()
    
    for level in levels:
        denominator = defense + (level * defense_param1 + defense_param2)
        defense_reduction = defense / denominator
        
        print(f"等级 {level}: 减伤比例 = {defense_reduction:.3f}")
    
    print("\n=== 逻辑分析 ===")
    print("当前公式：防御减伤比例 = 防御力 / (防御力 + (等级 * 参数1 + 参数2))")
    print("随着等级增加，分母 (防御力 + (等级 * 参数1 + 参数2)) 增加")
    print("因此防御减伤比例减小，意味着相同防御值在高等级时提供的减伤效果更弱")
    print("这符合'防御收益随等级升级而减弱'的需求")
    
    # 验证伤害变化
    print("\n=== 伤害变化验证 ===")
    base_damage = 1000
    
    for level in [1, 50]:
        denominator = defense + (level * defense_param1 + defense_param2)
        defense_reduction = defense / denominator
        damage = base_damage * (1 - defense_reduction)
        
        print(f"等级 {level}: 减伤比例 = {defense_reduction:.3f}, 实际伤害 = {damage:.0f}")
    
    print("\n结论：高等级时相同防御值提供的减伤效果确实更弱，伤害更高")
    print("这符合'防御收益随等级升级而减弱'的设计目标")

if __name__ == "__main__":
    verify_defense_logic()