# AssetOps 接口一览

以下函数均为 `UCppSkillApiSubsystem` 的 `BlueprintCallable` 原语：

- `RenameAsset(SourcePath, DestPath, OutError) -> bool`
- `DuplicateAsset(SourcePath, DestPath, OutError) -> bool`
- `DeleteAsset(AssetPath, OutError) -> bool`
- `SaveAsset(AssetPath, OutError) -> bool`

## 说明

- `SourcePath/DestPath` 使用 UE 资产路径（例如 `/Game/Folder/MyAsset`）。
- `OutError` 会返回失败原因；成功时为空或保持不变。

