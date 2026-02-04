#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件管理器模块 - 支持插件式技能系统
"""

from typing import Dict, List, Optional, Callable, Any, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
import importlib
import inspect
import os
import glob
from pathlib import Path
import logging
from .plugin_config import plugin_config_manager, PluginConfig


@dataclass
class PluginInfo:
    """插件信息数据类"""
    name: str
    version: str
    author: str
    description: str
    plugin_class: Type
    enabled: bool = True
    config: Optional[PluginConfig] = None  # 插件配置


class SkillPlugin(ABC):
    """技能插件基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def get_skill_name(self) -> str:
        """获取技能名称"""
        pass
    
    @abstractmethod
    def get_skill_description(self) -> str:
        """获取技能描述"""
        pass
    
    @abstractmethod
    def get_skill_type(self) -> str:
        """获取技能类型"""
        pass
    
    @abstractmethod
    def execute(self, caster: Any, target: Optional[Any] = None, 
               **kwargs) -> Dict[str, Any]:
        """执行技能效果"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证插件配置"""
        return True
    
    def on_enable(self):
        """插件启用时调用"""
        self.logger.info(f"插件 {self.get_skill_name()} 已启用")
    
    def on_disable(self):
        """插件禁用时调用"""
        self.logger.info(f"插件 {self.get_skill_name()} 已禁用")


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_plugins: Dict[str, SkillPlugin] = {}
        self.logger = logging.getLogger(__name__)
        
        # 创建插件目录（如果不存在）
        os.makedirs(plugins_dir, exist_ok=True)
    
    def discover_plugins(self) -> List[PluginInfo]:
        """发现可用插件"""
        plugin_files = glob.glob(os.path.join(self.plugins_dir, "*.py"))
        discovered_plugins = []
        
        for plugin_file in plugin_files:
            try:
                plugin_info = self._load_plugin_info(plugin_file)
                if plugin_info:
                    discovered_plugins.append(plugin_info)
                    self.plugins[plugin_info.name] = plugin_info
            except Exception as e:
                self.logger.error(f"加载插件 {plugin_file} 失败: {e}")
        
        return discovered_plugins
    
    def _load_plugin_info(self, plugin_file: str) -> Optional[PluginInfo]:
        """加载插件信息"""
        try:
            module_name = Path(plugin_file).stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, SkillPlugin) and 
                    obj != SkillPlugin):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                return None
            
            # 使用第一个找到的插件类
            plugin_class = plugin_classes[0]
            plugin_instance = plugin_class()
            
            # 加载插件配置
            plugin_name = plugin_instance.get_skill_name()
            config = plugin_config_manager.get_config(plugin_name)
            
            return PluginInfo(
                name=plugin_name,
                version=getattr(module, '__version__', '1.0.0'),
                author=getattr(module, '__author__', '未知'),
                description=plugin_instance.get_skill_description(),
                plugin_class=plugin_class,
                config=config
            )
            
        except Exception as e:
            self.logger.error(f"解析插件信息失败 {plugin_file}: {e}")
            return None
    
    def load_plugin(self, plugin_name: str) -> Optional[SkillPlugin]:
        """加载插件实例"""
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]
        
        if plugin_name not in self.plugins:
            self.logger.error(f"插件 {plugin_name} 未发现")
            return None
        
        try:
            plugin_info = self.plugins[plugin_name]
            plugin_instance = plugin_info.plugin_class()
            self.loaded_plugins[plugin_name] = plugin_instance
            plugin_instance.on_enable()
            
            self.logger.info(f"插件 {plugin_name} 加载成功")
            return plugin_instance
            
        except Exception as e:
            self.logger.error(f"加载插件实例失败 {plugin_name}: {e}")
            return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name in self.loaded_plugins:
            try:
                plugin_instance = self.loaded_plugins[plugin_name]
                plugin_instance.on_disable()
                del self.loaded_plugins[plugin_name]
                self.logger.info(f"插件 {plugin_name} 已卸载")
                return True
            except Exception as e:
                self.logger.error(f"卸载插件失败 {plugin_name}: {e}")
                return False
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[SkillPlugin]:
        """获取已加载的插件"""
        return self.loaded_plugins.get(plugin_name)

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        plugin_info = self.plugins.get(plugin_name)
        if plugin_info and plugin_info.config is None:
            # 如果配置未加载，重新加载配置
            plugin_info.config = plugin_config_manager.get_config(plugin_name)
        return plugin_info
    
    def get_all_plugins(self) -> List[PluginInfo]:
        """获取所有插件信息"""
        return list(self.plugins.values())
    
    def get_loaded_plugins(self) -> List[str]:
        """获取已加载的插件列表"""
        return list(self.loaded_plugins.keys())
    
    def execute_skill(self, plugin_name: str, caster: Any, 
                     target: Optional[Any] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """执行插件技能"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            plugin = self.load_plugin(plugin_name)
        
        if plugin:
            try:
                return plugin.execute(caster, target, **kwargs)
            except Exception as e:
                self.logger.error(f"执行技能 {plugin_name} 失败: {e}")
                return None
        
        return None
    
    def reload_plugins(self) -> List[PluginInfo]:
        """重新加载所有插件"""
        # 先卸载所有已加载的插件
        for plugin_name in list(self.loaded_plugins.keys()):
            self.unload_plugin(plugin_name)
        
        # 清空插件信息
        self.plugins.clear()
        
        # 重新发现插件
        return self.discover_plugins()


# 示例插件：寒冰箭
class FrostArrowPlugin(SkillPlugin):
    """寒冰箭插件 - 造成冰系伤害并减速目标"""
    
    def get_skill_name(self) -> str:
        return "寒冰箭"
    
    def get_skill_description(self) -> str:
        return "发射一支寒冰箭，造成冰系伤害并使目标减速"
    
    def get_skill_type(self) -> str:
        return "冰系魔法"
    
    def execute(self, caster: Any, target: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        """执行寒冰箭技能"""
        base_damage = kwargs.get('base_damage', 100)
        slow_duration = kwargs.get('slow_duration', 3)
        
        # 计算伤害（这里使用简单的伤害计算）
        damage = base_damage
        
        # 应用伤害
        if target:
            target.health -= damage
            target.health = max(0, target.health)
        
        return {
            'success': True,
            'damage': damage,
            'effects': [
                {
                    'type': 'slow',
                    'duration': slow_duration,
                    'target': target.name if target else '未知',
                    'message': f"{target.name if target else '目标'} 被减速 {slow_duration} 回合"
                }
            ],
            'message': f"{caster.name} 施展寒冰箭，造成 {damage} 点伤害"
        }


# 全局插件管理器实例
plugin_manager = PluginManager()