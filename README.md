# 英雄对战模拟系统

🎯 一个功能完整的英雄对战模拟系统，支持GUI界面、技能编辑、战斗模拟和数据分析。

## ✨ 功能特性

### 🎮 核心功能
- **英雄管理**: 完整的英雄数据管理和展示
- **技能系统**: 支持伤害类型选择（伤害/控制/BUFF/其他）
- **战斗模拟**: 实时战斗计算和结果分析
- **GUI界面**: 直观的可视化操作界面

### 🛠️ 技术特性
- **模块化设计**: 清晰的代码结构，易于维护和扩展
- **数据驱动**: Excel数据文件驱动，支持灵活配置
- **插件系统**: 可扩展的技能插件机制
- **缓存优化**: 智能缓存管理，提升性能

## 📁 项目结构

```
模拟战斗/
├── battle/           # 战斗系统模块
│   ├── simulator.py         # 战斗模拟器
│   ├── skill_processor.py  # 技能处理器
│   └── status_manager.py    # 状态管理器
├── config/           # 配置文件
│   ├── plugins/            # 技能插件配置
│   └── skill_chains/       # 技能链配置
├── core/             # 核心模块
│   ├── cache_manager.py    # 缓存管理
│   ├── config_manager.py   # 配置管理
│   ├── hero.py            # 英雄类
│   ├── plugin_manager.py   # 插件管理
│   └── skill_chain.py     # 技能链
├── data/             # 数据处理
│   ├── data_loader.py     # 数据加载器
│   └── data_validator.py  # 数据验证器
├── docs/             # 文档
│   └── skills/            # 技能文档
├── scripts/          # 工具脚本
│   └── build.py           # 打包脚本
├── tests/            # 测试文件
├── utils/            # 工具函数
├── main.py           # 命令行入口
├── main_gui.py       # GUI主界面
├── run_gui.py        # GUI启动脚本
├── config.py         # 全局配置
├── skill_manager.py  # 技能管理
├── visual_editor.py  # 可视化编辑器
├── requirements.txt  # 依赖配置
└── 英雄类数据1.xlsx  # 核心数据文件
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 依赖包: 见 `requirements.txt`

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动GUI
```bash
python run_gui.py
```

### 命令行模式
```bash
python main.py
```

## 🎯 使用指南

### 1. 英雄管理
- 查看所有英雄信息
- 编辑英雄属性
- 导入/导出英雄数据

### 2. 技能编辑
- 创建新技能
- 设置伤害类型（1-4对应不同类别）
- 配置技能等级效果

### 3. 战斗模拟
- 选择对战英雄
- 配置战斗参数
- 查看详细战斗日志

### 4. 数据分析
- 战斗结果统计
- 技能效果分析
- 性能优化建议

## 📦 打包分发

### 构建可执行文件
```bash
python scripts/build.py
```

### 生成文件
- `dist/HeroBattleSimulator` - 可执行文件
- `dist/HeroBattleSimulator.app` - macOS应用程序

## 🔧 开发指南

### 代码规范
- 遵循PEP8编码规范
- 使用类型提示
- 完整的文档字符串

### 测试
```bash
# 运行测试
pytest tests/

# 生成测试报告
pytest --cov=.  
```

### 代码检查
```bash
# 代码格式化
black .

# 语法检查
flake8 .

# 类型检查
mypy .
```

## 📊 数据格式

### 英雄数据格式
存储在 `英雄类数据1.xlsx` 中，包含：
- 英雄基本信息
- 技能配置
- 属性数值

### 技能配置
支持多种伤害类型：
- 1: 伤害类技能
- 2: 控制类技能  
- 3: BUFF类技能
- 4: 其他技能

## 🐛 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 使用清华镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 2. GUI启动失败
- 检查tkinter是否安装: `python -m tkinter`
- 确保数据文件存在

#### 3. 打包问题
- 确保PyInstaller已安装
- 检查文件路径是否正确

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 技术支持

- 提交Issue: [问题反馈](https://github.com/wuchen140/battle-simulator/issues)
- 文档: 查看 `docs/` 目录
- 邮箱: your-email@example.com

---

🎮 享受英雄对战的乐趣！
