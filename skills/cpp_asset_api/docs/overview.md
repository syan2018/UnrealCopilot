# CppSkillApiSubsystem - Asset Operations

## 获取子系统

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用方法

### RenameAsset

重命名/移动资产。

```python
success, error = api.rename_asset(
    source_path="/Game/OldFolder/MyAsset",
    dest_path="/Game/NewFolder/RenamedAsset"
)
```

**参数**：
- `source_path` (str): 源资产路径（如 `/Game/Characters/BP_Hero`）
- `dest_path` (str): 目标路径（如 `/Game/Characters/BP_Hero_New`）

**返回**：
- `success` (bool): 是否成功
- `error` (str): 失败时的错误信息

**注意**：会自动修复重定向器（Redirectors）。

---

### DuplicateAsset

复制资产到新位置。

```python
success, error = api.duplicate_asset(
    source_path="/Game/Characters/BP_Hero",
    dest_path="/Game/Characters/BP_Hero_Copy"
)
```

**参数**：
- `source_path` (str): 源资产路径
- `dest_path` (str): 目标路径

**返回**：
- `success` (bool): 是否成功
- `error` (str): 失败时的错误信息

---

### DeleteAsset

删除资产。

```python
success, error = api.delete_asset(asset_path="/Game/Characters/BP_Old")
```

**参数**：
- `asset_path` (str): 要删除的资产路径

**返回**：
- `success` (bool): 是否成功
- `error` (str): 失败时的错误信息

**警告**：此操作不可撤销，请谨慎使用。

---

### SaveAsset

保存单个资产。

```python
success, error = api.save_asset(asset_path="/Game/Characters/BP_Hero")
```

**参数**：
- `asset_path` (str): 要保存的资产路径

**返回**：
- `success` (bool): 是否成功
- `error` (str): 失败时的错误信息

## 示例：批量重命名

```python
import unreal

api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
registry = unreal.AssetRegistryHelpers.get_asset_registry()

# 获取所有蓝图
filter = unreal.ARFilter()
filter.class_paths = [unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")]
filter.package_paths = ["/Game/Characters"]
assets = registry.get_assets(filter)

results = []
for asset in assets:
    old_path = str(asset.package_name)
    if "Old" in old_path:
        new_path = old_path.replace("Old", "New")
        success, error = api.rename_asset(old_path, new_path)
        results.append({"old": old_path, "new": new_path, "ok": success})

RESULT = {"renamed": results}
```
