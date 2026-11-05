"""Dependency injection container and composition root."""

from src.presentation.dependencies.container import (
    Container,
    get_container,
    set_container,
)

__all__ = ["Container", "get_container", "set_container"]
