from __future__ import annotations

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.policy import PolicyManager
from ad_mcp.tools._shared import validate_provider_account


def build_object_tools(
    registry: CapabilityRegistry,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def list_objects(provider: str, account_id: str, object_type: str) -> dict:
        provider_client = registry.get_provider(provider)
        account = validate_provider_account(registry, policy_manager, provider, account_id)
        object_type = provider_client.ensure_valid_object_type(object_type)
        return {
            "provider": provider,
            "account_id": account_id,
            "object_type": object_type,
            "status": "simulated",
            "message": "Object listing is returned as a safe blueprint preview in this version.",
            "available_read_objects": provider_client.capabilities.read_objects,
            "available_write_objects": provider_client.capabilities.write_objects,
            "configured_account": bool(account),
            "sample_query_shape": {
                "provider": provider,
                "account_id": account_id,
                "object_type": object_type,
                "filters": {},
                "fields": [],
                "limit": 100,
            },
        }

    def get_object(provider: str, account_id: str, object_type: str, object_id: str) -> dict:
        provider_client = registry.get_provider(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        object_type = provider_client.ensure_valid_object_type(object_type)
        return {
            "provider": provider,
            "account_id": account_id,
            "object_type": object_type,
            "object_id": object_id,
            "status": "simulated",
            "message": "Direct get_object is scaffolded and returns the provider payload shape that would be used.",
            "provider_payload_shape": provider_client.build_provider_payload(
                action="update",
                account_id=account_id,
                object_type=object_type,
                payload={"id": object_id},
            ),
        }

    def describe_auth(provider: str, account_id: str | None = None) -> dict:
        provider_client = registry.get_provider(provider)
        account_config = provider_client.get_account_config(account_id) if account_id else {}
        non_secret_keys = sorted(
            key for key in account_config.keys() if not any(marker in key.lower() for marker in ("token", "secret", "password", "key"))
        )
        return {
            "provider": provider,
            "configured": bool(account_config),
            "account_id": account_id,
            "config_keys_present": non_secret_keys,
            "notes": provider_client.capabilities.notes,
        }

    return {
        "list_objects": list_objects,
        "get_object": get_object,
        "describe_auth": describe_auth,
    }
