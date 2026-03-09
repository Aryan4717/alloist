"""Enforcement SDK: token+policy check with local verify, remote fallback, revocation listener."""

from __future__ import annotations

import uuid
from typing import Any, Callable

from . import api, evidence, jwt, policy, policy_service, websocket_


def _resolve_fail_mode(
    action_name: str,
    fail_mode: str,
    fail_mode_per_action: dict[str, str] | None,
    fail_closed: bool,
    high_risk_actions: list[str],
) -> str:
    """Resolve fail mode for an action. Backward compat: fail_closed + high_risk_actions."""
    if fail_mode_per_action is not None and action_name in fail_mode_per_action:
        return fail_mode_per_action[action_name]
    if fail_mode_per_action is not None:
        return fail_mode
    if fail_closed and action_name in high_risk_actions:
        return "fail_closed"
    return "fail_open"


def create_enforcement(
    api_url: str = "http://localhost:8000",
    api_key: str = "",
    policy_service_url: str | None = None,
    policy_service_api_key: str = "",
    fail_closed: bool = False,
    high_risk_actions: list[str] | None = None,
    fail_mode: str = "fail_open",
    fail_mode_per_action: dict[str, str] | None = None,
    on_log: Callable[[dict], None] | None = None,
    jwks_override: dict[str, Any] | None = None,
    _test_revoked_tokens: set[str] | None = None,
) -> object:
    """
    Create enforcement instance. Returns object with check(token, action_name, metadata) and close().
    fail_mode: default when backend unreachable (fail_closed, soft_fail, fail_open).
    fail_mode_per_action: override per action. Backward compat: fail_closed=True uses high_risk_actions.
    """
    if high_risk_actions is None:
        high_risk_actions = ["send_email", "delete_user", "transfer_funds"]

    revoked_tokens: set[str] = _test_revoked_tokens if _test_revoked_tokens is not None else set()
    cache: dict[str, dict] = {}

    def on_revoked(token_id: str) -> None:
        revoked_tokens.add(token_id)
        if on_log:
            on_log({"type": "revocation", "token_id": token_id})

    ws = websocket_.create_revocation_listener(api_url, on_revoked)

    class Enforcement:
        def check(
            self,
            token: str,
            action_name: str,
            metadata: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            """
            Check token and policy. Returns {allowed: bool, reason?: str, evidence_id: str}.
            """
            evidence_id = str(uuid.uuid4())

            def log(payload: dict) -> None:
                if on_log:
                    on_log({"evidence_id": evidence_id, **payload})

            try:
                # 1. Local validation
                local = jwt.verify_token_locally(token, api_url, jwks_override)
                if not local.get("valid"):
                    reason = local.get("reason", "invalid_token")
                    log({"action": action_name, "result": "blocked", "reason": reason})
                    return {"allowed": False, "reason": reason, "evidence_id": evidence_id}

                jti = local.get("jti", "")
                scopes = local.get("scopes", [])

                # 2. Revocation cache
                if jti in revoked_tokens:
                    log({"action": action_name, "result": "blocked", "reason": "token_revoked"})
                    return {"allowed": False, "reason": "token_revoked", "evidence_id": evidence_id}

                # 3. Remote fallback
                status = cache.get(jti, {}).get("status")
                if status is None:
                    remote = api.validate_token_remote(token, api_url, api_key)
                    if remote:
                        status = remote["status"]
                        cache[jti] = {
                            "status": status,
                            "subject": remote.get("subject", ""),
                            "scopes": remote.get("scopes", []),
                        }
                        if status == "revoked":
                            revoked_tokens.add(jti)
                            log({"action": action_name, "result": "blocked", "reason": "token_revoked"})
                            return {"allowed": False, "reason": "token_revoked", "evidence_id": evidence_id}
                    else:
                        mode = _resolve_fail_mode(
                            action_name, fail_mode, fail_mode_per_action, fail_closed, high_risk_actions
                        )
                        if mode == "fail_closed":
                            log({
                                "action": action_name,
                                "result": "blocked",
                                "reason": "fail_closed_backend_unreachable",
                            })
                            return {
                                "allowed": False,
                                "reason": "fail_closed_backend_unreachable",
                                "evidence_id": evidence_id,
                            }
                        if mode == "soft_fail" and policy_service_url:
                            token_snapshot = evidence.get_token_snapshot(token, jti, scopes)
                            evidence.create_evidence_remote(
                                evidence_id=evidence_id,
                                action_name=action_name,
                                token_snapshot=token_snapshot,
                                policy_id=None,
                                result="allow",
                                runtime_metadata={
                                    "severity": "high",
                                    "degraded_mode": "soft_fail",
                                    "reason": "backend_unreachable",
                                },
                                policy_service_url=policy_service_url,
                                api_key=policy_service_api_key,
                            )
                            log({"action": action_name, "result": "allowed", "degraded_mode": "soft_fail"})

                # 4. Policy service check (when configured)
                if policy_service_url:
                    if "." in action_name:
                        service, name = action_name.split(".", 1)
                    else:
                        service, name = "", action_name
                    action_payload = {
                        "service": service,
                        "name": name,
                        "metadata": metadata or {},
                    }
                    ps_result = policy_service.evaluate_remote(
                        token_id=jti,
                        action=action_payload,
                        policy_service_url=policy_service_url,
                        api_key=policy_service_api_key,
                    )
                    if ps_result is not None and not ps_result.get("allowed"):
                        reason = ps_result.get("reason", "policy_denied")
                        policy_id = ps_result.get("policy_id")
                        token_snapshot = evidence.get_token_snapshot(token, jti, scopes)
                        evidence.create_evidence_remote(
                            evidence_id=evidence_id,
                            action_name=action_name,
                            token_snapshot=token_snapshot,
                            policy_id=str(policy_id) if policy_id else None,
                            result="deny",
                            runtime_metadata={"reason": reason},
                            policy_service_url=policy_service_url,
                            api_key=policy_service_api_key,
                        )
                        log({"action": action_name, "result": "blocked", "reason": reason})
                        return {"allowed": False, "reason": reason, "evidence_id": evidence_id}
                    if ps_result is None:
                        mode = _resolve_fail_mode(
                            action_name, fail_mode, fail_mode_per_action, fail_closed, high_risk_actions
                        )
                        if mode == "fail_closed":
                            log({
                                "action": action_name,
                                "result": "blocked",
                                "reason": "fail_closed_backend_unreachable",
                            })
                            return {
                                "allowed": False,
                                "reason": "fail_closed_backend_unreachable",
                                "evidence_id": evidence_id,
                            }
                        if mode == "soft_fail":
                            token_snapshot = evidence.get_token_snapshot(token, jti, scopes)
                            evidence.create_evidence_remote(
                                evidence_id=evidence_id,
                                action_name=action_name,
                                token_snapshot=token_snapshot,
                                policy_id=None,
                                result="allow",
                                runtime_metadata={
                                    "severity": "high",
                                    "degraded_mode": "soft_fail",
                                    "reason": "backend_unreachable",
                                },
                                policy_service_url=policy_service_url,
                                api_key=policy_service_api_key,
                            )
                            log({"action": action_name, "result": "allowed", "degraded_mode": "soft_fail"})

                # 5. Local policy check
                policy_result = policy.check_policy(action_name, scopes)
                if not policy_result.get("allowed"):
                    reason = policy_result.get("reason", "policy_denied")
                    log({"action": action_name, "result": "blocked", "reason": reason})
                    return {"allowed": False, "reason": reason, "evidence_id": evidence_id}

                # 6. Fail-closed: re-check revoked before returning allowed (in-flight revocation)
                if jti in revoked_tokens:
                    log({"action": action_name, "result": "blocked", "reason": "token_revoked"})
                    return {"allowed": False, "reason": "token_revoked", "evidence_id": evidence_id}

                log({"action": action_name, "result": "allowed"})
                return {"allowed": True, "evidence_id": evidence_id}

            except Exception as err:
                mode = _resolve_fail_mode(
                    action_name, fail_mode, fail_mode_per_action, fail_closed, high_risk_actions
                )
                if mode == "fail_closed":
                    log({"action": action_name, "result": "blocked", "reason": str(err)})
                    return {"allowed": False, "reason": str(err), "evidence_id": evidence_id}
                raise

        def close(self) -> None:
            ws.close()

    return Enforcement()
