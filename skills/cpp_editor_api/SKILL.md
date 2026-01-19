---
name: cpp_editor_api
description: CppSkillApiSubsystem 编辑器原语 - 列出/保存未保存包、撤销/重做事务
tags: [cpp, editor, save, undo, api]
---

# CppSkillApiSubsystem - EditorOps

本 skill 文档描述 `UCppSkillApiSubsystem` 的编辑器相关原语。

## 入口说明

从 UE Python 中获取子系统：

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用操作

| 方法 | 描述 |
|------|------|
| `ListDirtyPackages` | 列出所有未保存的包 |
| `SaveDirtyPackages` | 保存所有未保存的包 |
| `UndoLastTransaction` | 撤销上一个事务 |
| `RedoLastTransaction` | 重做上一个撤销的事务 |

详细接口和示例见 `docs/overview.md`。

## 快速示例

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 列出未保存的包
dirty = api.list_dirty_packages()
print(f"Dirty packages: {dirty}")

# 保存所有未保存的包（不弹窗）
success, error = api.save_dirty_packages(False)

# 撤销
api.undo_last_transaction()

# 重做
api.redo_last_transaction()
```
