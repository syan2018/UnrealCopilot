// Copyright Unreal Project Analyzer Team. All Rights Reserved.

using UnrealBuildTool;

public class UnrealProjectAnalyzer : ModuleRules
{
    public UnrealProjectAnalyzer(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "EditorSubsystem",  // Required for UEditorSubsystem base class
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            // HTTP Server
            "HTTP",
            "HTTPServer",

            // JSON
            "Json",
            "JsonUtilities",

            // Editor APIs
            "UnrealEd",
            "BlueprintGraph",
            "Kismet",
            "KismetCompiler",

            // Asset Registry
            "AssetRegistry",
            "AssetTools",

            // Python integration
            "PythonScriptPlugin",

            // Socket probing (to detect MCP server readiness)
            "Sockets",

            // UI / Editor integration (toolbar + settings)
            "ToolMenus",
            "LevelEditor",
            "Slate",
            "SlateCore",
            "Projects",
            "Settings",
            "ApplicationCore",
        });
    }
}
