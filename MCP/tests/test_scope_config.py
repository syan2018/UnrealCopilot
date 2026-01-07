"""
Tests for plugin scope support in config.py.

Run with: uv run pytest MCP/tests/test_scope_config.py -v
"""

import os
import pytest
from pathlib import Path

# Ensure clean config state for each test
@pytest.fixture(autouse=True)
def reset_config():
    """Reset config before each test."""
    from unreal_analyzer.config import reset_config
    reset_config()
    yield
    reset_config()


class TestSourceType:
    """Tests for SourceType enum."""

    def test_source_type_values(self):
        """Verify all source types are defined."""
        from unreal_analyzer.config import SourceType
        
        assert SourceType.PROJECT_SOURCE.value == "project_source"
        assert SourceType.PROJECT_PLUGIN.value == "project_plugin"
        assert SourceType.ENGINE_SOURCE.value == "engine_source"
        assert SourceType.ENGINE_PLUGIN.value == "engine_plugin"


class TestSearchScope:
    """Tests for SearchScope enum."""

    def test_search_scope_values(self):
        """Verify all search scopes are defined."""
        from unreal_analyzer.config import SearchScope
        
        assert SearchScope.PROJECT.value == "project"
        assert SearchScope.ENGINE.value == "engine"
        assert SearchScope.PLUGIN.value == "plugin"
        assert SearchScope.ALL.value == "all"


class TestSourceConfig:
    """Tests for SourceConfig dataclass."""

    def test_is_engine_property(self):
        """Test is_engine property for backward compatibility."""
        from unreal_analyzer.config import SourceConfig, SourceType
        
        project_src = SourceConfig(path="/project/Source", source_type=SourceType.PROJECT_SOURCE)
        project_plugin = SourceConfig(path="/project/Plugins/MyPlugin/Source", source_type=SourceType.PROJECT_PLUGIN)
        engine_src = SourceConfig(path="/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        engine_plugin = SourceConfig(path="/engine/Plugins/MyPlugin/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        assert project_src.is_engine == False
        assert project_plugin.is_engine == False
        assert engine_src.is_engine == True
        assert engine_plugin.is_engine == True

    def test_is_plugin_property(self):
        """Test is_plugin property."""
        from unreal_analyzer.config import SourceConfig, SourceType
        
        project_src = SourceConfig(path="/project/Source", source_type=SourceType.PROJECT_SOURCE)
        project_plugin = SourceConfig(path="/project/Plugins/MyPlugin/Source", source_type=SourceType.PROJECT_PLUGIN)
        engine_src = SourceConfig(path="/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        engine_plugin = SourceConfig(path="/engine/Plugins/MyPlugin/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        assert project_src.is_plugin == False
        assert project_plugin.is_plugin == True
        assert engine_src.is_plugin == False
        assert engine_plugin.is_plugin == True


class TestConfig:
    """Tests for Config class with scope filtering."""

    def test_add_source_path_with_type(self):
        """Test adding source paths with different types."""
        from unreal_analyzer.config import Config, SourceType
        
        config = Config()
        config._source_configs = []  # Clear auto-detected paths
        config.cpp_source_paths = []
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        config.add_source_path("/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        config.add_source_path("/engine/Plugins/B/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        assert len(config._source_configs) == 4

    def test_get_source_paths_project_scope(self):
        """Test getting paths for project scope (includes project plugins)."""
        from unreal_analyzer.config import Config, SourceType, SearchScope
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        config.add_source_path("/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        config.add_source_path("/engine/Plugins/B/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        paths = config.get_source_paths(SearchScope.PROJECT)
        
        assert len(paths) == 2
        # Paths are resolved to absolute, check endings instead
        assert any(p.endswith("project\\Source") or p.endswith("project/Source") for p in paths)
        assert any("Plugins" in p and "A" in p for p in paths)

    def test_get_source_paths_engine_scope(self):
        """Test getting paths for engine scope (includes engine plugins)."""
        from unreal_analyzer.config import Config, SourceType, SearchScope
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        config.add_source_path("/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        config.add_source_path("/engine/Plugins/B/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        paths = config.get_source_paths(SearchScope.ENGINE)
        
        assert len(paths) == 2
        # Paths are resolved to absolute, check endings instead
        assert any(p.endswith("engine\\Source") or p.endswith("engine/Source") for p in paths)
        assert any("Plugins" in p and "B" in p for p in paths)

    def test_get_source_paths_plugin_scope(self):
        """Test getting paths for plugin scope (only plugins, no main source)."""
        from unreal_analyzer.config import Config, SourceType, SearchScope
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        config.add_source_path("/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        config.add_source_path("/engine/Plugins/B/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        paths = config.get_source_paths(SearchScope.PLUGIN)
        
        assert len(paths) == 2
        # Plugin scope should only include plugin paths
        assert any("Plugins" in p and "A" in p for p in paths)
        assert any("Plugins" in p and "B" in p for p in paths)
        # Should not include main Source directories
        assert not any(p.endswith("project\\Source") or p.endswith("project/Source") for p in paths)
        assert not any(p.endswith("engine\\Source") or p.endswith("engine/Source") for p in paths)

    def test_get_source_paths_all_scope(self):
        """Test getting all paths."""
        from unreal_analyzer.config import Config, SourceType, SearchScope
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        config.add_source_path("/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        config.add_source_path("/engine/Plugins/B/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        paths = config.get_source_paths(SearchScope.ALL)
        
        assert len(paths) == 4

    def test_get_plugin_paths_convenience(self):
        """Test convenience method for getting plugin paths."""
        from unreal_analyzer.config import Config, SourceType
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        config.add_source_path("/engine/Plugins/B/Source", source_type=SourceType.ENGINE_PLUGIN)
        
        paths = config.get_plugin_paths()
        
        assert len(paths) == 2
        # Paths are resolved to absolute, check plugin paths are included
        assert any("Plugins" in p and "A" in p for p in paths)
        assert any("Plugins" in p and "B" in p for p in paths)

    def test_has_plugin_source(self):
        """Test checking if plugin sources are configured."""
        from unreal_analyzer.config import Config, SourceType
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        
        assert config.has_plugin_source() == False
        
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        
        assert config.has_plugin_source() == True


class TestScopeStringParsing:
    """Tests for scope string parsing."""

    def test_scope_from_string(self):
        """Test that scope can be parsed from string values."""
        from unreal_analyzer.config import Config, SourceType
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/project/Plugins/A/Source", source_type=SourceType.PROJECT_PLUGIN)
        
        # Test string scope values
        project_paths = config.get_source_paths("project")
        plugin_paths = config.get_source_paths("plugin")
        all_paths = config.get_source_paths("all")
        
        assert len(project_paths) == 2
        assert len(plugin_paths) == 1
        assert len(all_paths) == 2

    def test_invalid_scope_fallback(self):
        """Test that invalid scope falls back to default."""
        from unreal_analyzer.config import Config, SourceType, SearchScope
        
        config = Config()
        config._source_configs = []
        config.cpp_source_paths = []
        config.default_scope = SearchScope.PROJECT
        
        config.add_source_path("/project/Source", source_type=SourceType.PROJECT_SOURCE)
        config.add_source_path("/engine/Source", source_type=SourceType.ENGINE_SOURCE)
        
        # Invalid scope should fall back to default (project)
        paths = config.get_source_paths("invalid_scope")
        
        assert len(paths) == 1
        # Paths are resolved to absolute
        assert any(p.endswith("project\\Source") or p.endswith("project/Source") for p in paths)
