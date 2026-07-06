"""Smoke tests for the initial package structure."""

import app
import app.api
import app.coach
import app.domain
import app.engines
import app.integrations
import app.integrations.coros
import app.repositories


def test_main_packages_are_importable() -> None:
    """Verify that the Sprint 0 packages can be imported."""
    assert app
