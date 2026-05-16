"""AppContext — framework runtime container.

Holds registered integrations and supports lookup by name, by concrete type,
or by contract protocol (with optional explicit binding for disambiguation).

See spec § 2.2, § 5.6.
"""

from __future__ import annotations

from typing import TypeVar

from hwhkit.core.integration import IntegrationProvider

T = TypeVar("T")
P = TypeVar("P", bound=IntegrationProvider)


class AppContext:
    """Runtime container of registered integrations + contract bindings."""

    def __init__(self) -> None:
        self._integrations: dict[str, IntegrationProvider] = {}
        self._contract_bindings: dict[type, str] = {}

    def register(self, integration: IntegrationProvider) -> None:
        if integration.name in self._integrations:
            raise ValueError(f"Integration {integration.name!r} already registered")
        self._integrations[integration.name] = integration

    def get(self, name: str) -> IntegrationProvider:
        try:
            return self._integrations[name]
        except KeyError as exc:
            raise KeyError(
                f"No integration named {name!r}. Registered: {list(self._integrations)}"
            ) from exc

    def get_typed(self, cls: type[P]) -> P:
        for integ in self._integrations.values():
            if isinstance(integ, cls):
                return integ
        raise LookupError(f"No integration of type {cls.__name__}")

    def bind_contract(self, contract: type, provider_name: str) -> None:
        if provider_name not in self._integrations:
            raise KeyError(f"Cannot bind to unknown integration {provider_name!r}")
        self._contract_bindings[contract] = provider_name

    def resolve(self, contract: type[T]) -> T:
        """Resolve a contract Protocol to its bound or auto-detected implementer."""
        if contract in self._contract_bindings:
            return self._integrations[self._contract_bindings[contract]]  # type: ignore[return-value]
        candidates = [
            integ for integ in self._integrations.values() if contract in integ.implements
        ]
        if not candidates:
            raise LookupError(
                f"No integration implements {contract.__name__}. "
                "Register one or use bind_contract()."
            )
        if len(candidates) > 1:
            names = [c.name for c in candidates]
            raise LookupError(
                f"multiple integrations implement {contract.__name__}: {names}. "
                "Use bind_contract() to disambiguate."
            )
        return candidates[0]  # type: ignore[return-value]

    @property
    def integrations(self) -> dict[str, IntegrationProvider]:
        return dict(self._integrations)


__all__ = ["AppContext"]
