"""
UnrealProjectAnalyzer MCP Server initialization script.

This script initializes the MCP server inside Unreal Engine's Python environment.
It sets up the bridge between C++ and Python, and starts the analyzer server.
"""

import sys
import os
from pathlib import Path
import site

_python_dir = Path(__file__).parent
_venv_site_packages_dir = _python_dir / ".venv" / "Lib" / "site-packages"

# Add uv-managed venv site-packages first (higher priority for dependencies).
if _venv_site_packages_dir.exists():
    try:
        # Important: process .pth files too (e.g. pywin32 on Windows)
        site.addsitedir(str(_venv_site_packages_dir))
    except Exception:
        if str(_venv_site_packages_dir) not in sys.path:
            sys.path.insert(0, str(_venv_site_packages_dir))

# Add Content/Python for the analyzer package
if str(_python_dir) not in sys.path:
    sys.path.insert(0, str(_python_dir))

import unreal
import asyncio
import uuid
from typing import Optional


# -----------------------------------------------------------------------------
# Module state (avoid relying on __main__ across ExecPythonCommand calls)
# -----------------------------------------------------------------------------
_analyzer_mcp = None
_analyzer_context_id: Optional[str] = None
_analyzer_server_thread = None
_tools_registered = False
_stderr_redirected = False
_original_stderr = None
_dependency_dialog_shown = False


def _show_dependency_error_dialog_once() -> None:
    """
    Show a user-facing dialog when Python dependencies are not ready.

    This is intentionally simple and actionable: tell the user to run uv sync manually
    and restart the editor. Shown at most once per editor session.
    """
    global _dependency_dialog_shown
    if _dependency_dialog_shown:
        return

    _dependency_dialog_shown = True

    try:
        import uv_sync

        missing = getattr(uv_sync, "LAST_MISSING", None) or []
        last_error = getattr(uv_sync, "LAST_ERROR", None)
    except Exception:
        missing = []
        last_error = None

    missing_text = ", ".join(missing) if missing else "(unknown)"
    details = f"缺失依赖: {missing_text}"
    if last_error:
        details += f"\n\n最近一次错误:\n{last_error}"

    message = (
        "UnrealProjectAnalyzer 需要 Python 依赖才能启动 MCP。\n\n"
        f"{details}\n\n"
        "建议（首次安装/更新后）：\n"
        "1) 关闭 Unreal Editor\n"
        "2) 在插件目录执行:\n"
        "   cd <PluginRoot>/Content/Python\n"
        "   uv sync\n"
        "3) 重新打开 Unreal Editor 后再点击 Start\n\n"
        "更多细节请查看 Output Log 中的 LogPython。"
    )

    try:
        unreal.EditorDialog.show_message(
            "UnrealProjectAnalyzer - 依赖未就绪",
            message,
            unreal.AppMsgType.OK,
        )
    except Exception:
        # If dialog API isn't available, at least log it.
        unreal.log_warning(message)


class _UnrealLogStream:
    """
    A minimal file-like stream that forwards writes to Unreal log.

    Unreal's Python plugin treats stderr as LogPython: Error (even for INFO).
    We redirect FastMCP/Uvicorn stderr to Unreal log to avoid misleading red errors.
    """

    encoding = "utf-8"

    def write(self, s: str) -> int:
        if not s:
            return 0
        # Avoid logging huge chunks as one line
        for line in str(s).splitlines():
            line = line.rstrip()
            if line:
                unreal.log(line)
        return len(s)

    def flush(self) -> None:
        return None

    def isatty(self) -> bool:
        return False


def _redirect_stderr_to_unreal_once() -> None:
    global _stderr_redirected, _original_stderr
    if _stderr_redirected:
        return
    try:
        _original_stderr = sys.stderr
        sys.stderr = _UnrealLogStream()
        _stderr_redirected = True
    except Exception:
        # Best-effort; if we can't redirect, keep default behavior.
        pass


def _store_legacy_globals(mcp, context_id: str) -> None:
    """Backward-compatible: also store into __main__ (best-effort)."""
    try:
        import __main__

        __main__._analyzer_mcp = mcp
        __main__._analyzer_context_id = context_id
    except Exception:
        # UE may execute python in a non-standard global module; ignore.
        pass


def setup_analyzer_bridge(force: bool = False):
    """
    Set up the bridge between C++ and Python for the analyzer.
    This creates a context object that C++ can use to communicate with Python.
    """
    global _analyzer_mcp, _analyzer_context_id, _tools_registered

    if _analyzer_mcp is not None and _analyzer_context_id is not None and not force:
        return {
            "context_id": _analyzer_context_id,
            "status": "initialized",
            "mcp_name": getattr(_analyzer_mcp, "name", "UnrealProjectAnalyzer"),
        }

    try:
        # Ensure dependencies are installed (and sys.path updated by uv_sync)
        try:
            import uv_sync

            if not uv_sync.ensure_dependencies():
                unreal.log_error("[UnrealProjectAnalyzer] Dependencies are missing; cannot initialize bridge.")
                unreal.log_error("[UnrealProjectAnalyzer] Run: uv sync (in Content/Python)")
                _show_dependency_error_dialog_once()
                return None
        except Exception as e:
            unreal.log_warning(f"[UnrealProjectAnalyzer] Dependency check failed: {e}")

        # Check if we can import the analyzer
        from analyzer.server import initialize_from_environment, mcp, register_tools

        unreal.log("[UnrealProjectAnalyzer] MCP server module loaded successfully")

        # Register tools once (important when running via import in UE)
        if not _tools_registered:
            try:
                register_tools()
                _tools_registered = True
            except Exception as e:
                unreal.log_error(f"[UnrealProjectAnalyzer] Failed to register MCP tools: {e}")
                import traceback

                unreal.log_error(traceback.format_exc())
                return None

        # Initialize analyzer config from current environment (optional but helpful)
        try:
            initialize_from_environment()
        except Exception:
            # Not fatal; tools that rely on paths will warn later.
            pass

        # Create a bridge context
        context_id = str(uuid.uuid4())

        # Store the MCP instance for later access
        _analyzer_mcp = mcp
        _analyzer_context_id = context_id
        _store_legacy_globals(mcp, context_id)

        unreal.log(f"[UnrealProjectAnalyzer] Bridge initialized with ID: {context_id}")

        return {
            "context_id": context_id,
            "status": "initialized",
            "mcp_name": mcp.name if hasattr(mcp, 'name') else "UnrealProjectAnalyzer",
        }

    except ImportError as e:
        unreal.log_error(f"[UnrealProjectAnalyzer] Failed to import MCP server: {e}")
        unreal.log_error(f"[UnrealProjectAnalyzer] Make sure dependencies are installed")
        unreal.log_error(f"[UnrealProjectAnalyzer] Run: uv sync (in Content/Python)")
        _show_dependency_error_dialog_once()
        return None
    except Exception as e:
        unreal.log_error(f"[UnrealProjectAnalyzer] Error initializing analyzer: {e}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return None


def get_mcp_instance():
    """Get the global MCP instance."""
    global _analyzer_mcp
    if _analyzer_mcp is not None:
        return _analyzer_mcp
    # Fallback for legacy storage
    try:
        import __main__

        return getattr(__main__, "_analyzer_mcp", None)
    except Exception:
        return None


def start_analyzer_server(
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp",
    cpp_source_path: Optional[str] = None,
    unreal_engine_path: Optional[str] = None,
):
    """
    Start the MCP analyzer server.

    Args:
        transport: Transport protocol ("stdio", "http", "sse")
        host: Host for HTTP/SSE transport
        port: Port for HTTP/SSE transport
        path: Path for HTTP transport
        cpp_source_path: Project C++ source path
        unreal_engine_path: Unreal Engine source path
    """
    try:
        # Prevent FastMCP/Uvicorn from emitting INFO logs as LogPython: Error
        _redirect_stderr_to_unreal_once()

        mcp = get_mcp_instance()
        if not mcp:
            unreal.log_warning("[UnrealProjectAnalyzer] MCP instance not found. Initializing bridge lazily...")
            result = setup_analyzer_bridge()
            if not result:
                unreal.log_error("[UnrealProjectAnalyzer] Failed to initialize bridge; cannot start server.")
                return False
            mcp = get_mcp_instance()
            if not mcp:
                unreal.log_error("[UnrealProjectAnalyzer] MCP instance still missing after initialization.")
                return False

        unreal.log(f"[UnrealProjectAnalyzer] Starting MCP server with transport: {transport}")

        # Set environment variables for paths
        if cpp_source_path:
            os.environ["CPP_SOURCE_PATH"] = cpp_source_path
            unreal.log(f"[UnrealProjectAnalyzer] Set CPP_SOURCE_PATH: {cpp_source_path}")

        if unreal_engine_path:
            os.environ["UNREAL_ENGINE_PATH"] = unreal_engine_path
            unreal.log(f"[UnrealProjectAnalyzer] Set UNREAL_ENGINE_PATH: {unreal_engine_path}")

        # Ensure tools are registered + analyzer initialized from env
        global _tools_registered
        try:
            from analyzer.server import initialize_from_environment, register_tools

            if not _tools_registered:
                register_tools()
                _tools_registered = True
            initialize_from_environment()
        except Exception:
            pass

        # Start the server in a background thread
        def run_server():
            try:
                # Prefer suppressing FastMCP banner if supported.
                if transport == "stdio":
                    try:
                        mcp.run(show_banner=False)
                    except TypeError:
                        mcp.run()
                elif transport == "http":
                    try:
                        mcp.run(transport="http", host=host, port=port, path=path, show_banner=False)
                    except TypeError:
                        mcp.run(transport="http", host=host, port=port, path=path)
                elif transport == "sse":
                    try:
                        mcp.run(transport="sse", host=host, port=port, show_banner=False)
                    except TypeError:
                        mcp.run(transport="sse", host=host, port=port)
                else:
                    unreal.log_error(f"[UnrealProjectAnalyzer] Unknown transport: {transport}")
            except Exception as e:
                unreal.log_error(f"[UnrealProjectAnalyzer] MCP server crashed: {e}")
                import traceback

                unreal.log_error(traceback.format_exc())

        import threading
        global _analyzer_server_thread
        if _analyzer_server_thread is not None and _analyzer_server_thread.is_alive():
            unreal.log_warning("[UnrealProjectAnalyzer] MCP server thread already running")
            return True

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        _analyzer_server_thread = server_thread
        # Legacy storage (best-effort)
        try:
            import __main__

            __main__._analyzer_server_thread = server_thread
        except Exception:
            pass

        unreal.log(f"[UnrealProjectAnalyzer] MCP server started on {transport}://{host}:{port}{path}")
        return True

    except Exception as e:
        unreal.log_error(f"[UnrealProjectAnalyzer] Failed to start MCP server: {e}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False


def stop_analyzer_server():
    """Stop the MCP analyzer server."""
    try:
        global _analyzer_server_thread
        if _analyzer_server_thread is not None:
            unreal.log("[UnrealProjectAnalyzer] Stopping MCP server...")
            # Note: The server thread is a daemon thread, so it will be terminated
            # when the main process exits. For clean shutdown, you'd need to implement
            # proper shutdown handling in the MCP server.
            _analyzer_server_thread = None
            try:
                import __main__

                if hasattr(__main__, "_analyzer_server_thread"):
                    delattr(__main__, "_analyzer_server_thread")
            except Exception:
                pass
            unreal.log("[UnrealProjectAnalyzer] MCP server stopped")
            return True
        return False
    except Exception as e:
        unreal.log_error(f"[UnrealProjectAnalyzer] Error stopping MCP server: {e}")
        return False


def get_server_status():
    """Get the current status of the MCP server."""
    try:
        global _analyzer_server_thread, _analyzer_context_id
        thread = _analyzer_server_thread
        if thread is None:
            # Fallback to legacy storage
            try:
                import __main__

                thread = getattr(__main__, "_analyzer_server_thread", None)
            except Exception:
                thread = None

        if thread is not None:
            return {
                "running": thread.is_alive(),
                "context_id": _analyzer_context_id,
            }
        return {
            "running": False,
            "context_id": None,
        }
    except Exception as e:
        unreal.log_error(f"[UnrealProjectAnalyzer] Error getting server status: {e}")
        return {
            "running": False,
            "error": str(e),
        }


# Auto-initialize when imported
if __name__ != "__main__":
    # We're being imported/exec'd by UE
    unreal.log("[UnrealProjectAnalyzer] Initializing analyzer bridge...")

    # Ensure dependencies are installed
    _deps_ok = False
    try:
        import uv_sync
        _deps_ok = uv_sync.ensure_dependencies()
        if not _deps_ok:
            unreal.log_warning("[UnrealProjectAnalyzer] Dependencies are missing.")
            unreal.log_warning("[UnrealProjectAnalyzer] Please run: uv sync")
            unreal.log_warning("[UnrealProjectAnalyzer] in the Content/Python directory, then restart the editor or click Start again.")
            _show_dependency_error_dialog_once()
    except Exception as e:
        unreal.log_warning(f"[UnrealProjectAnalyzer] Failed to check dependencies: {e}")

    # Only set up the bridge if dependencies are available
    if _deps_ok:
        result = setup_analyzer_bridge()
        if result:
            unreal.log("[UnrealProjectAnalyzer] Analyzer initialized successfully")
        else:
            unreal.log_error("[UnrealProjectAnalyzer] Failed to initialize analyzer")
    else:
        unreal.log_error("[UnrealProjectAnalyzer] Skipping bridge setup due to missing dependencies")
