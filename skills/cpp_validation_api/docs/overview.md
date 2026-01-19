# CppSkillApiSubsystem - Validation Operations

## 获取子系统

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用方法

### CompileAllBlueprintsSummary

编译项目中所有蓝图并返回摘要。

```python
summary = api.compile_all_blueprints_summary()
```

**返回**：
- `summary` (str): 编译结果摘要，包含错误和警告信息

## 示例：编译并检查所有蓝图

```python
import unreal

api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 编译所有蓝图
summary = api.compile_all_blueprints_summary()

# 解析结果
lines = summary.split("\n")
has_errors = "Errors:" in summary and "Errors: 0" not in summary

RESULT = {
    "summary": summary,
    "has_errors": has_errors,
    "lines": len(lines)
}
```

## 注意事项

- 此操作可能需要较长时间（取决于项目中蓝图数量）
- 建议在执行前保存所有修改
- 编译过程中会自动加载所有蓝图资产
