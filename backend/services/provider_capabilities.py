"""Provider capability registry used before any external AI request."""

from __future__ import annotations


class ProviderCapabilityError(ValueError):
    """Raised when a provider is unknown or does not support a requested capability."""


PROVIDER_CAPABILITIES: dict[str, frozenset[str]] = {
    "featherless": frozenset({"text"}),
    "aimlapi": frozenset({"text", "image"}),
}

_PROVIDER_ALIASES = {
    "featherless_ai": "featherless",
    "featherless ai": "featherless",
    "aiml": "aimlapi",
    "aiml_api": "aimlapi",
    "aiml api": "aimlapi",
}


def normalize_provider_type(provider_type: str) -> str:
    normalized = (provider_type or "").strip().lower()
    return _PROVIDER_ALIASES.get(normalized, normalized)


def validate_provider_capability(provider_type: str, capability: str) -> str:
    """Return the canonical provider name or reject before a network request."""
    provider = normalize_provider_type(provider_type)
    requested = capability.strip().lower()
    supported = PROVIDER_CAPABILITIES.get(provider)
    if supported is None:
        raise ProviderCapabilityError(f"Unknown AI provider: {provider_type!r}")
    if requested not in supported:
        raise ProviderCapabilityError(
            f"Provider '{provider}' does not support {requested} generation. "
            f"Supported capabilities: {', '.join(sorted(supported))}."
        )
    return provider
