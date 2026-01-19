# BlueprintOps 接口一览

以下函数均为 `UCppSkillApiSubsystem` 的 `BlueprintCallable` 原语：

- `CreateBlueprint(ParentClassPath, PackagePath, BlueprintName, OutBlueprintPath, OutError) -> bool`
- `CompileBlueprint(BlueprintPath, OutError) -> bool`
- `SaveBlueprint(BlueprintPath, OutError) -> bool`
- `SetBlueprintCDOPropertyByString(BlueprintPath, PropertyName, ValueAsString, OutError) -> bool`
- `AddBlueprintComponent(BlueprintPath, ComponentClassPath, ComponentName, OutError) -> bool`
- `RemoveBlueprintComponent(BlueprintPath, ComponentName, OutError) -> bool`

## 说明

- `BlueprintPath` 使用 UE 资产路径（例如 `/Game/Folder/BP_MyActor`）。
- `ParentClassPath/ComponentClassPath` 使用类路径（例如 `/Script/Engine.StaticMeshComponent`）。
- `ValueAsString` 使用 `FProperty::ImportText` 规则解析。

