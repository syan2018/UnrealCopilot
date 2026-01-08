// Copyright Unreal Project Analyzer Team. All Rights Reserved.

#include "AnalyzerSubsystem.h"
#include "UnrealProjectAnalyzerSettings.h"

#include "Interfaces/IPluginManager.h"
#include "IPythonScriptPlugin.h"
#include "Misc/Paths.h"
#include "Sockets.h"
#include "SocketSubsystem.h"

// Define logging category
DEFINE_LOG_CATEGORY_STATIC(LogAnalyzerSubsystem, Log, All);

static bool IsTcpPortOpen(const FString& Host, int32 Port)
{
    if (Host.IsEmpty() || Port <= 0)
    {
        return false;
    }

    ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
    if (!SocketSubsystem)
    {
        return false;
    }

    TSharedRef<FInternetAddr> Addr = SocketSubsystem->CreateInternetAddr();
    bool bIsValid = false;
    Addr->SetIp(*Host, bIsValid);
    Addr->SetPort(Port);
    if (!bIsValid)
    {
        return false;
    }

    FSocket* Socket = SocketSubsystem->CreateSocket(NAME_Stream, TEXT("UnrealProjectAnalyzer_McpProbe"), false);
    if (!Socket)
    {
        return false;
    }

    // Best-effort: local connect should be fast; keep it simple.
    const bool bConnected = Socket->Connect(*Addr);
    Socket->Close();
    SocketSubsystem->DestroySocket(Socket);
    return bConnected;
}

void UAnalyzerSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("UnrealProjectAnalyzer Subsystem initialized"));

    // Check if Python is available
    if (!IsPythonAvailable())
    {
        UE_LOG(LogAnalyzerSubsystem, Warning, TEXT("Python is not available. UnrealProjectAnalyzer will not work."));
        return;
    }

    // Wait for Python to be initialized, then set up the bridge
#if ENGINE_MINOR_VERSION >= 7
    if (IPythonScriptPlugin::Get()->IsPythonInitialized())
    {
        InitializePythonBridge();
    }
    else
    {
        IPythonScriptPlugin::Get()->OnPythonInitialized().AddUObject(this, &UAnalyzerSubsystem::InitializePythonBridge);
    }
#else
    // For older engine versions, we need to use the editor initialized delegate
    FEditorDelegates::OnEditorInitialized.AddLambda([this](double)
    {
        InitializePythonBridge();
    });
#endif

    // Auto-start if enabled in settings
    const UUnrealProjectAnalyzerSettings* Settings = GetDefault<UUnrealProjectAnalyzerSettings>();
    if (Settings && Settings->bAutoStartMcpServer)
    {
        StartAnalyzer();
    }
}

void UAnalyzerSubsystem::Deinitialize()
{
    StopAnalyzer();
    Super::Deinitialize();
}

void UAnalyzerSubsystem::Tick(float DeltaTime)
{
    if (LastTransport == EUnrealAnalyzerMcpTransport::Stdio)
    {
        return;
    }

    // If we have host/port, probe readiness.
    const bool bPortOpen = IsTcpPortOpen(LastMcpHost, LastMcpPort);
    const double Now = FPlatformTime::Seconds();

    if (bAnalyzerStarting)
    {
        if (bPortOpen)
        {
            bAnalyzerStarting = false;
            bAnalyzerRunning = true;
            UE_LOG(LogAnalyzerSubsystem, Log, TEXT("MCP server is now listening on %s:%d"), *LastMcpHost, LastMcpPort);
        }
        else if (Now - StartRequestedAtSeconds > 30.0)
        {
            bAnalyzerStarting = false;
            UE_LOG(LogAnalyzerSubsystem, Error, TEXT("MCP server start timed out (no listener on %s:%d)"), *LastMcpHost, LastMcpPort);
        }
    }

    if (bAnalyzerStopRequested)
    {
        if (!bPortOpen)
        {
            bAnalyzerStopRequested = false;
            bStopWarned = false;
            bAnalyzerRunning = false;
            UE_LOG(LogAnalyzerSubsystem, Log, TEXT("MCP server stopped (port closed)"));
        }
        else if (!bStopWarned && (Now - StopRequestedAtSeconds > 5.0))
        {
            bStopWarned = true;
            UE_LOG(LogAnalyzerSubsystem, Warning, TEXT("Stop requested but MCP port still open (%s:%d). Server may not support graceful shutdown yet."), *LastMcpHost, LastMcpPort);
        }
    }

    // Keep running state aligned with actual listener.
    if (bAnalyzerRunning && !bPortOpen && !bAnalyzerStopRequested && !bAnalyzerStarting)
    {
        bAnalyzerRunning = false;
        UE_LOG(LogAnalyzerSubsystem, Warning, TEXT("MCP server no longer listening on %s:%d"), *LastMcpHost, LastMcpPort);
    }
}

void UAnalyzerSubsystem::StartAnalyzer()
{
    if (!IsPythonAvailable())
    {
        UE_LOG(LogAnalyzerSubsystem, Error, TEXT("Cannot start analyzer: Python is not available"));
        return;
    }

    if (bAnalyzerRunning || bAnalyzerStarting)
    {
        UE_LOG(LogAnalyzerSubsystem, Warning, TEXT("Analyzer is already running or starting"));
        return;
    }

    if (!bPythonBridgeInitialized)
    {
        UE_LOG(LogAnalyzerSubsystem, Warning, TEXT("Python bridge not initialized. Attempting to initialize..."));
        InitializePythonBridge();

        if (!bPythonBridgeInitialized)
        {
            UE_LOG(LogAnalyzerSubsystem, Error, TEXT("Failed to initialize Python bridge. Cannot start analyzer."));
            return;
        }
    }

    // Get settings
    const UUnrealProjectAnalyzerSettings* Settings = GetDefault<UUnrealProjectAnalyzerSettings>();
    if (!Settings)
    {
        UE_LOG(LogAnalyzerSubsystem, Error, TEXT("Failed to get UnrealProjectAnalyzer settings"));
        return;
    }

    // Build Python command to start the analyzer
    FString TransportStr;
    switch (Settings->Transport)
    {
    case EUnrealAnalyzerMcpTransport::Stdio:
        TransportStr = TEXT("stdio");
        break;
    case EUnrealAnalyzerMcpTransport::Sse:
        TransportStr = TEXT("sse");
        break;
    case EUnrealAnalyzerMcpTransport::Http:
    default:
        TransportStr = TEXT("http");
        break;
    }

    // Prepare paths
    FString CppSourcePath = Settings->CppSourcePath;
    if (CppSourcePath.IsEmpty())
    {
        CppSourcePath = FPaths::Combine(FPaths::ProjectDir(), TEXT("Source"));
    }

    FString EngineSourcePath = Settings->UnrealEngineSourcePath;
    if (EngineSourcePath.IsEmpty())
    {
        EngineSourcePath = FPaths::EngineSourceDir();
    }

    // Execute Python command to start the server
    FString PythonCommand = FString::Printf(
        TEXT("import init_analyzer; init_analyzer.start_analyzer_server("
             "transport='%s', host='%s', port=%d, path='%s', "
             "cpp_source_path='%s', unreal_engine_path='%s')"),
        *TransportStr,
        *Settings->McpHost,
        Settings->McpPort,
        *Settings->McpPath,
        *CppSourcePath,
        *EngineSourcePath
    );

    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("Starting MCP analyzer server..."));
    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("Transport: %s, Host: %s, Port: %d"),
        *TransportStr, *Settings->McpHost, Settings->McpPort);

    IPythonScriptPlugin::Get()->ExecPythonCommand(*PythonCommand);

    // Track state for UI feedback.
    LastTransport = Settings->Transport;
    LastMcpHost = Settings->McpHost;
    LastMcpPort = Settings->McpPort;
    StartRequestedAtSeconds = FPlatformTime::Seconds();

    if (Settings->Transport == EUnrealAnalyzerMcpTransport::Stdio)
    {
        bAnalyzerRunning = true;
        bAnalyzerStarting = false;
    }
    else
    {
        bAnalyzerRunning = false;
        bAnalyzerStarting = true;
    }

    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("MCP analyzer server start requested (check Python log for result)"));
}

void UAnalyzerSubsystem::StopAnalyzer()
{
    if (!bAnalyzerRunning && !bAnalyzerStarting)
    {
        return;
    }

    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("Stopping MCP analyzer server..."));

    // Execute Python command to stop the server
    FString PythonCommand = TEXT("import init_analyzer; init_analyzer.stop_analyzer_server()");
    IPythonScriptPlugin::Get()->ExecPythonCommand(*PythonCommand);

    bAnalyzerStarting = false;
    bAnalyzerStopRequested = true;
    bStopWarned = false;
    StopRequestedAtSeconds = FPlatformTime::Seconds();

    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("MCP analyzer server stop requested"));
}

bool UAnalyzerSubsystem::IsAnalyzerRunning() const
{
    return bAnalyzerRunning;
}

bool UAnalyzerSubsystem::IsAnalyzerStarting() const
{
    return bAnalyzerStarting;
}

UAnalyzerSubsystem* UAnalyzerSubsystem::Get()
{
    return GEditor ? GEditor->GetEditorSubsystem<UAnalyzerSubsystem>() : nullptr;
}

bool UAnalyzerSubsystem::IsPythonAvailable() const
{
#if ENGINE_MINOR_VERSION >= 7
    return IPythonScriptPlugin::Get() != nullptr;
#else
    // For older engine versions, check if the plugin is available
    return FModuleManager::Get().IsModuleLoaded("PythonScriptPlugin");
#endif
}

void UAnalyzerSubsystem::InitializePythonBridge()
{
    if (!IsPythonAvailable())
    {
        UE_LOG(LogAnalyzerSubsystem, Error, TEXT("Python is not available"));
        return;
    }

    if (bPythonBridgeInitialized)
    {
        return;
    }

    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("Initializing Python bridge..."));

    // Get the plugin directory
    FString PluginDir = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectPluginsDir(), TEXT("UnrealProjectAnalyzer"))
    );

    // Check if we're in a development build (plugin might be in a different location)
    if (!FPaths::DirectoryExists(PluginDir))
    {
        // Try to find the plugin via the plugin manager
        if (IPluginManager::Get().FindPlugin(TEXT("UnrealProjectAnalyzer")))
        {
            PluginDir = IPluginManager::Get().FindPlugin(TEXT("UnrealProjectAnalyzer"))->GetBaseDir();
        }
        else
        {
            UE_LOG(LogAnalyzerSubsystem, Error, TEXT("Failed to locate UnrealProjectAnalyzer plugin directory"));
            return;
        }
    }

    // Add the Content/Python directory to sys.path
    FString PythonInitScript = FPaths::Combine(PluginDir, TEXT("Content/Python"));

    // Execute the initialization script
    FString PythonCommand = FString::Printf(
        TEXT("import sys; sys.path.insert(0, r'%s'); import init_analyzer"),
        *PythonInitScript
    );

    IPythonScriptPlugin::Get()->ExecPythonCommand(*PythonCommand);

    bPythonBridgeInitialized = true;

    UE_LOG(LogAnalyzerSubsystem, Log, TEXT("Python bridge initialized"));
}
