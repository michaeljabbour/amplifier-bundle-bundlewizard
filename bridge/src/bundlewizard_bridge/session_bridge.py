"""Session bridge for the Bundlewizard desktop bundle.

Exposes the bundle configuration constant required to load the correct
Amplifier desktop bundle.
"""

from __future__ import annotations

__all__ = [
    "BUNDLEWIZARD_BUNDLE_REF",
]

#: Fully-qualified bundle reference used to load the Bundlewizard desktop bundle.
BUNDLEWIZARD_BUNDLE_REF = (
    "git+https://github.com/michaeljabbour/amplifier-bundle-bundlewizard"
    "@main"
    "#subdirectory=bundles/desktop.yaml"
)
