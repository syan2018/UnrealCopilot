// Copyright UE5 Project Analyzer Team. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class UUE5ProjectAnalyzerSettings;

/**
 * Manage external MCP Server process (uv run ...).
 *
 * 设计目标：
 * - UE 内一键启动/停止 MCP Server
 * - 通过 uv 管理 Python 依赖，不污染 Unreal 自带 Python
 * - 默认只监听 127.0.0.1，避免对局域网暴露
 */
class FUE5ProjectAnalyzerMcpLauncher
{
public:
	bool Start(const UUE5ProjectAnalyzerSettings& Settings);
	void Stop();
	bool IsRunning() const;

	FString GetMcpUrl() const { return McpUrl; }
	FString GetLastCommandLine() const { return LastCommandLine; }

private:
	static FString GetDefaultMcpServerDir();
	static FString Quote(const FString& S);
	static FString TransportToArg(const UUE5ProjectAnalyzerSettings& Settings);

private:
	FProcHandle ProcHandle;
	uint32 ProcId = 0;
	FString McpUrl;
	FString LastCommandLine;
};

