// Copyright Unreal Project Analyzer Team. All Rights Reserved.

#include "CppSkillApiSubsystem.h"

#include "Editor.h"

UCppSkillApiSubsystem* UCppSkillApiSubsystem::Get()
{
    return GEditor ? GEditor->GetEditorSubsystem<UCppSkillApiSubsystem>() : nullptr;
}

