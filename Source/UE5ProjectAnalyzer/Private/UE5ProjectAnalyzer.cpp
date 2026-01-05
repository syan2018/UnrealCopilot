// Copyright UE5 Project Analyzer Team. All Rights Reserved.

#include "UE5ProjectAnalyzer.h"
#include "HttpServerModule.h"
#include "IHttpRouter.h"
#include "HttpPath.h"
#include "IPythonScriptPlugin.h"
#include "Misc/Paths.h"

#include "UE5AnalyzerHttpRoutes.h"
#include "UE5ProjectAnalyzerMcpLauncher.h"
#include "UE5ProjectAnalyzerSettings.h"

#include "Interfaces/IPluginManager.h"
#include "ToolMenus.h"
#include "LevelEditor.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Framework/Notifications/NotificationManager.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "Misc/MessageDialog.h"
#include "HAL/PlatformApplicationMisc.h"
#include "ISettingsModule.h"

#define LOCTEXT_NAMESPACE "FUE5ProjectAnalyzerModule"

void FUE5ProjectAnalyzerModule::StartupModule()
{
    UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: Starting module..."));

    McpLauncher = new FUE5ProjectAnalyzerMcpLauncher();
    
    // Initialize HTTP server
    InitializeHttpServer();
    
    // Initialize Python bridge
    InitializePythonBridge();

    // Editor integration
    RegisterSettings();
    RegisterMenus();

    // Optional auto-start (only for HTTP/SSE transports; stdio is typically Cursor-managed)
    const UUE5ProjectAnalyzerSettings* Settings = GetDefault<UUE5ProjectAnalyzerSettings>();
    if (Settings && Settings->bAutoStartMcpServer && Settings->Transport != EUE5AnalyzerMcpTransport::Stdio)
    {
        StartMcpServer();
    }
    
    UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: Module started successfully. HTTP API available at port %d"), HttpPort);
}

void FUE5ProjectAnalyzerModule::ShutdownModule()
{
    UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: Shutting down module..."));

    UnregisterMenus();
    UnregisterSettings();

    StopMcpServer();
    delete McpLauncher;
    McpLauncher = nullptr;
    
    ShutdownPythonBridge();
    ShutdownHttpServer();
    
    UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: Module shutdown complete."));
}

FUE5ProjectAnalyzerModule& FUE5ProjectAnalyzerModule::Get()
{
    return FModuleManager::LoadModuleChecked<FUE5ProjectAnalyzerModule>("UE5ProjectAnalyzer");
}

bool FUE5ProjectAnalyzerModule::IsAvailable()
{
    return FModuleManager::Get().IsModuleLoaded("UE5ProjectAnalyzer");
}

void FUE5ProjectAnalyzerModule::InitializeHttpServer()
{
    // Get HTTP server module
    FHttpServerModule& HttpServerModule = FHttpServerModule::Get();
    
    // Start listeners on specified port
    HttpServerModule.StartAllListeners();
    
    // Get router for our port
    HttpRouter = HttpServerModule.GetHttpRouter(HttpPort);
    
    if (HttpRouter.IsValid())
    {
        // Register all routes
        RegisterRoutes(HttpRouter);
        UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: HTTP server initialized on port %d"), HttpPort);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("UE5ProjectAnalyzer: Failed to initialize HTTP server on port %d"), HttpPort);
    }
}

void FUE5ProjectAnalyzerModule::ShutdownHttpServer()
{
    if (HttpRouter.IsValid())
    {
        // Routes will be automatically cleaned up
        HttpRouter.Reset();
    }
}

void FUE5ProjectAnalyzerModule::InitializePythonBridge()
{
    // Check if Python plugin is available
    IPythonScriptPlugin* PythonPlugin = FModuleManager::GetModulePtr<IPythonScriptPlugin>("PythonScriptPlugin");
    
    if (!PythonPlugin)
    {
        UE_LOG(LogTemp, Warning, TEXT("UE5ProjectAnalyzer: PythonScriptPlugin not available. Python bridge disabled."));
        return;
    }
    
    // Get the path to our Python bridge script (do NOT hardcode ProjectPluginsDir / plugin folder name)
    TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("UE5ProjectAnalyzer"));
    const FString PluginDir = Plugin.IsValid() ? Plugin->GetBaseDir() : FPaths::ProjectPluginsDir();
    FString BridgeScriptPath = FPaths::Combine(PluginDir, TEXT("Content/Python/bridge_server.py"));
    
    // Check if script exists
    if (!FPaths::FileExists(BridgeScriptPath))
    {
        UE_LOG(LogTemp, Warning, TEXT("UE5ProjectAnalyzer: Python bridge script not found at %s"), *BridgeScriptPath);
        return;
    }
    
    // Execute the bridge script
    // Note: In production, we'd want more robust error handling
    // Windows paths contain backslashes; escape them for Python string literal.
    BridgeScriptPath.ReplaceInline(TEXT("\\"), TEXT("\\\\"));
    FString PythonCommand = FString::Printf(TEXT("exec(open(r'%s').read())"), *BridgeScriptPath);
    
    // Execute the Python script (best-effort)
    PythonPlugin->ExecPythonCommand(*PythonCommand);
    
    bPythonBridgeInitialized = true;
    UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: Python bridge initialized."));
}

void FUE5ProjectAnalyzerModule::ShutdownPythonBridge()
{
    if (bPythonBridgeInitialized)
    {
        // TODO: Send shutdown signal to Python bridge
        bPythonBridgeInitialized = false;
    }
}

void FUE5ProjectAnalyzerModule::RegisterRoutes(TSharedPtr<IHttpRouter> Router)
{
    if (!Router.IsValid())
    {
        return;
    }
    
    // Health check endpoint
    Router->BindRoute(
        FHttpPath(TEXT("/health")),
        EHttpServerRequestVerbs::VERB_GET,
        [](const FHttpServerRequest& Request, const FHttpResultCallback& OnComplete)
        {
            TUniquePtr<FHttpServerResponse> Response = FHttpServerResponse::Create(
                TEXT("{\"status\": \"ok\", \"service\": \"UE5ProjectAnalyzer\"}"),
                TEXT("application/json")
            );
            OnComplete(MoveTemp(Response));
            return true;
        }
    );

    // Register analyzer API routes.
    // NOTE: For any parameter that contains "/Game/...", we use query params (e.g. ?bp_path=...),
    // to avoid router path-segment matching issues.
    UE5AnalyzerHttpRoutes::Register(Router);
    
    UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: Routes registered."));
}

// ============================================================================
// Settings + Menus
// ============================================================================

void FUE5ProjectAnalyzerModule::RegisterSettings()
{
    ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");
    if (!SettingsModule)
    {
        return;
    }

    SettingsModule->RegisterSettings(
        "Project",
        "Plugins",
        "UE5ProjectAnalyzer",
        LOCTEXT("UE5ProjectAnalyzerSettingsName", "UE5 Project Analyzer"),
        LOCTEXT("UE5ProjectAnalyzerSettingsDesc", "Settings for UE5 Project Analyzer (MCP launcher, transport, and analyzer paths)."),
        GetMutableDefault<UUE5ProjectAnalyzerSettings>()
    );
}

void FUE5ProjectAnalyzerModule::UnregisterSettings()
{
    ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");
    if (!SettingsModule)
    {
        return;
    }

    SettingsModule->UnregisterSettings("Project", "Plugins", "UE5ProjectAnalyzer");
}

void FUE5ProjectAnalyzerModule::RegisterMenus()
{
    if (!UToolMenus::IsToolMenusAvailable())
    {
        return;
    }

    UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateLambda([this]()
    {
        FToolMenuOwnerScoped OwnerScoped(this);

        UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
        if (!Menu)
        {
            return;
        }

        FToolMenuSection& Section = Menu->FindOrAddSection("UE5ProjectAnalyzer");

        // Start
        Section.AddEntry(FToolMenuEntry::InitToolBarButton(
            "UE5ProjectAnalyzer.StartMcp",
            FUIAction(
                FExecuteAction::CreateRaw(this, &FUE5ProjectAnalyzerModule::StartMcpServer),
                FCanExecuteAction::CreateRaw(this, &FUE5ProjectAnalyzerModule::CanStartMcpServer)
            ),
            LOCTEXT("StartMcp_Label", "Start MCP"),
            LOCTEXT("StartMcp_Tooltip", "Start MCP Server via uv (HTTP/SSE transport recommended for quick connect)."),
            FSlateIcon()
        ));

        // Stop
        Section.AddEntry(FToolMenuEntry::InitToolBarButton(
            "UE5ProjectAnalyzer.StopMcp",
            FUIAction(
                FExecuteAction::CreateRaw(this, &FUE5ProjectAnalyzerModule::StopMcpServer),
                FCanExecuteAction::CreateRaw(this, &FUE5ProjectAnalyzerModule::CanStopMcpServer)
            ),
            LOCTEXT("StopMcp_Label", "Stop MCP"),
            LOCTEXT("StopMcp_Tooltip", "Stop MCP Server process."),
            FSlateIcon()
        ));

        // Copy URL
        Section.AddEntry(FToolMenuEntry::InitToolBarButton(
            "UE5ProjectAnalyzer.CopyMcpUrl",
            FUIAction(
                FExecuteAction::CreateRaw(this, &FUE5ProjectAnalyzerModule::CopyMcpUrlToClipboard),
                FCanExecuteAction::CreateRaw(this, &FUE5ProjectAnalyzerModule::CanStopMcpServer) // running => can copy
            ),
            LOCTEXT("CopyMcpUrl_Label", "Copy MCP URL"),
            LOCTEXT("CopyMcpUrl_Tooltip", "Copy MCP URL to clipboard (HTTP/SSE only)."),
            FSlateIcon()
        ));

        // Settings
        Section.AddEntry(FToolMenuEntry::InitToolBarButton(
            "UE5ProjectAnalyzer.OpenSettings",
            FUIAction(FExecuteAction::CreateRaw(this, &FUE5ProjectAnalyzerModule::OpenPluginSettings)),
            LOCTEXT("OpenSettings_Label", "MCP Settings"),
            LOCTEXT("OpenSettings_Tooltip", "Open UE5 Project Analyzer settings."),
            FSlateIcon()
        ));
    }));
}

void FUE5ProjectAnalyzerModule::UnregisterMenus()
{
    if (UToolMenus::IsToolMenusAvailable())
    {
        UToolMenus::UnregisterOwner(this);
    }
}

bool FUE5ProjectAnalyzerModule::CanStartMcpServer() const
{
    return McpLauncher && !McpLauncher->IsRunning();
}

bool FUE5ProjectAnalyzerModule::CanStopMcpServer() const
{
    return McpLauncher && McpLauncher->IsRunning();
}

void FUE5ProjectAnalyzerModule::StartMcpServer()
{
    if (!McpLauncher)
    {
        return;
    }

    const UUE5ProjectAnalyzerSettings* Settings = GetDefault<UUE5ProjectAnalyzerSettings>();
    if (!Settings)
    {
        return;
    }

    const bool bOk = McpLauncher->Start(*Settings);
    if (!bOk)
    {
        const FText Msg = LOCTEXT("McpStartFailed", "Failed to start MCP Server. Please ensure `uv` is installed and configured in settings.");
        FMessageDialog::Open(EAppMsgType::Ok, Msg);
        UE_LOG(LogTemp, Error, TEXT("UE5ProjectAnalyzer: Failed to start MCP server. cmd=%s"), *McpLauncher->GetLastCommandLine());
        return;
    }

    const FString Url = McpLauncher->GetMcpUrl();
    UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: MCP server started. %s"), *McpLauncher->GetLastCommandLine());
    if (!Url.IsEmpty())
    {
        UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: MCP URL: %s"), *Url);
    }

    FNotificationInfo Info(LOCTEXT("McpStarted", "MCP Server started"));
    Info.ExpireDuration = 3.0f;
    FSlateNotificationManager::Get().AddNotification(Info);
}

void FUE5ProjectAnalyzerModule::StopMcpServer()
{
    if (!McpLauncher)
    {
        return;
    }

    if (McpLauncher->IsRunning())
    {
        McpLauncher->Stop();
        UE_LOG(LogTemp, Log, TEXT("UE5ProjectAnalyzer: MCP server stopped."));

        FNotificationInfo Info(LOCTEXT("McpStopped", "MCP Server stopped"));
        Info.ExpireDuration = 3.0f;
        FSlateNotificationManager::Get().AddNotification(Info);
    }
}

void FUE5ProjectAnalyzerModule::CopyMcpUrlToClipboard() const
{
    if (!McpLauncher || !McpLauncher->IsRunning())
    {
        return;
    }

    const FString Url = McpLauncher->GetMcpUrl();
    if (Url.IsEmpty())
    {
        FNotificationInfo Info(LOCTEXT("McpUrlEmpty", "MCP URL is empty (transport is likely stdio)."));
        Info.ExpireDuration = 3.0f;
        FSlateNotificationManager::Get().AddNotification(Info);
        return;
    }

    FPlatformApplicationMisc::ClipboardCopy(*Url);
    FNotificationInfo Info(LOCTEXT("McpUrlCopied", "MCP URL copied to clipboard"));
    Info.ExpireDuration = 2.0f;
    FSlateNotificationManager::Get().AddNotification(Info);
}

void FUE5ProjectAnalyzerModule::OpenPluginSettings() const
{
    ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");
    if (SettingsModule)
    {
        SettingsModule->ShowViewer("Project", "Plugins", "UE5ProjectAnalyzer");
    }
}

#undef LOCTEXT_NAMESPACE
    
IMPLEMENT_MODULE(FUE5ProjectAnalyzerModule, UE5ProjectAnalyzer)
