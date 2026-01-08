// Copyright Unreal Project Analyzer Team. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"
#include "UnrealProjectAnalyzerSettings.h"
#include "AnalyzerSubsystem.generated.h"

/**
 * Unreal Project Analyzer Subsystem
 *
 * Manages the lifecycle of the MCP analyzer server running inside UE's Python environment.
 * Provides blueprint functions and editor commands to control the analyzer.
 */
UCLASS()
class UNREALPROJECTANALYZER_API UAnalyzerSubsystem : public UEditorSubsystem, public FTickableGameObject
{
    GENERATED_BODY()

public:
    // ============================================================================
    // UEditorSubsystem interface
    // ============================================================================

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    // ============================================================================
    // FTickableGameObject interface
    // ============================================================================

    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override
    {
        RETURN_QUICK_DECLARE_CYCLE_STAT(UAnalyzerSubsystem, STATGROUP_Tickables);
    }
    virtual bool IsTickable() const override { return true; }
    virtual bool IsTickableInEditor() const override { return true; }
    virtual ETickableTickType GetTickableTickType() const override
    {
        return ETickableTickType::Always;
    }

    // ============================================================================
    // Blueprint API
    // ============================================================================

    /**
     * Start the MCP analyzer server.
     * The server will run in a background thread inside UE's Python environment.
     */
    UFUNCTION(BlueprintCallable, Category = "UnrealProjectAnalyzer|Analyzer")
    void StartAnalyzer();

    /**
     * Stop the MCP analyzer server.
     */
    UFUNCTION(BlueprintCallable, Category = "UnrealProjectAnalyzer|Analyzer")
    void StopAnalyzer();

    /**
     * Check if the analyzer server is running.
     */
    UFUNCTION(BlueprintCallable, Category = "UnrealProjectAnalyzer|Analyzer")
    bool IsAnalyzerRunning() const;

    /**
     * Check if the analyzer server is starting (HTTP/SSE port not ready yet).
     */
    UFUNCTION(BlueprintCallable, Category = "UnrealProjectAnalyzer|Analyzer")
    bool IsAnalyzerStarting() const;

    /**
     * Get the singleton instance of the subsystem.
     */
    UFUNCTION(BlueprintCallable, Category = "UnrealProjectAnalyzer|Analyzer")
    static UAnalyzerSubsystem* Get();

    // ============================================================================
    // Internal API
    // ============================================================================

    /** Check if Python is available and initialized */
    bool IsPythonAvailable() const;

    /** Initialize the Python bridge (executes init_analyzer.py) */
    void InitializePythonBridge();

private:
    /** Whether the Python bridge has been initialized */
    bool bPythonBridgeInitialized = false;

    /** Whether the analyzer server is currently running */
    bool bAnalyzerRunning = false;

    /** Whether a start request is in progress */
    bool bAnalyzerStarting = false;

    /** Whether a stop request is in progress */
    bool bAnalyzerStopRequested = false;

    /** Stop request warning printed */
    bool bStopWarned = false;

    /** Last MCP transport used */
    EUnrealAnalyzerMcpTransport LastTransport = EUnrealAnalyzerMcpTransport::Http;

    /** Last MCP host used */
    FString LastMcpHost;

    /** Last MCP port used */
    int32 LastMcpPort = 0;

    /** Timestamp (seconds) when start was requested */
    double StartRequestedAtSeconds = 0.0;

    /** Timestamp (seconds) when stop was requested */
    double StopRequestedAtSeconds = 0.0;
};
