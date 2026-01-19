# CppSkillApiSubsystem - Blueprint Operations

## 获取子系统

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用方法

### CreateBlueprint

创建新蓝图。

```python
bp_path, error = api.create_blueprint(
    parent_class_path="/Script/Engine.Actor",
    package_path="/Game/Characters",
    blueprint_name="BP_NewCharacter"
)
```

**参数**：
- `parent_class_path` (str): 父类路径（如 `/Script/Engine.Actor`、`/Script/Engine.Character`）
- `package_path` (str): 蓝图存放目录（如 `/Game/Characters`）
- `blueprint_name` (str): 蓝图名称

**返回**：
- `bp_path` (str): 创建的蓝图完整路径
- `error` (str): 失败时的错误信息

### CompileBlueprint

编译蓝图。

```python
success, error = api.compile_blueprint(blueprint_path="/Game/Characters/BP_Hero")
```

### SaveBlueprint

保存蓝图。

```python
success, error = api.save_blueprint(blueprint_path="/Game/Characters/BP_Hero")
```

### SetBlueprintCDOPropertyByString

设置蓝图 CDO（Class Default Object）属性值。

```python
success, error = api.set_blueprint_cdo_property_by_string(
    blueprint_path="/Game/Characters/BP_Hero",
    property_name="MaxHealth",
    value_as_string="100.0"
)
```

**支持的类型**：
- 数值类型：`"100"`, `"3.14"`
- 布尔：`"true"`, `"false"`
- 字符串：`"Hello World"`
- 向量：`"(X=1.0,Y=2.0,Z=3.0)"`
- 旋转：`"(Pitch=0.0,Yaw=90.0,Roll=0.0)"`

### AddBlueprintComponent

向蓝图添加组件。

```python
success, error = api.add_blueprint_component(
    blueprint_path="/Game/Characters/BP_Hero",
    component_class_path="/Script/Engine.StaticMeshComponent",
    component_name="MyMesh"
)
```

**常用组件类**：
- `/Script/Engine.StaticMeshComponent`
- `/Script/Engine.SkeletalMeshComponent`
- `/Script/Engine.BoxComponent`
- `/Script/Engine.SphereComponent`
- `/Script/Engine.CapsuleComponent`
- `/Script/Engine.AudioComponent`
- `/Script/Engine.PointLightComponent`

### RemoveBlueprintComponent

从蓝图移除组件。

```python
success, error = api.remove_blueprint_component(
    blueprint_path="/Game/Characters/BP_Hero",
    component_name="MyMesh"
)
```

## 示例：创建并配置蓝图

```python
import unreal

api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 1. 创建蓝图
bp_path, error = api.create_blueprint(
    parent_class_path="/Script/Engine.Actor",
    package_path="/Game/Gameplay",
    blueprint_name="BP_HealthPickup"
)

if bp_path:
    # 2. 添加组件
    api.add_blueprint_component(bp_path, "/Script/Engine.StaticMeshComponent", "PickupMesh")
    api.add_blueprint_component(bp_path, "/Script/Engine.SphereComponent", "CollisionSphere")
    
    # 3. 设置默认值
    api.set_blueprint_cdo_property_by_string(bp_path, "HealAmount", "50.0")
    
    # 4. 编译并保存
    api.compile_blueprint(bp_path)
    api.save_blueprint(bp_path)

RESULT = {"created": bp_path, "error": error}
```
