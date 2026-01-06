"""
MCP Server entry point - Unreal Project Analyzer.

提供统一的 Unreal 项目分析能力：
- 跨域搜索（C++/Blueprint/Asset）
- 继承层次分析
- 引用关系查询
- UE 模式检测

设计原则：最小工具集，最大能力覆盖。

配置（环境变量）：
- CPP_SOURCE_PATH: 项目 C++ 源码目录
- UNREAL_ENGINE_PATH: UE 引擎源码目录（可选）
- UE_PLUGIN_HOST: UE 插件 HTTP API Host
- UE_PLUGIN_PORT: UE 插件 HTTP API Port（默认 8080）
- DEFAULT_SEARCH_SCOPE: 默认搜索范围（project/engine/all）
"""

from __future__ import annotations

import argparse
import os
import sys

from fastmcp import FastMCP

from .config import get_config
from .tools import blueprint, cpp, cross_domain, unified

# Initialize MCP server
mcp = FastMCP(
    name="UnrealProjectAnalyzer",
    version="0.3.0",  # 精简工具集版本
)


def _is_ue_plugin_available() -> bool:
    """检查 UE 插件 HTTP API 是否可用。"""
    host = os.getenv("UE_PLUGIN_HOST")
    return host is not None and host.strip() != ""


def register_tools():
    """
    注册 MCP 工具。

    工具设计原则：最小困惑度，用最少工具达成最完整能力。

    **核心工具（4 个）**：
    - search: 统一搜索（C++/Blueprint/Asset）
    - get_hierarchy: 获取继承层次
    - get_references: 获取引用关系
    - get_details: 获取详细信息

    **特殊工具（5 个）**：
    - get_blueprint_graph: 获取蓝图节点图（unified 无法覆盖）
    - detect_ue_patterns: 检测 UPROPERTY/UFUNCTION 等 UE 模式
    - get_cpp_blueprint_exposure: 获取 C++ 暴露给蓝图的 API
    - trace_reference_chain: 跨域引用链追踪
    - find_cpp_class_usage: 查找 C++ 类在蓝图中的使用

    总计：9 个工具
    """

    ue_available = _is_ue_plugin_available()

    if not ue_available:
        print("[Unreal Analyzer] 警告：UE_PLUGIN_HOST 未配置。")
        print("  蓝图/资产相关功能不可用，仅 C++ 分析可用。")
        print("  设置 --ue-plugin-host 或 UE_PLUGIN_HOST 环境变量以启用全部功能。")
        print("")

    # ========================================================================
    # 核心工具（统一接口）
    # ========================================================================
    mcp.tool(description="统一搜索 C++/Blueprint/Asset（支持 scope: project/engine/all）")(
        unified.search
    )

    mcp.tool(description="获取继承层次（C++ 或 Blueprint）")(unified.get_hierarchy)

    mcp.tool(description="获取引用关系（出/入方向）")(unified.get_references)

    mcp.tool(description="获取详细信息（C++/Blueprint/Asset）")(unified.get_details)

    # ========================================================================
    # 特殊工具（unified 无法完全覆盖的能力）
    # ========================================================================

    # 蓝图节点图 - 需要专门的图结构返回
    if ue_available:
        mcp.tool(description="获取蓝图节点图（EventGraph、函数图）")(blueprint.get_blueprint_graph)

    # UE 模式检测 - 分析 UPROPERTY/UFUNCTION 等宏
    mcp.tool(description="检测 C++ 文件中的 UE 模式（UPROPERTY/UFUNCTION/UCLASS）")(
        cpp.detect_ue_patterns
    )

    # Blueprint 暴露分析 - 专门分析 C++ 到蓝图的接口
    mcp.tool(description="获取 C++ 文件中暴露给蓝图的 API 汇总")(cpp.get_cpp_blueprint_exposure)

    # 跨域引用链 - 需要递归追踪
    if ue_available:
        mcp.tool(description="跨域追踪完整引用链（Blueprint/Asset/C++）")(
            cross_domain.trace_reference_chain
        )

        mcp.tool(description="查找 C++ 类在蓝图/资产中的使用")(cross_domain.find_cpp_class_usage)

    # 打印摘要
    tool_count = 4 + 2  # 核心工具 + C++ 特殊工具
    if ue_available:
        tool_count += 3  # 蓝图节点图 + 跨域工具
        print(f"[Unreal Analyzer] 已注册 {tool_count} 个工具")
        print("  核心工具：search, get_hierarchy, get_references, get_details")
        print("  特殊工具：get_blueprint_graph, detect_ue_patterns,")
        print("           get_cpp_blueprint_exposure, trace_reference_chain,")
        print("           find_cpp_class_usage")
    else:
        print(f"[Unreal Analyzer] 已注册 {tool_count} 个工具（仅 C++ 模式）")
        print("  核心工具：search, get_hierarchy, get_references, get_details")
        print("  特殊工具：detect_ue_patterns, get_cpp_blueprint_exposure")


def initialize_from_environment():
    """从环境变量初始化分析器。"""
    import asyncio

    from .cpp_analyzer import get_analyzer

    cpp_source_path = os.getenv("CPP_SOURCE_PATH")
    unreal_engine_path = os.getenv("UNREAL_ENGINE_PATH")

    analyzer = get_analyzer()

    async def init():
        if cpp_source_path:
            try:
                await analyzer.initialize_custom_codebase(cpp_source_path)
                print(f"[Unreal Analyzer] 已加载项目源码：{cpp_source_path}")
                if unreal_engine_path:
                    await analyzer.initialize(unreal_engine_path)
                    print(f"[Unreal Analyzer] 已加载引擎源码：{unreal_engine_path}")
                return True
            except Exception as e:
                print(f"[Unreal Analyzer] 加载项目源码失败：{e}")

        if unreal_engine_path:
            try:
                await analyzer.initialize(unreal_engine_path)
                print(f"[Unreal Analyzer] 已加载引擎源码：{unreal_engine_path}")
                return True
            except Exception as e:
                print(f"[Unreal Analyzer] 加载引擎源码失败：{e}")

        print("[Unreal Analyzer] 警告：未配置 C++ 源码路径。")
        print("  设置 CPP_SOURCE_PATH 环境变量以启用 C++ 分析。")
        return False

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(init())
        else:
            loop.run_until_complete(init())
    except RuntimeError:
        asyncio.run(init())


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unreal-analyzer",
        description="Unreal Project Analyzer MCP Server",
    )

    parser.add_argument(
        "--cpp-source-path",
        help="项目 C++ 源码根目录",
        default=None,
    )
    parser.add_argument(
        "--unreal-engine-path",
        help="UE 引擎源码目录（可选）",
        default=None,
    )
    parser.add_argument(
        "--ue-plugin-host",
        help="UE 插件 HTTP API Host",
        default=None,
    )
    parser.add_argument(
        "--ue-plugin-port",
        type=int,
        help="UE 插件 HTTP API Port（默认 8080）",
        default=None,
    )
    parser.add_argument(
        "--default-scope",
        choices=["project", "engine", "all"],
        help="默认搜索范围",
        default=None,
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help="跳过启动时初始化",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="打印配置并退出",
    )

    # Transport 选项
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="MCP 传输方式（默认 stdio）",
    )
    parser.add_argument(
        "--mcp-host",
        default="127.0.0.1",
        help="HTTP/SSE 监听 Host（默认 127.0.0.1）",
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=8000,
        help="HTTP/SSE 监听 Port（默认 8000）",
    )
    parser.add_argument(
        "--mcp-path",
        default="/mcp",
        help="HTTP 路由前缀（默认 /mcp）",
    )

    return parser


def _apply_cli_overrides(args: argparse.Namespace) -> None:
    """将命令行参数覆盖到环境变量。"""
    if args.cpp_source_path:
        os.environ["CPP_SOURCE_PATH"] = args.cpp_source_path
    if args.unreal_engine_path:
        os.environ["UNREAL_ENGINE_PATH"] = args.unreal_engine_path
    if args.ue_plugin_host:
        os.environ["UE_PLUGIN_HOST"] = args.ue_plugin_host
    if args.ue_plugin_port is not None:
        os.environ["UE_PLUGIN_PORT"] = str(args.ue_plugin_port)
    if args.default_scope:
        os.environ["DEFAULT_SEARCH_SCOPE"] = args.default_scope


def main():
    """启动 MCP Server。"""
    parser = _build_arg_parser()
    args = parser.parse_args(sys.argv[1:])
    _apply_cli_overrides(args)

    if args.print_config:
        cfg = get_config()
        print("[Unreal Analyzer] 当前配置：")
        print(f"  CPP_SOURCE_PATH: {os.getenv('CPP_SOURCE_PATH')}")
        print(f"  UNREAL_ENGINE_PATH: {os.getenv('UNREAL_ENGINE_PATH')}")
        print(f"  UE_PLUGIN_URL: {cfg.ue_plugin_url}")
        print(f"  DEFAULT_SCOPE: {cfg.default_scope}")
        print(f"  项目路径: {cfg.get_project_paths()}")
        print(f"  引擎路径: {cfg.get_engine_paths()}")
        return

    register_tools()

    if not args.no_init:
        try:
            initialize_from_environment()
        except Exception as e:
            print(f"[Unreal Analyzer] 初始化错误：{e}")

    if args.transport == "stdio":
        mcp.run()
    elif args.transport == "http":
        mcp.run(transport="http", host=args.mcp_host, port=args.mcp_port, path=args.mcp_path)
    else:
        mcp.run(transport="sse", host=args.mcp_host, port=args.mcp_port)


if __name__ == "__main__":
    main()
