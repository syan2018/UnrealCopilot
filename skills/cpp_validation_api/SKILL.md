---
name: cpp_validation_api
description: CppSkillApiSubsystem 验证原语 - 编译所有蓝图并返回错误/警告摘要
tags: [cpp, validation, compile, api]
---

# CppSkillApiSubsystem - ValidationOps

本 skill 文档描述 `UCppSkillApiSubsystem` 的验证相关原语。

## 入口说明

从 UE Python 中获取子系统：

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用操作

| 方法 | 描述 |
|------|------|
| `CompileAllBlueprintsSummary` | 编译项目中所有蓝图并返回摘要 |

详细接口和示例见 `docs/overview.md`。

## 快速示例

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 编译所有蓝图
summary = api.compile_all_blueprints_summary()
print(summary)

# 检查是否有错误
has_errors = "Errors:" in summary and "Errors: 0" not in summary
RESULT = {"summary": summary, "has_errors": has_errors}
```

## 注意事项

- 此操作可能需要较长时间（取决于项目中蓝图数量）
- 建议在执行前保存所有修改
