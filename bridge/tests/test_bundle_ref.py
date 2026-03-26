"""Tests for BUNDLEWIZARD_BUNDLE_REF constant in session_bridge."""

from bundlewizard_bridge.session_bridge import BUNDLEWIZARD_BUNDLE_REF


def test_bundle_ref_points_to_desktop_variant():
    """The bundle ref must point to the desktop variant."""
    assert "bundles/desktop.yaml" in BUNDLEWIZARD_BUNDLE_REF
    assert "amplifier-bundle-bundlewizard" in BUNDLEWIZARD_BUNDLE_REF


def test_bundle_ref_uses_subdirectory_fragment():
    """The bundle ref must use the #subdirectory= fragment to load the desktop bundle."""
    assert "#subdirectory=" in BUNDLEWIZARD_BUNDLE_REF


def test_bundle_ref_uses_main_branch_by_default():
    """BUNDLEWIZARD_BUNDLE_REF defaults to the main branch."""
    assert "@main#subdirectory=" in BUNDLEWIZARD_BUNDLE_REF
