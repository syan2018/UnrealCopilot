"""
MCP Server entry point.

Provides unified access to:
- Blueprint analysis tools (via UE5 Plugin HTTP API)
- Asset reference tools (via UE5 Plugin HTTP API)
- C++ source analysis tools (built-in tree-sitter based)
- Cross-domain analysis tools

This server enables AI agents to comprehensively analyze UE5 projects,
tracing references across Blueprint ↔ C++ ↔ Asset boundaries.

Configuration (via environment variables):
- CPP_SOURCE_PATH: Path to project's C++ source directory (required for C++ analysis)
- UNREAL_ENGINE_PATH: Path to UE5 installation (optional, for engine source analysis)
- UE_PLUGIN_HOST: Host for UE5 Plugin HTTP API (default: localhost)
- UE_PLUGIN_PORT: Port for UE5 Plugin HTTP API (default: 8080)
"""

import os
from fastmcp import FastMCP

from .config import get_config
from .tools import blueprint, asset, cpp, cross_domain

# Initialize MCP server
mcp = FastMCP(
    name="UE5ProjectAnalyzer",
    version="0.1.0",
)


def register_tools():
    """
    Register all MCP tools.
    
    Tools are organized into groups focused on reference chain tracing:
    - Blueprint: Blueprint analysis via UE5 Plugin
    - Asset: Asset reference tracking via UE5 Plugin
    - C++: Source code analysis via tree-sitter
    - Cross-domain: Reference tracing across all domains
    """
    
    # ========================================================================
    # Blueprint Tools
    # ========================================================================
    # These communicate with the UE5 Plugin HTTP API
    
    mcp.tool(
        description="Search blueprints by name pattern and optional class filter"
    )(blueprint.search_blueprints)
    
    mcp.tool(
        description="Get the inheritance hierarchy of a blueprint"
    )(blueprint.get_blueprint_hierarchy)
    
    mcp.tool(
        description="Get all dependencies (referenced assets/classes) of a blueprint"
    )(blueprint.get_blueprint_dependencies)
    
    mcp.tool(
        description="Get all assets/blueprints that reference this blueprint"
    )(blueprint.get_blueprint_referencers)
    
    mcp.tool(
        description="Get the node graph of a blueprint function or event graph"
    )(blueprint.get_blueprint_graph)
    
    mcp.tool(
        description="Get comprehensive details about a blueprint (variables, functions, components)"
    )(blueprint.get_blueprint_details)
    
    # ========================================================================
    # Asset Tools
    # ========================================================================
    # These communicate with the UE5 Plugin HTTP API
    
    mcp.tool(
        description="Search assets by name pattern and optional type filter"
    )(asset.search_assets)
    
    mcp.tool(
        description="Get all assets that this asset references"
    )(asset.get_asset_references)
    
    mcp.tool(
        description="Get all assets that reference this asset"
    )(asset.get_asset_referencers)
    
    mcp.tool(
        description="Get metadata information about an asset"
    )(asset.get_asset_metadata)
    
    # ========================================================================
    # C++ Analysis Tools
    # ========================================================================
    # These use tree-sitter for local source analysis
    # All focused on understanding C++ ↔ Blueprint boundaries
    
    mcp.tool(
        description="Analyze a C++ class structure (methods, properties, inheritance)"
    )(cpp.analyze_cpp_class)
    
    mcp.tool(
        description="Get the complete inheritance hierarchy of a C++ class"
    )(cpp.get_cpp_class_hierarchy)
    
    mcp.tool(
        description="Search through C++ source code with regex support"
    )(cpp.search_cpp_code)
    
    mcp.tool(
        description="Find all references to a C++ identifier (class, function, variable)"
    )(cpp.find_cpp_references)
    
    mcp.tool(
        description="Detect UE patterns (UPROPERTY, UFUNCTION, UCLASS) that expose to Blueprints"
    )(cpp.detect_ue_patterns)
    
    mcp.tool(
        description="Get all Blueprint-exposed API from a C++ header file"
    )(cpp.get_cpp_blueprint_exposure)
    
    # ========================================================================
    # Cross-Domain Tools
    # ========================================================================
    # These coordinate between Blueprint, Asset, and C++ analysis
    
    mcp.tool(
        description="Trace a complete reference chain across Blueprint/Asset/C++ boundaries"
    )(cross_domain.trace_reference_chain)
    
    mcp.tool(
        description="Find all Blueprints and Assets that use a specific C++ class"
    )(cross_domain.find_cpp_class_usage)


def initialize_from_environment():
    """
    Initialize analyzer from environment variables.
    
    Environment variables:
    - CPP_SOURCE_PATH: Path to project's C++ source directory
    - UNREAL_ENGINE_PATH: Path to UE5 installation
    """
    from .cpp_analyzer import get_analyzer
    import asyncio
    
    cpp_source_path = os.getenv("CPP_SOURCE_PATH")
    unreal_engine_path = os.getenv("UNREAL_ENGINE_PATH")
    
    # Also check config
    config = get_config()
    
    analyzer = get_analyzer()
    
    async def init():
        # Priority: CPP_SOURCE_PATH > UNREAL_ENGINE_PATH
        if cpp_source_path:
            try:
                await analyzer.initialize_custom_codebase(cpp_source_path)
                print(f"[UE5 Analyzer] Initialized with C++ source path: {cpp_source_path}")
                return True
            except Exception as e:
                print(f"[UE5 Analyzer] Failed to initialize from CPP_SOURCE_PATH: {e}")
        
        if unreal_engine_path:
            try:
                await analyzer.initialize(unreal_engine_path)
                print(f"[UE5 Analyzer] Initialized with UE path: {unreal_engine_path}")
                return True
            except Exception as e:
                print(f"[UE5 Analyzer] Failed to initialize from UNREAL_ENGINE_PATH: {e}")
        
        print("[UE5 Analyzer] Warning: No C++ source path configured.")
        print("  Set CPP_SOURCE_PATH environment variable to enable C++ analysis.")
        return False
    
    # Run initialization
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop, create a task
            asyncio.create_task(init())
        else:
            loop.run_until_complete(init())
    except RuntimeError:
        # No event loop exists, create one
        asyncio.run(init())


def main():
    """Run the MCP server."""
    register_tools()
    
    # Initialize from environment
    try:
        initialize_from_environment()
    except Exception as e:
        print(f"[UE5 Analyzer] Initialization error: {e}")
    
    mcp.run()


if __name__ == "__main__":
    main()
