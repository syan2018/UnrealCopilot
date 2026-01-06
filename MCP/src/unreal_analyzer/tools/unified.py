"""
Unified search tools.

These tools provide a grep-like unified interface for searching across
all code types: C++, Blueprint, and Assets with scope control.

Design goals:
- Minimize tool count for better AI understanding
- Provide consistent interface across code types
- Support scope-based filtering (project/engine)
"""

from __future__ import annotations

from typing import Literal

from ..cpp_analyzer import get_analyzer
from ..ue_client import get_client
from ..ue_client.http_client import UEPluginError

# Type aliases
ScopeType = Literal["project", "engine", "all"]
DomainType = Literal["cpp", "blueprint", "asset", "all"]


def _ue_error(tool: str, e: Exception) -> dict:
    """Return a friendly, structured error for UE Plugin connectivity issues."""
    return {
        "ok": False,
        "error": f"UE Plugin API 调用失败（{tool}）",
        "detail": str(e),
        "hint": "请确认 UE 编辑器已启动且启用了 UnrealProjectAnalyzer 插件。",
    }


async def search(
    query: str,
    domain: DomainType = "all",
    domains: list[Literal["cpp", "blueprint", "asset"]] | None = None,
    scope: ScopeType = "project",
    file_pattern: str = "*.{h,cpp}",
    asset_type: str = "",
    class_filter: str = "",
    max_results: int = 100,
    include_comments: bool = True,
    query_mode: Literal["smart", "regex", "tokens"] = "smart",
) -> dict:
    """
    Unified search across C++, Blueprint, and Asset domains.

    This is the primary search tool - think of it like grep for Unreal projects.
    It searches across different code types with consistent output format.

    Args:
        query: 搜索关键字（C++ 默认使用智能分词，Blueprint/Asset 使用通配符）
        domain: 搜索域 - "cpp", "blueprint", "asset", or "all"
        domains: 可选：显式指定多个域（例如 ["cpp","blueprint"]），优先级高于 domain
        scope: Where to search - "project" (default), "engine", or "all"
        file_pattern: For C++ search, file pattern (default: "*.{h,cpp}")
        asset_type: For asset search, filter by type (e.g., "Blueprint", "SkeletalMesh")
        class_filter: For blueprint search, filter by parent class
        max_results: Maximum results per domain (default: 100)
        include_comments: For C++ search, include comment lines
        query_mode: C++ 查询模式 - "smart"(默认), "regex", "tokens"

    Returns:
        Dictionary containing:
        - cpp_matches: C++ search results (if domain includes cpp)
        - blueprint_matches: Blueprint search results (if domain includes blueprint)
        - asset_matches: Asset search results (if domain includes asset)
        - total_count: Total matches across all domains
        - scope: The scope that was searched
        - domains_searched: List of domains that were searched

    Example:
        >>> # Search for "Health" in project C++ code only
        >>> await search("Health", domain="cpp", scope="project")

        >>> # Search for blueprints containing "Character"
        >>> await search("Character", domain="blueprint", class_filter="Pawn")

        >>> # Search everything everywhere
        >>> await search("Ability", domain="all", scope="all")
    """
    # Resolve domains to search.
    resolved_domains: list[Literal["cpp", "blueprint", "asset"]] = []
    if domains is not None:
        resolved_domains = [d for d in domains if d in ("cpp", "blueprint", "asset")]
    else:
        if domain == "all":
            resolved_domains = ["cpp", "blueprint", "asset"]
        elif domain in ("cpp", "blueprint", "asset"):
            resolved_domains = [domain]
        else:
            resolved_domains = ["cpp", "blueprint", "asset"]

    results = {
        "query": query,
        "scope": scope,
        "domains_searched": resolved_domains,
        "total_count": 0,
        "ok": True,
        "errors": [],
        "warnings": [],
        "tips": [],
        "query_mode": query_mode,
        "scope_meaning": {
            "project": "只搜索项目源码（默认，快）",
            "engine": "只搜索引擎源码",
            "all": "搜索项目 + 引擎（慢但全面）",
        },
    }

    # C++ search
    if "cpp" in resolved_domains:
        try:
            analyzer = get_analyzer()
            cpp_result = await analyzer.search_code(
                query,
                file_pattern,
                include_comments,
                scope=scope,
                max_results=max_results,
                query_mode=query_mode,
            )
            results["cpp_matches"] = cpp_result.get("matches", [])
            results["cpp_count"] = cpp_result.get("count", 0)
            results["cpp_truncated"] = cpp_result.get("truncated", False)
            results["cpp_searched_paths"] = cpp_result.get("searched_paths", [])
            results["cpp_query_mode_resolved"] = cpp_result.get("query_mode_resolved")
            results["total_count"] += results["cpp_count"]
        except Exception as e:
            results["cpp_matches"] = []
            results["cpp_count"] = 0
            results["cpp_error"] = str(e)
            results["ok"] = False
            results["errors"].append({"domain": "cpp", "error": str(e)})

    # Blueprint search (requires UE Plugin)
    if "blueprint" in resolved_domains:
        try:
            client = get_client()
            # Use query as pattern, apply scope filter
            params = {
                "pattern": query,
                "class": class_filter,
            }
            bp_result = await client.get("/blueprint/search", params)
            matches = bp_result.get("matches", [])

            # Apply scope filter (exclude engine paths for project scope)
            if scope == "project":
                matches = [m for m in matches if not m.get("path", "").startswith("/Script/")]
            elif scope == "engine":
                matches = [m for m in matches if m.get("path", "").startswith("/Script/")]

            # Limit results
            if len(matches) > max_results:
                matches = matches[:max_results]
                results["blueprint_truncated"] = True
            else:
                results["blueprint_truncated"] = False

            results["blueprint_matches"] = matches
            results["blueprint_count"] = len(matches)
            results["total_count"] += results["blueprint_count"]
        except UEPluginError as e:
            results["blueprint_matches"] = []
            results["blueprint_count"] = 0
            results["blueprint_error"] = str(e)
            results["ok"] = False
            results["errors"].append({"domain": "blueprint", "error": str(e)})
        except Exception as e:
            results["blueprint_matches"] = []
            results["blueprint_count"] = 0
            results["blueprint_error"] = f"Unexpected error: {e}"
            results["ok"] = False
            results["errors"].append({"domain": "blueprint", "error": str(e)})

    # Asset search (requires UE Plugin)
    if "asset" in resolved_domains:
        try:
            client = get_client()
            params = {
                "pattern": query,
                "type": asset_type,
            }
            asset_result = await client.get("/asset/search", params)
            matches = asset_result.get("matches", [])

            # Apply scope filter
            if scope == "project":
                matches = [
                    m
                    for m in matches
                    if not m.get("path", "").startswith("/Script/")
                    and not m.get("path", "").startswith("/Engine/")
                ]
            elif scope == "engine":
                matches = [
                    m
                    for m in matches
                    if m.get("path", "").startswith("/Script/")
                    or m.get("path", "").startswith("/Engine/")
                ]

            # Limit results
            if len(matches) > max_results:
                matches = matches[:max_results]
                results["asset_truncated"] = True
            else:
                results["asset_truncated"] = False

            results["asset_matches"] = matches
            results["asset_count"] = len(matches)
            results["total_count"] += results["asset_count"]
        except UEPluginError as e:
            results["asset_matches"] = []
            results["asset_count"] = 0
            results["asset_error"] = str(e)
            results["ok"] = False
            results["errors"].append({"domain": "asset", "error": str(e)})
        except Exception as e:
            results["asset_matches"] = []
            results["asset_count"] = 0
            results["asset_error"] = f"Unexpected error: {e}"
            results["ok"] = False
            results["errors"].append({"domain": "asset", "error": str(e)})

    # Add tips when nothing found.
    if results.get("total_count", 0) == 0:
        if (
            "cpp" in resolved_domains
            and query_mode in ("smart", "tokens")
            and any(ch.isspace() for ch in query)
        ):
            results["tips"].append(
                "C++ 搜索默认按空格分词并按命中度排序；建议先用更少关键词，"
                "如：LyraGameplayAbility / Damage / Execution"
            )
        if "blueprint" in resolved_domains or "asset" in resolved_domains:
            results["tips"].append(
                "Blueprint/Asset 搜索按名称通配符匹配；"
                "建议用更接近资源名的关键词（如 GA_, GE_, B_, BP_）"
            )

    return results


async def get_hierarchy(
    name: str,
    domain: Literal["cpp", "blueprint"] = "cpp",
    scope: ScopeType = "project",
    include_interfaces: bool = True,
) -> dict:
    """
    Get inheritance hierarchy for a class (C++ or Blueprint).

    Unified interface for getting class hierarchy across domains.

    Args:
        name: Class name (for C++) or blueprint path (for Blueprint)
        domain: "cpp" or "blueprint"
        scope: Search scope for C++ (project/engine/all)
        include_interfaces: Whether to include implemented interfaces

    Returns:
        Dictionary containing class hierarchy
    """
    if domain == "cpp":
        analyzer = get_analyzer()
        return await analyzer.find_class_hierarchy(name, include_interfaces, scope=scope)
    else:  # blueprint
        try:
            client = get_client()
            return await client.get("/blueprint/hierarchy", {"bp_path": name})
        except UEPluginError as e:
            return _ue_error("get_hierarchy", e)


async def get_references(
    path: str,
    domain: Literal["cpp", "blueprint", "asset"] = "asset",
    scope: ScopeType = "project",
    direction: Literal["outgoing", "incoming", "both"] = "both",
) -> dict:
    """
    Get references for an item (who it references and/or who references it).

    Unified interface for reference queries across domains.

    Args:
        path: Path or identifier (file path for C++, asset path for BP/Asset)
        domain: "cpp", "blueprint", or "asset"
        scope: Search scope for C++ (project/engine/all)
        direction: "outgoing" (what I reference), "incoming" (who references me), or "both"

    Returns:
        Dictionary containing references
    """
    results = {
        "path": path,
        "domain": domain,
        "direction": direction,
    }

    if domain == "cpp":
        # For C++, use identifier search
        analyzer = get_analyzer()
        if direction in ("incoming", "both"):
            refs = await analyzer.find_references(path, scope=scope)
            results["references"] = refs.get("matches", [])
            results["reference_count"] = refs.get("count", 0)
        results["ok"] = True
        return results

    # Blueprint/Asset use UE Plugin
    try:
        client = get_client()
        param_key = "bp_path" if domain == "blueprint" else "asset_path"

        if direction in ("outgoing", "both"):
            endpoint = f"/{domain}/references" if domain == "asset" else f"/{domain}/dependencies"
            out_result = await client.get(endpoint, {param_key: path})
            results["outgoing"] = out_result.get("dependencies", out_result.get("references", []))

        if direction in ("incoming", "both"):
            in_result = await client.get(f"/{domain}/referencers", {param_key: path})
            results["incoming"] = in_result.get("referencers", [])

        results["ok"] = True
        return results
    except UEPluginError as e:
        return _ue_error("get_references", e)


async def get_details(
    path: str,
    domain: Literal["cpp", "blueprint", "asset"] = "blueprint",
    scope: ScopeType = "project",
) -> dict:
    """
    Get detailed information about an item.

    Unified interface for getting details across domains.

    Args:
        path: Path or identifier (class name for C++, asset path for BP/Asset)
        domain: "cpp", "blueprint", or "asset"
        scope: Search scope for C++ (project/engine/all)

    Returns:
        Dictionary containing detailed information
    """
    if domain == "cpp":
        analyzer = get_analyzer()
        return await analyzer.analyze_class(path, scope=scope)

    try:
        client = get_client()
        if domain == "blueprint":
            return await client.get("/blueprint/details", {"bp_path": path})
        else:  # asset
            return await client.get("/asset/metadata", {"asset_path": path})
    except UEPluginError as e:
        return _ue_error("get_details", e)
