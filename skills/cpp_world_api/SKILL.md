---
name: cpp_world_api
description: CppSkillApiSubsystem 世界原语 - 加载关卡、生成/查找/销毁 Actor、设置属性和 Transform
tags: [cpp, world, actor, api]
---

# CppSkillApiSubsystem - WorldOps

本 skill 文档描述 `UCppSkillApiSubsystem` 的世界/关卡相关原语。

## 入口说明

从 UE Python 中获取子系统：

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用操作

| 方法 | 描述 |
|------|------|
| `LoadMap` | 加载关卡 |
| `SpawnActorByClassPath` | 生成 Actor |
| `FindActorByName` | 按名称查找 Actor |
| `DestroyActorByName` | 按名称销毁 Actor |
| `SetActorPropertyByString` | 设置 Actor 属性 |
| `SetActorTransformByName` | 设置 Actor Transform |

详细接口和示例见 `docs/overview.md`。

## 快速示例

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 加载关卡
api.load_map("/Game/Maps/MainLevel")

# 生成 Actor
transform = unreal.Transform(
    location=unreal.Vector(100, 0, 0),
    rotation=unreal.Rotator(0, 0, 0),
    scale=unreal.Vector(1, 1, 1)
)
actor, error = api.spawn_actor_by_class_path(
    "/Game/Characters/BP_Hero.BP_Hero_C",
    transform
)

# 查找 Actor
found = api.find_actor_by_name("BP_Hero_C_0")

# 设置 Transform
api.set_actor_transform_by_name("BP_Hero_C_0", transform)

# 销毁 Actor
api.destroy_actor_by_name("BP_Hero_C_0")
```
