from __future__ import annotations

from ad_mcp.core.capability_registry import CapabilityRegistry


def build_discovery_tools(registry: CapabilityRegistry) -> dict[str, callable]:
    def list_providers() -> list[str]:
        return registry.list_providers()

    def get_provider_capabilities(provider: str) -> dict:
        return registry.get_capabilities(provider).model_dump()

    def list_supported_objects(provider: str) -> dict:
        capabilities = registry.get_capabilities(provider)
        return {
            "provider": provider,
            "read_objects": capabilities.read_objects,
            "write_objects": capabilities.write_objects,
        }

    def list_supported_metrics(provider: str) -> dict:
        capabilities = registry.get_capabilities(provider)
        return {
            "provider": provider,
            "supported_metrics": capabilities.supported_metrics,
            "supported_dimensions": capabilities.supported_dimensions,
        }

    def list_supported_dimensions(provider: str) -> dict:
        capabilities = registry.get_capabilities(provider)
        return {
            "provider": provider,
            "supported_dimensions": capabilities.supported_dimensions,
        }

    def list_supported_campaign_types(provider: str) -> dict:
        capabilities = registry.get_capabilities(provider)
        return {
            "provider": provider,
            "supported_campaign_types": capabilities.supported_campaign_types,
        }

    def list_supported_audience_types(provider: str) -> dict:
        capabilities = registry.get_capabilities(provider)
        return {
            "provider": provider,
            "supported_audience_types": capabilities.supported_audience_types,
        }

    def list_accounts(provider: str) -> list[dict]:
        return [account.model_dump() for account in registry.get_provider(provider).list_accounts()]

    return {
        "list_providers": list_providers,
        "get_provider_capabilities": get_provider_capabilities,
        "list_supported_objects": list_supported_objects,
        "list_supported_metrics": list_supported_metrics,
        "list_supported_dimensions": list_supported_dimensions,
        "list_supported_campaign_types": list_supported_campaign_types,
        "list_supported_audience_types": list_supported_audience_types,
        "list_accounts": list_accounts,
    }
