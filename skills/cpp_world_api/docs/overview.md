# WorldOps 接口一览

以下函数均为 `UCppSkillApiSubsystem` 的 `BlueprintCallable` 原语：

- `LoadMap(MapPath, OutError) -> bool`
- `SpawnActorByClassPath(ClassPath, Transform, OutError) -> AActor*`
- `FindActorByName(ActorName) -> AActor*`
- `DestroyActorByName(ActorName, OutError) -> bool`
- `SetActorPropertyByString(ActorName, PropertyName, ValueAsString, OutError) -> bool`
- `SetActorTransformByName(ActorName, Transform, OutError) -> bool`

## 说明

- `MapPath` 为长包路径（例如 `/Game/Maps/MyMap`）。
- 这些接口均在 Editor World 上执行。

