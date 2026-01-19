# EditorOps 接口一览

以下函数均为 `UCppSkillApiSubsystem` 的 `BlueprintCallable` 原语：

- `ListDirtyPackages() -> [str]`
- `SaveDirtyPackages(bPromptUser, OutError) -> bool`
- `UndoLastTransaction(OutError) -> bool`
- `RedoLastTransaction(OutError) -> bool`

## 说明

- 事务接口依赖编辑器的撤销系统；失败时 `OutError` 会给出原因。

