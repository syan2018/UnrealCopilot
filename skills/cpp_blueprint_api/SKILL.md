---
name: cpp_blueprint_api
description: CppSkillApiSubsystem 蓝图原语 - 创建、编译、保存蓝图，设置 CDO 属性，管理组件
tags: [cpp, blueprint, api]
---

# CppSkillApiSubsystem - BlueprintOps

本 skill 文档描述 `UCppSkillApiSubsystem` 的蓝图相关原语。

## 入口说明

从 UE Python 中获取子系统：

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用操作

| 方法 | 描述 |
|------|------|
| `CreateBlueprint` | 创建新蓝图（指定父类） |
| `CompileBlueprint` | 编译蓝图 |
| `SaveBlueprint` | 保存蓝图 |
| `SetBlueprintCDOPropertyByString` | 设置蓝图 CDO 默认值 |
| `AddBlueprintComponent` | 向蓝图添加组件 |
| `RemoveBlueprintComponent` | 从蓝图移除组件 |

详细接口和示例见 `docs/overview.md`。

## 快速示例

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 创建蓝图
bp_path, error = api.create_blueprint(
    "/Script/Engine.Actor",
    "/Game/Blueprints",
    "BP_MyActor"
)

# 添加组件
api.add_blueprint_component(bp_path, "/Script/Engine.StaticMeshComponent", "Mesh")

# 设置默认值
api.set_blueprint_cdo_property_by_string(bp_path, "MyProperty", "100")

# 编译并保存
api.compile_blueprint(bp_path)
api.save_blueprint(bp_path)
```
