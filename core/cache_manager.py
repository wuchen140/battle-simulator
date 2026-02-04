#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据缓存管理器 - 提供数据预加载和缓存功能
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import time
from core.config_manager import config
import logging


class CacheManager:
    """数据缓存管理器（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """初始化缓存管理器"""
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._last_loaded: Dict[str, datetime] = {}
        
        # 默认缓存过期时间（秒）
        self.default_ttl = config.cache.default_ttl if hasattr(config.cache, 'default_ttl') else 300
        
        # 启动缓存清理线程
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired_cache, daemon=True)
        self._cleanup_thread.start()
        
        self.logger.info("缓存管理器初始化完成")
    
    def get(self, cache_key: str, data_type: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            cache_key: 缓存键
            data_type: 数据类型（'heroes', 'skills', 'hero_skills'）
            
        Returns:
            缓存数据或None
        """
        with self._cache_lock:
            if data_type in self._cache and cache_key in self._cache[data_type]:
                cached_data = self._cache[data_type][cache_key]
                
                # 检查是否过期
                if self._is_expired(data_type, cache_key):
                    self.logger.debug(f"缓存 {data_type}:{cache_key} 已过期")
                    self._remove(data_type, cache_key)
                    return None
                
                self.logger.debug(f"缓存命中 {data_type}:{cache_key}")
                return cached_data['data']
            
            self.logger.debug(f"缓存未命中 {data_type}:{cache_key}")
            return None
    
    def set(self, cache_key: str, data_type: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存数据
        
        Args:
            cache_key: 缓存键
            data_type: 数据类型
            data: 要缓存的数据
            ttl: 过期时间（秒），None使用默认值
        """
        with self._cache_lock:
            if data_type not in self._cache:
                self._cache[data_type] = {}
            
            expire_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            self._cache[data_type][cache_key] = {
                'data': data,
                'expire_time': expire_time,
                'created_at': datetime.now()
            }
            
            self.logger.debug(f"缓存设置 {data_type}:{cache_key}, 过期时间: {expire_time}")
    
    def preload_data(self, data_loader: Any) -> None:
        """
        预加载常用数据到缓存
        
        Args:
            data_loader: 数据加载器实例
        """
        self.logger.info("开始预加载数据到缓存")
        
        try:
            # 预加载英雄数据
            heroes_data = data_loader.load_hero_data(config.excel_path, validate=False)
            self.set('all_heroes', 'heroes', heroes_data, ttl=600)  # 10分钟
            
            # 预加载技能数据
            skills_data = data_loader.load_skills_data(config.excel_path, validate=False)
            self.set('all_skills', 'skills', skills_data, ttl=600)  # 10分钟
            
            # 预加载基础英雄列表
            base_heroes = data_loader.get_base_heroes(heroes_data)
            self.set('base_heroes', 'heroes', base_heroes, ttl=3600)  # 1小时
            
            self.logger.info(f"预加载完成: {len(heroes_data)}英雄, {len(skills_data)}技能, {len(base_heroes)}基础英雄")
            
        except Exception as e:
            self.logger.error(f"预加载数据失败: {e}")
    
    def get_cached_heroes(self) -> Optional[List[Dict]]:
        """获取缓存的英雄数据"""
        return self.get('all_heroes', 'heroes')
    
    def get_cached_skills(self) -> Optional[List[Dict]]:
        """获取缓存的技能数据"""
        return self.get('all_skills', 'skills')
    
    def get_cached_base_heroes(self) -> Optional[List[str]]:
        """获取缓存的基础英雄列表"""
        return self.get('base_heroes', 'heroes')
    
    def clear_cache(self, data_type: Optional[str] = None) -> None:
        """
        清除缓存
        
        Args:
            data_type: 要清除的数据类型，None表示清除所有
        """
        with self._cache_lock:
            if data_type is None:
                self._cache.clear()
                self.logger.info("清除所有缓存")
            elif data_type in self._cache:
                self._cache[data_type].clear()
                self.logger.info(f"清除 {data_type} 类型缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._cache_lock:
            stats = {
                'total_items': 0,
                'by_type': {},
                'memory_usage_estimate': 0  # 简化的内存使用估计
            }
            
            for data_type, cache_data in self._cache.items():
                stats['by_type'][data_type] = len(cache_data)
                stats['total_items'] += len(cache_data)
                
                # 粗略估计内存使用（假设每个缓存项约1KB）
                stats['memory_usage_estimate'] += len(cache_data) * 1024
            
            return stats
    
    def _is_expired(self, data_type: str, cache_key: str) -> bool:
        """检查缓存是否过期"""
        if data_type in self._cache and cache_key in self._cache[data_type]:
            cached_item = self._cache[data_type][cache_key]
            return datetime.now() > cached_item['expire_time']
        return True
    
    def _remove(self, data_type: str, cache_key: str) -> None:
        """移除缓存项"""
        if data_type in self._cache and cache_key in self._cache[data_type]:
            del self._cache[data_type][cache_key]
    
    def _cleanup_expired_cache(self) -> None:
        """清理过期缓存的线程函数"""
        while self._running:
            try:
                time.sleep(60)  # 每分钟检查一次
                
                with self._cache_lock:
                    expired_count = 0
                    for data_type in list(self._cache.keys()):
                        for cache_key in list(self._cache[data_type].keys()):
                            if self._is_expired(data_type, cache_key):
                                self._remove(data_type, cache_key)
                                expired_count += 1
                    
                    if expired_count > 0:
                        self.logger.debug(f"清理了 {expired_count} 个过期缓存项")
                        
            except Exception as e:
                self.logger.error(f"缓存清理线程错误: {e}")
    
    def shutdown(self) -> None:
        """关闭缓存管理器"""
        self._running = False
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        self.logger.info("缓存管理器已关闭")


# 全局缓存实例
cache_manager = CacheManager()