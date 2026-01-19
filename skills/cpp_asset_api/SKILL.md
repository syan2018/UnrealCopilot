---
name: cpp_asset_api
description: CppSkillApiSubsystem 资产原语 - 重命名、复制、删除、保存资产
tags: [cpp, asset, api]
---

# CppSkillApiSubsystem - AssetOps

本 skill 文档描述 `UCppSkillApiSubsystem` 的资产相关原语。

## 入口说明

从 UE Python 中获取子系统：

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
```

## 可用操作

| 方法 | 描述 |
|------|------|
| `RenameAsset` | 重命名/移动资产，自动修复重定向器 |
| `DuplicateAsset` | 复制资产到新位置 |
| `DeleteAsset` | 删除资产 |
| `SaveAsset` | 保存单个资产 |

详细接口和示例见 `docs/overview.md`。

## 快速示例

```python
import unreal
api = unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)

# 重命名资产
success, error = api.rename_asset("/Game/Old", "/Game/New")

# 复制资产
success, error = api.duplicate_asset("/Game/Original", "/Game/Copy")

# 删除资产
success, error = api.delete_asset("/Game/ToDelete")

# 保存资产
success, error = api.save_asset("/Game/Modified")
```
