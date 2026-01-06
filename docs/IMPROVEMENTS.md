# UnrealProjectAnalyzer 改进建议

基于实际使用 Lyra 项目进行技能链条分析的经验，本文档记录了工具集的改进建议。

## ✅ 已修复问题

### 1. HTTP Socket 发送失败 (已修复)

**现象**：
```
LogHttpConnectionResponseWriteContext: Warning: WriteBytes sent -1/164 bytes
LogHttpConnection: Error: errors.com.epicgames.httpserver.socket_send_failure
```

或者 Python 侧报错：
```
ConnectionResetError: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
```

**原因**：UE 内置 HTTP Server 在写入大 JSON 响应时会失败，强制关闭连接。

**已实现的修复**：**通用异步任务 + 分块拉取机制**

#### UE 侧 (C++)
- 新增 `FAsyncJsonJob` 异步任务管理器
- 新增端点：
  - `GET /analysis/job/status?id=...` - 查询任务状态
  - `GET /analysis/job/result?id=...&offset=...&limit=...` - 分块获取结果
- 已改造的接口：
  - `/analysis/reference-chain` - 始终返回异步任务
  - `/blueprint/graph` - 节点数 ≥50 时自动走异步模式

#### Python 侧
- `http_client.py` 新增 `get_with_async()` 方法
- 自动检测响应是否为异步任务信封
- 透明轮询 + 分块拉取 + JSON 重组
- 对调用方完全透明，无需修改业务代码

**使用示例**：
```python
# 自动处理异步任务
result = await client.get_with_async("/analysis/reference-chain", {"start": path})
```

---

## 🔧 工具改进建议

### C++ 分析工具

| 问题 | 当前行为 | 建议改进 |
|------|---------|---------|
| `search_cpp_code` 正则不稳定 | 某些正则返回空 | 改进 tree-sitter 查询，或提供更详细的错误信息 |
| `analyze_cpp_class` 宏解析 | UPROPERTY 被当作方法 | 区分宏和方法定义 |
| `get_cpp_class_hierarchy` 接口 | interfaces 始终为空 | 修复接口继承检测 |

### Blueprint 分析工具

| 问题 | 当前行为 | 建议改进 |
|------|---------|---------|
| 变量默认值 | 只返回 `default: ""` | 解析实际默认值 |
| 大蓝图图表 | 返回所有节点 | 增加分页或摘要模式 |

### 输出控制

| 问题 | 当前行为 | 建议改进 |
|------|---------|---------|
| 引用链过大 | 返回完整树 | 增加节点数限制、添加 `truncated` 标记 |
| 包含引擎资源 | `/Script/*`, `/Engine/*` 全返回 | 增加 `exclude_engine=true` 参数 |

---

## ✨ 新功能建议

### 1. 健康检查端点

```cpp
// /health - 检查 UE 插件是否运行
static bool HandleHealth(const FHttpServerRequest& Request, const FHttpResultCallback& OnComplete)
{
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetBoolField(TEXT("ok"), true);
    Root->SetStringField(TEXT("status"), TEXT("running"));
    Root->SetStringField(TEXT("ue_version"), *FEngineVersion::Current().ToString());
    OnComplete(FUnrealAnalyzerHttpUtils::JsonResponse(JsonString(Root)));
    return true;
}
```

### 2. 摘要模式

为大响应增加摘要模式参数：
- `?summary=true` - 只返回计数和顶级信息
- `?limit=100` - 限制返回数量

### 3. 批量查询

支持一次查询多个资源：
```
POST /blueprint/batch
{
  "paths": ["/Game/BP1", "/Game/BP2"],
  "operation": "details"
}
```

---

## 📊 工具使用统计（基于 Lyra 技能链条分析）

| 工具 | 调用次数 | 成功率 | 最有价值 |
|------|---------|--------|---------|
| `search_blueprints` | 4 | 100% | ⭐⭐⭐⭐ |
| `get_blueprint_graph` | 2 | 100% | ⭐⭐⭐⭐⭐ |
| `get_blueprint_details` | 3 | 100% | ⭐⭐⭐⭐ |
| `search_cpp_code` | 8 | 75% | ⭐⭐⭐ |
| `analyze_cpp_class` | 4 | 100% | ⭐⭐⭐ |
| `trace_reference_chain` | 1 | 0%* | ⭐⭐⭐⭐ |
| `detect_ue_patterns` | 1 | 100% | ⭐⭐⭐⭐⭐ |
| `get_cpp_blueprint_exposure` | 1 | 100% | ⭐⭐⭐⭐⭐ |
| `find_cpp_references` | 1 | 100% | ⭐⭐⭐⭐⭐ |
| `find_cpp_class_usage` | 1 | 0%* | - |

\* HTTP socket 失败（响应过大）

---

## 🎯 优先级建议

### 高优先级（影响核心功能）
1. 修复大响应导致的 HTTP socket 失败
2. 为 `trace_reference_chain` 增加节点数限制
3. 增加健康检查端点（便于快速验证 UE 插件状态）

### 中优先级（提升体验）
4. 改进 `search_cpp_code` 正则匹配
5. 修复 `analyze_cpp_class` 宏解析
6. 增加 `exclude_engine` 过滤参数

### 低优先级（增值功能）
7. 摘要模式
8. 批量查询
9. 蓝图变量默认值解析

---

## 📝 更新日志

- **2026-01-06**：基于 Lyra 技能链条分析创建初始文档
