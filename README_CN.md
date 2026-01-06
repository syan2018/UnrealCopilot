# Unreal Project Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

用于分析 Unreal Engine 5 项目的 MCP 服务器 - 支持蓝图、资产和 C++ 源码分析。

> **目标**：让 AI 能够完整理解 Unreal 项目，跨越 Blueprint ↔ C++ ↔ Asset 边界追踪引用链。

**[English](README.md)**

## 特性

- **蓝图分析**：继承层次、依赖关系、节点图、变量、组件
- **资产引用追踪**：查找资产的依赖和被引用关系
- **C++ 源码分析**：类结构、UPROPERTY/UFUNCTION 检测（基于 tree-sitter）
- **跨域查询**：跨所有领域追踪完整引用链
- **编辑器集成**：直接从 Unreal Editor 菜单启动/停止 MCP 服务器
- **搜索范围控制 (v0.2.0)**：支持只搜索项目代码、引擎代码或全部
- **统一搜索 (v0.2.0)**：类似 grep 的跨域统一搜索接口

## v0.3.0 新特性

- **最小工具集**：从 22 个精简到 **9 个工具**（4 核心 + 5 特殊）
- **统一接口**：`search`、`get_hierarchy`、`get_references`、`get_details`
- **三层搜索**：`scope` 参数支持 `project`/`engine`/`all`
- **健康检查**：`/health` 端点验证 UE 插件状态

## 快速开始（推荐方式）

### 前置要求

- **Unreal Engine 5.3+**
- **[uv](https://docs.astral.sh/uv/)** - Python 包管理器（必需）

### 1. 安装插件

将 `UnrealProjectAnalyzer` 文件夹复制到你的 Unreal 项目的 `Plugins/` 目录：

```
YourProject/
├── Plugins/
│   └── UnrealProjectAnalyzer/    ← 这个文件夹
│       ├── Source/
│       ├── Mcp/
│       └── UnrealProjectAnalyzer.uplugin
```

### 2. 配置 uv 路径

1. 打开 Unreal Editor
2. 进入 **Edit → Project Settings → Plugins → Unreal Project Analyzer**
3. 设置 **Uv Executable** 为你的 uv 安装路径，例如：
   - Windows: `C:\Users\你的用户名\.local\bin\uv.exe` 或 `C:\Users\你的用户名\anaconda3\Scripts\uv.exe`
   - macOS/Linux: `/usr/local/bin/uv` 或 `~/.local/bin/uv`

**如何找到 uv 路径？**
```powershell
# Windows PowerShell
Get-Command uv | Select-Object -ExpandProperty Source

# macOS/Linux
which uv
```

### 3. 启动 MCP 服务器

1. 在 Unreal Editor 菜单：**Tools → Unreal Project Analyzer → Start MCP Server**
2. 检查 Output Log 是否显示：`LogMcpServer: MCP Server process started`
3. 通过 **Tools → Unreal Project Analyzer → Copy MCP URL** 复制 MCP 地址

### 4. 连接 Cursor

在 Cursor 的 MCP 设置中添加（使用复制的 URL）：

```json
{
  "mcpServers": {
    "unreal-project-analyzer": {
      "url": "http://127.0.0.1:19840/mcp"
    }
  }
}
```

## 替代方案：手动运行 MCP 服务器

如果你更喜欢在 Unreal Editor 外部运行 MCP 服务器：

```bash
cd /path/to/UnrealProjectAnalyzer

# 安装依赖
uv sync

# 以 stdio 方式运行（用于 Cursor MCP 集成）
uv run unreal-analyzer -- \
  --cpp-source-path "/path/to/YourProject/Source" \
  --unreal-engine-path "/path/to/UE_5.3/Engine/Source" \
  --ue-plugin-host "localhost" \
  --ue-plugin-port 8080 \
  --default-scope project

# 或以 HTTP 服务器方式运行（便于快速连接）
uv run unreal-analyzer -- \
  --transport http \
  --mcp-host 127.0.0.1 \
  --mcp-port 19840 \
  --cpp-source-path "/path/to/YourProject/Source"
```

## 架构

```
┌──────────────────────────────────────────────────────────────────┐
│                       AI Agent (Cursor)                          │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ MCP Protocol
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                  MCP Server (Python/FastMCP)                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │            C++ 源码分析器 (tree-sitter)                     │  │
│  │            支持: project / engine / all                     │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ HTTP
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│            UnrealProjectAnalyzer 插件 (Editor 内运行)             │
│  ┌─────────────────────────┐  ┌────────────────────────────────┐ │
│  │   HTTP Server (:8080)   │  │   MCP 启动器 (uv 进程)          │ │
│  │   蓝图/资产 API          │  │   从 Editor 自动启动            │ │
│  │   /health 健康检查       │  │                                │ │
│  └─────────────────────────┘  └────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## 搜索范围 (v0.2.0)

所有 C++ 分析工具都支持 `scope` 参数：

| 范围 | 描述 | 使用场景 |
|------|------|----------|
| `project` | 只搜索项目源码（默认） | 快速、聚焦的搜索 |
| `engine` | 只搜索引擎源码 | 理解 UE 内部实现 |
| `all` | 搜索项目和引擎 | 全面分析 |

示例：
```python
# 只搜索项目代码（快）
await search_cpp_code("Health", scope="project")

# 只搜索引擎代码
await analyze_cpp_class("ACharacter", scope="engine")

# 搜索所有代码（较慢但全面）
await find_cpp_references("UAbilitySystemComponent", scope="all")
```

## 可用工具（共 9 个）

### 核心工具（4 个）

| 工具 | 描述 |
|------|------|
| `search` | 统一搜索 C++/蓝图/资产 |
| `get_hierarchy` | 获取继承层次（C++ 或蓝图） |
| `get_references` | 获取引用关系（出/入方向） |
| `get_details` | 获取详细信息（C++/蓝图/资产） |

### 特殊工具（5 个）

| 工具 | 描述 | 为什么需要 |
|------|------|------------|
| `get_blueprint_graph` | 获取蓝图节点图 | 需要图结构返回 |
| `detect_ue_patterns` | 检测 UPROPERTY/UFUNCTION | UE 宏分析 |
| `get_cpp_blueprint_exposure` | 获取 C++ 暴露给蓝图的 API | C++→BP 接口汇总 |
| `trace_reference_chain` | 跨域引用链追踪 | 递归深度遍历 |
| `find_cpp_class_usage` | 查找 C++ 类使用 | BP 中的 C++ 类查找 |

## 插件设置

| 设置 | 描述 | 默认值 |
|------|------|--------|
| `Auto Start MCP Server` | Editor 启动时自动启动 MCP | `false` |
| `Uv Executable` | uv 可执行文件路径 | `uv` |
| `Capture Server Output` | 将 MCP 输出打印到 UE Log | `true` |
| `Transport` | MCP 传输模式 | `http` |
| `MCP Port` | HTTP/SSE 监听端口 | `19840` |
| `Cpp Source Path` | 项目 C++ 源码根目录 | 自动检测 |
| `Unreal Engine Source Path` | 引擎源码路径（用于分析引擎类） | 自动检测 |

## 使用示例

### 使用统一搜索

```python
# 跨域搜索 "Health"
result = await search(
    query="Health",
    domain="all",      # "cpp", "blueprint", "asset", "all"
    scope="project",   # "project", "engine", "all"
    max_results=100
)

# 获取 C++ 类的继承层次
hierarchy = await get_hierarchy(
    name="ACharacter", 
    domain="cpp", 
    scope="engine"
)
```

### 追踪 GAS 能力

```
用户: 帮我追踪 GA_Hero_Dash 这个能力是怎么触发和执行的

AI Agent:
[使用 search, get_hierarchy, get_blueprint_graph...]

GA_Hero_Dash 完整流程：

触发路径：
玩家按下 Shift → IA_Dash → IC_Default_KBM 
  → ULyraHeroComponent::Input_AbilityInputTagPressed()
  → ULyraAbilitySystemComponent::TryActivateAbility(Ability.Dash)

执行逻辑 (EventGraph):
1. ActivateAbility → IsLocallyControlled?
2. SelectDirectionalMontage → Set Direction
3. CommitAbility → PlayMontageAndWait
4. ApplyRootMotionConstantForce
5. Delay → EndAbility

关联资产：
- GE_HeroDash_Cooldown (GameplayEffect)
- Dash_Fwd/Bwd/Left/Right Montages
```

### 查找资产引用

```
用户: B_Hero_Default 被哪些地方引用了？

AI Agent:
[使用 get_references, trace_reference_chain...]

B_Hero_Default 引用情况：

直接引用者:
├─ B_Hero_ShooterMannequin (蓝图)
├─ B_Hero_Explorer (蓝图)
├─ DA_HeroData_Default (数据资产)
└─ ... (共 8 个资产)

间接引用者 (通过 Experience):
├─ B_LyraDefaultExperience
├─ B_ShooterGame_Elimination
└─ ...
```

## 健康检查

验证 UE 插件是否运行：

```bash
curl http://localhost:8080/health
```

返回：
```json
{
  "ok": true,
  "status": "running",
  "plugin": "UnrealProjectAnalyzer",
  "version": "0.2.0",
  "ue_version": "5.3.2-xxx",
  "project_name": "LyraStarterGame"
}
```

## 常见问题

### MCP 服务器启动失败

1. **检查 uv 路径**：确保在设置中填写了正确的 uv 完整路径
2. **检查端口冲突**：默认端口 19840，如有冲突可在设置中修改
3. **查看日志**：Output Log 中搜索 `LogMcpServer` 查看详细错误

### 连接 Cursor 失败

1. **确认 MCP 服务器已启动**：检查 Output Log 中的启动日志
2. **检查 URL**：使用 Copy MCP URL 功能获取正确地址
3. **防火墙**：确保本地端口未被防火墙阻止

## 开发

```bash
# 安装开发依赖
uv sync --all-extras

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .

# 打印配置（调试用）
uv run unreal-analyzer --print-config
```

## 致谢

本项目参考了以下优秀项目的实现方案：

- **[unreal-analyzer-mcp](https://github.com/ayeletstudioindia/unreal-analyzer-mcp)** - C++ 源码分析方案（tree-sitter）
- **[ue5-mcp](https://github.com/cutehusky/ue5-mcp)** - Unreal Editor HTTP API 暴露方案

## 许可证

MIT
