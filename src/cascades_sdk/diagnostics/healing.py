"""
Auto-healing capabilities for the Cascades developer tooling.

When diagnostics detect an issue, the healing module attempts to
automatically repair it. Each healer targets a specific problem
and reports whether the repair succeeded.
"""


import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .._meta import SDK_AUTH_URL, SDK_DOCS_URL, SDK_GETTING_STARTED_URL


@dataclass
class HealResult:
    healer_name: str
    success: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class BaseHealer:
    name: str = ""
    description: str = ""

    def can_heal(self, diagnostic_result: Any) -> bool:
        raise NotImplementedError

    def heal(self, context: Dict[str, Any]) -> HealResult:
        raise NotImplementedError


class SessionRefreshHealer(BaseHealer):
    """Guide the user through refreshing their authentication session."""

    name = "session_refresh"
    description = "Refresh expired authentication tokens"

    def can_heal(self, result: Any) -> bool:
        return getattr(result, "check_name", "") == "authentication" and getattr(result, "status", "") == "failed"

    def heal(self, context: Dict[str, Any]) -> HealResult:
        return HealResult(
            healer_name=self.name,
            success=False,
            message="Session cookie expired. Please re-authenticate.",
            details={
                "action": "open_url",
                "url": SDK_AUTH_URL,
                "instructions": "Log into your Cascades deployment and copy the new __session cookie.",
            },
        )


class BaseUrlHealer(BaseHealer):
    """Auto-correct common base URL mistakes."""

    name = "base_url_fix"
    description = "Correct common base URL misconfigurations"

    COMMON_MISTAKES = {
        "http:/": "http://",
        "https:/": "https://",
        "cascades.work": "https://cascades.work",
        "localhost:3102": "http://localhost:3102",
        "localhost": "http://localhost:3102",
    }

    def can_heal(self, result: Any) -> bool:
        if getattr(result, "check_name", "") != "configuration":
            return False
        msg = getattr(result, "message", "")
        return "base_url" in msg

    def heal(self, context: Dict[str, Any]) -> HealResult:
        base_url = context.get("base_url", "")
        corrected = base_url
        for mistake, fix in self.COMMON_MISTAKES.items():
            if corrected.startswith(mistake):
                corrected = corrected.replace(mistake, fix, 1)
                break

        if corrected == base_url and not base_url.startswith("http"):
            corrected = f"https://{base_url}"

        if corrected != base_url:
            return HealResult(
                healer_name=self.name,
                success=True,
                message=f"Corrected base_url: '{base_url}' → '{corrected}'",
                details={"old_value": base_url, "new_value": corrected, "action": "update_config", "key": "base_url"},
            )

        return HealResult(
            healer_name=self.name,
            success=False,
            message=f"Could not auto-correct base_url: '{base_url}'",
            details={"action": "manual", "url": f"{SDK_DOCS_URL}/configuration"},
        )


class VersionUpgradeHealer(BaseHealer):
    """Recommend SDK/extension version upgrades when outdated."""

    name = "version_upgrade"
    description = "Detect and recommend version upgrades"

    def can_heal(self, result: Any) -> bool:
        return getattr(result, "check_name", "") == "version_compatibility" and getattr(result, "status", "") == "warning"

    def heal(self, context: Dict[str, Any]) -> HealResult:
        return HealResult(
            healer_name=self.name,
            success=False,
            message="Version mismatch detected. Upgrade recommendation available.",
            details={
                "action": "open_url",
                "url": "https://pypi.org/project/cascades-sdk/",
                "pip_command": "pip install --upgrade cascades-sdk",
            },
        )


class HealingEngine:
    """Runs healers against diagnostic results."""

    def __init__(self, healers: Optional[List[BaseHealer]] = None):
        self.healers = healers or [
            SessionRefreshHealer(),
            BaseUrlHealer(),
            VersionUpgradeHealer(),
        ]

    def heal_all(self, results: List[Any], context: Dict[str, Any]) -> List[HealResult]:
        outcomes = []
        for result in results:
            for healer in self.healers:
                if healer.can_heal(result):
                    outcome = healer.heal(context)
                    outcomes.append(outcome)
        return outcomes
