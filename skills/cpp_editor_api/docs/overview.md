# CppSkillApiSubsystem - Editor Operations

## 获取子系统

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用方法

### ListDirtyPackages

列出所有未保存的包。

```python
dirty_packages = api.list_dirty_packages()
# 返回: ["/Game/Characters/BP_Hero", "/Game/Maps/MainLevel", ...]
```

**返回**：
- `dirty_packages` (list[str]): 未保存的包路径列表

### SaveDirtyPackages

保存所有未保存的包。

```python
success, error = api.save_dirty_packages(prompt_user=False)
```

**参数**：
- `prompt_user` (bool): 是否弹出保存对话框让用户确认

**返回**：
- `success` (bool): 是否成功
- `error` (str): 失败时的错误信息

### UndoLastTransaction

撤销上一个事务。

```python
success, error = api.undo_last_transaction()
```

**返回**：
- `success` (bool): 是否成功
- `error` (str): 失败时的错误信息

**注意**：只能撤销支持事务的操作。

### RedoLastTransaction

重做上一个撤销的事务。

```python
success, error = api.redo_last_transaction()
```

**返回**：
- `success` (bool): 是否成功
- `error` (str): 失败时的错误信息

## 示例：检查并保存所有修改

```python
import unreal

api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 列出所有未保存的包
dirty = api.list_dirty_packages()

if dirty:
    print(f"Found {len(dirty)} dirty packages:")
    for pkg in dirty:
        print(f"  - {pkg}")
    
    # 保存所有
    success, error = api.save_dirty_packages(prompt_user=False)
    RESULT = {"saved": len(dirty), "success": success, "error": error}
else:
    RESULT = {"saved": 0, "message": "No dirty packages"}
```
