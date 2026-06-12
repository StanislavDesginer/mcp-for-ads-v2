class AdMCPError(Exception):
    """Base application error."""


class ProviderNotFoundError(AdMCPError):
    """Raised when provider is missing from the registry."""


class PreviewNotFoundError(AdMCPError):
    """Raised when a preview token is invalid or expired."""


class PolicyViolationError(AdMCPError):
    """Raised when a request violates the configured safety policy."""


class ValidationError(AdMCPError):
    """Raised when a request is invalid for the selected provider."""


class OAuthError(AdMCPError):
    """Raised when OAuth authorization, callback, or account selection fails."""


class ProviderApiError(AdMCPError):
    """Raised when a provider read API request fails."""


class TokenExpiredError(AdMCPError):
    """Raised when stored OAuth credentials are expired or no longer usable."""


class MissingEnvError(AdMCPError):
    """Raised when required environment variables are missing."""


class NoAccountsSelectedError(AdMCPError):
    """Raised when OAuth succeeded but no ad accounts are selected."""


class McpTransportError(AdMCPError):
    """Raised when hosted MCP transport is unavailable or misconfigured."""


class PreviewOnlyBlockedError(AdMCPError):
    """Raised when a write/apply action is blocked by preview-only mode."""


def normalize_error(exc: Exception) -> dict:
    error_type = type(exc).__name__
    code_map = {
        "OAuthError": "oauth_error",
        "MetaOAuthError": "oauth_error",
        "PartnerOAuthError": "oauth_error",
        "ProviderApiError": "provider_api_error",
        "TokenExpiredError": "token_expired",
        "MissingEnvError": "missing_env",
        "NoAccountsSelectedError": "no_accounts_selected",
        "McpTransportError": "mcp_transport_error",
        "PreviewOnlyBlockedError": "preview_only_blocked",
        "PolicyViolationError": "preview_only_blocked",
        "ProviderNotFoundError": "provider_not_found",
        "ValidationError": "validation_error",
        "PreviewNotFoundError": "preview_not_found",
    }
    return {
        "type": error_type,
        "code": code_map.get(error_type, "provider_api_error" if "api" in error_type.lower() else "unknown_error"),
        "message": str(exc) or error_type,
    }
