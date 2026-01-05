// Copyright UE5 Project Analyzer Team. All Rights Reserved.
//
// HTTP route registration for UE5ProjectAnalyzer.

#pragma once

#include "CoreMinimal.h"

class IHttpRouter;

namespace UE5AnalyzerHttpRoutes
{
	/** Bind all HTTP routes to the provided router. */
	void Register(TSharedPtr<IHttpRouter> Router);
}

