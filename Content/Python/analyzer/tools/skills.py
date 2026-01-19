from __future__ import annotations

from typing import Any, Dict, Optional

from ..skills.runner import SkillRunner

_runner = SkillRunner()


def list_unreal_skill(query: Optional[str] = None) -> Dict[str, Any]:
    try:
        return _runner.list_skills(query=query)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def read_unreal_skill(skill_name: str, path: Optional[str] = None) -> Dict[str, Any]:
    try:
        return _runner.read_skill(skill_name=skill_name, path=path)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def run_unreal_skill(
    *,
    skill_name: Optional[str] = None,
    script: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None,
    python: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        if python is not None and python.strip():
            return _runner.run_inline_python(python_code=python, args=args)

        if not skill_name:
            return {"ok": False, "error": "skill_name is required when running a skill script"}
        if not script:
            return {"ok": False, "error": "script is required when running a skill script"}

        return _runner.run_script(skill_name=skill_name, script=script, args=args)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

