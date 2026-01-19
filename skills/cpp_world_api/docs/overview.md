# CppSkillApiSubsystem - World Operations

## 获取子系统

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用方法

### LoadMap

加载关卡。

```python
success, error = api.load_map(map_path="/Game/Maps/MainLevel")
```

### SpawnActorByClassPath

在编辑器世界中生成 Actor。

```python
actor, error = api.spawn_actor_by_class_path(
    class_path="/Game/Characters/BP_Hero.BP_Hero_C",
    transform=unreal.Transform(
        location=unreal.Vector(100, 200, 0),
        rotation=unreal.Rotator(0, 90, 0),
        scale=unreal.Vector(1, 1, 1)
    )
)
```

**注意**：蓝图类路径需要加 `_C` 后缀。

### FindActorByName

按名称查找 Actor。

```python
actor = api.find_actor_by_name(actor_name="BP_Hero_C_0")
```

### DestroyActorByName

按名称销毁 Actor。

```python
success, error = api.destroy_actor_by_name(actor_name="BP_Hero_C_0")
```

### SetActorPropertyByString

设置 Actor 属性值。

```python
success, error = api.set_actor_property_by_string(
    actor_name="BP_Hero_C_0",
    property_name="MaxHealth",
    value_as_string="200.0"
)
```

### SetActorTransformByName

设置 Actor 的 Transform。

```python
success, error = api.set_actor_transform_by_name(
    actor_name="BP_Hero_C_0",
    transform=unreal.Transform(
        location=unreal.Vector(500, 0, 100),
        rotation=unreal.Rotator(0, 180, 0),
        scale=unreal.Vector(2, 2, 2)
    )
)
```

## 示例：批量生成 Actor

```python
import unreal

api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

spawned = []
for x in range(5):
    for y in range(5):
        transform = unreal.Transform(
            location=unreal.Vector(x * 200, y * 200, 0),
            rotation=unreal.Rotator(0, 0, 0),
            scale=unreal.Vector(1, 1, 1)
        )
        actor, error = api.spawn_actor_by_class_path(
            class_path="/Game/Props/BP_Crate.BP_Crate_C",
            transform=transform
        )
        if actor:
            spawned.append(str(actor.get_name()))

RESULT = {"spawned": spawned, "count": len(spawned)}
```
