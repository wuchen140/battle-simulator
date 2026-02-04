#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件配置系统模块
支持JSON配置文件管理插件配置
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from dataclasses import dataclass, asdict


@dataclass
class PluginConfig:
    """插件配置数据类"""
    enabled: bool = True
    priority: int = 50  # 优先级 (1-100)
    cooldown: int = 0    # 技能冷却时间
    config: Dict[str, Any] = None  # 插件特定配置
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class PluginConfigManager:
    """插件配置管理器"""
    
    def __init__(self, config_dir: str = "config/plugins"):
        self.config_dir = config_dir
        self.configs: Dict[str, PluginConfig] = {}
        self.logger = logging.getLogger(__name__)
        
        # 创建配置目录
        os.makedirs(config_dir, exist_ok=True)
    
    def load_config(self, plugin_name: str) -> Optional[PluginConfig]:
        """加载插件配置"""
        config_path = self._get_config_path(plugin_name)
        
        if not os.path.exists(config_path):
            # 如果配置文件不存在，创建默认配置
            default_config = PluginConfig()
            self.save_config(plugin_name, default_config)
            return default_config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            return PluginConfig(
                enabled=config_data.get('enabled', True),
                priority=config_data.get('priority', 50),
                cooldown=config_data.get('cooldown', 0),
                config=config_data.get('config', {})
            )
            
        except Exception as e:
            self.logger.error(f"加载插件配置失败 {plugin_name}: {e}")
            return None
    
    def save_config(self, plugin_name: str, config: PluginConfig) -> bool:
        """保存插件配置"""
        config_path = self._get_config_path(plugin_name)
        
        try:
            config_data = {
                'enabled': config.enabled,
                'priority': config.priority,
                'cooldown': config.cooldown,
                'config': config.config
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.configs[plugin_name] = config
            return True
            
        except Exception as e:
            self.logger.error(f"保存插件配置失败 {plugin_name}: {e}")
            return False
    
    def get_config(self, plugin_name: str) -> Optional[PluginConfig]:
        """获取插件配置"""
        if plugin_name in self.configs:
            return self.configs[plugin_name]
        
        config = self.load_config(plugin_name)
        if config:
            self.configs[plugin_name] = config
        
        return config
    
    def update_config(self, plugin_name: str, **kwargs) -> bool:
        """更新插件配置"""
        config = self.get_config(plugin_name)
        if not config:
            return False
        
        # 更新配置字段
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif key in config.config:
                config.config[key] = value
        
        return self.save_config(plugin_name, config)
    
    def get_all_configs(self) -> Dict[str, PluginConfig]:
        """获取所有插件配置"""
        config_files = [f for f in os.listdir(self.config_dir) 
                       if f.endswith('.json')]
        
        configs = {}
        for config_file in config_files:
            plugin_name = config_file[:-5]  # 移除 .json 后缀
            config = self.load_config(plugin_name)
            if config:
                configs[plugin_name] = config
        
        return configs
    
    def create_default_config(self, plugin_name: str, 
                             default_config: Optional[Dict[str, Any]] = None) -> bool:
        """创建默认配置"""
        if default_config is None:
            default_config = {}
        
        config = PluginConfig(
            enabled=True,
            priority=50,
            cooldown=0,
            config=default_config
        )
        
        return self.save_config(plugin_name, config)
    
    def _get_config_path(self, plugin_name: str) -> str:
        """获取配置文件路径"""
        return os.path.join(self.config_dir, f"{plugin_name}.json")


# 全局配置管理器实例
plugin_config_manager = PluginConfigManager()


# 配置工具函数
def config_to_dict(config: PluginConfig) -> Dict[str, Any]:
    """将配置对象转换为字典"""
    return asdict(config)


def dict_to_config(config_dict: Dict[str, Any]) -> PluginConfig:
    """将字典转换为配置对象"""
    return PluginConfig(**config_dict)