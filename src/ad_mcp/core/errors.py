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
