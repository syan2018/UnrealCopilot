// Copyright UE5 Project Analyzer Team. All Rights Reserved.

#include "UE5ProjectAnalyzerMcpLauncher.h"

#include "UE5ProjectAnalyzerSettings.h"

#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "Misc/FeedbackContext.h"

namespace
{
	static FString NormalizePath(const FString& InPath)
	{
		FString P = InPath;
		FPaths::NormalizeDirectoryName(P);
		return P;
	}
}

FString FUE5ProjectAnalyzerMcpLauncher::GetDefaultMcpServerDir()
{
	// uv project lives at plugin root (pyproject.toml at root), so run from <PluginDir>
	TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("UE5ProjectAnalyzer"));
	if (Plugin.IsValid())
	{
		return NormalizePath(Plugin->GetBaseDir());
	}
	return TEXT("");
}

FString FUE5ProjectAnalyzerMcpLauncher::Quote(const FString& S)
{
	// Minimal quoting for CreateProc command line.
	if (S.Contains(TEXT(" ")) || S.Contains(TEXT("\t")) || S.Contains(TEXT("\"")))
	{
		FString Escaped = S;
		Escaped.ReplaceInline(TEXT("\""), TEXT("\\\""));
		return FString::Printf(TEXT("\"%s\""), *Escaped);
	}
	return S;
}

FString FUE5ProjectAnalyzerMcpLauncher::TransportToArg(const UUE5ProjectAnalyzerSettings& Settings)
{
	switch (Settings.Transport)
	{
	case EUE5AnalyzerMcpTransport::Stdio:
		return TEXT("stdio");
	case EUE5AnalyzerMcpTransport::Sse:
		return TEXT("sse");
	case EUE5AnalyzerMcpTransport::Http:
	default:
		return TEXT("http");
	}
}

bool FUE5ProjectAnalyzerMcpLauncher::Start(const UUE5ProjectAnalyzerSettings& Settings)
{
	if (IsRunning())
	{
		return true;
	}

	const FString UvExe = Settings.UvExecutable.IsEmpty() ? TEXT("uv") : Settings.UvExecutable;

	FString ServerDir = Settings.McpServerDirectory;
	if (ServerDir.IsEmpty())
	{
		ServerDir = GetDefaultMcpServerDir();
	}
	ServerDir = NormalizePath(ServerDir);

	// Default cpp source path: <Project>/Source
	FString CppSource = Settings.CppSourcePath;
	if (CppSource.IsEmpty())
	{
		CppSource = NormalizePath(FPaths::Combine(FPaths::ProjectDir(), TEXT("Source")));
	}

	const FString Transport = TransportToArg(Settings);
	McpUrl = TEXT("");
	if (Transport == TEXT("http"))
	{
		McpUrl = FString::Printf(TEXT("http://%s:%d%s"), *Settings.McpHost, Settings.McpPort, *Settings.McpPath);
	}
	else if (Transport == TEXT("sse"))
	{
		McpUrl = FString::Printf(TEXT("http://%s:%d"), *Settings.McpHost, Settings.McpPort);
	}

	// Build:
	// uv run --directory <ServerDir> ue5-analyzer -- --transport http --mcp-host ... --mcp-port ... --mcp-path ...
	//   --cpp-source-path ... --ue-plugin-host ... --ue-plugin-port ...
	FString Args;
	Args += TEXT("run");
	if (!ServerDir.IsEmpty())
	{
		Args += TEXT(" --directory ");
		Args += Quote(ServerDir);
	}
	Args += TEXT(" ue5-analyzer -- ");
	Args += TEXT("--transport ");
	Args += Transport;

	if (Transport != TEXT("stdio"))
	{
		Args += TEXT(" --mcp-host ");
		Args += Quote(Settings.McpHost);
		Args += TEXT(" --mcp-port ");
		Args += FString::FromInt(Settings.McpPort);

		if (Transport == TEXT("http"))
		{
			Args += TEXT(" --mcp-path ");
			Args += Quote(Settings.McpPath);
		}
	}

	Args += TEXT(" --cpp-source-path ");
	Args += Quote(CppSource);
	Args += TEXT(" --ue-plugin-host ");
	Args += Quote(Settings.UePluginHost);
	Args += TEXT(" --ue-plugin-port ");
	Args += FString::FromInt(Settings.UePluginPort);

	if (!Settings.ExtraArgs.IsEmpty())
	{
		Args += TEXT(" ");
		Args += Settings.ExtraArgs;
	}

	LastCommandLine = FString::Printf(TEXT("%s %s"), *UvExe, *Args);

	// CreateProc parameters
	const bool bLaunchDetached = true;
	const bool bLaunchHidden = true;
	const bool bLaunchReallyHidden = true;

	ProcHandle = FPlatformProcess::CreateProc(
		*UvExe,
		*Args,
		bLaunchDetached,
		bLaunchHidden,
		bLaunchReallyHidden,
		&ProcId,
		0,
		nullptr,
		nullptr,
		nullptr
	);

	if (!ProcHandle.IsValid())
	{
		ProcId = 0;
		return false;
	}

	return true;
}

void FUE5ProjectAnalyzerMcpLauncher::Stop()
{
	if (!IsRunning())
	{
		ProcId = 0;
		ProcHandle.Reset();
		return;
	}

	FPlatformProcess::TerminateProc(ProcHandle, true);
	FPlatformProcess::CloseProc(ProcHandle);
	ProcHandle.Reset();
	ProcId = 0;
}

bool FUE5ProjectAnalyzerMcpLauncher::IsRunning() const
{
	return ProcHandle.IsValid() && FPlatformProcess::IsProcRunning(ProcHandle);
}

