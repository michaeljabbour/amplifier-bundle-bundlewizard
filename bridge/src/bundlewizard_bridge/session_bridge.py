"""Session bridge for the Bundlewizard desktop bundle.

Exposes the runtime prompt-execution entry point used by the WebSocket
handler, along with the bundle configuration constants required to load
the correct Amplifier desktop bundle.
"""

from __future__ import annotations

import os

from bundlewizard_bridge.ws_handler import _execute_prompt as execute_prompt

__all__ = [
    "BUNDLEWIZARD_BUNDLE_REF",
    "BUNDLEWIZARD_GITHUB_ORG",
    "BUNDLEWIZARD_REPO_NAME",
    "BUNDLEWIZARD_BUNDLE_SUBDIRECTORY",
    "execute_prompt",
]

#: Environment variable used to override the bundle branch at runtime.
_ENV_BUNDLE_BRANCH = "BUNDLEWIZARD_BUNDLE_BRANCH"

#: Default branch used when the env var is not set.
_DEFAULT_BRANCH = "main"

#: Amplifier GitHub organisation that hosts the bundle.
BUNDLEWIZARD_GITHUB_ORG = "michaeljabbour"

#: Repository name inside the organisation.
BUNDLEWIZARD_REPO_NAME = "amplifier-bundle-bundlewizard"

#: Subdirectory inside the repo that contains the desktop bundle descriptor.
BUNDLEWIZARD_BUNDLE_SUBDIRECTORY = "bundles/desktop.yaml"


def build_bundle_ref(branch: str | None = None) -> str:
    """Build a fully-qualified bundle reference for the Bundlewizard desktop bundle.

    Reads ``BUNDLEWIZARD_BUNDLE_BRANCH`` from the environment at call time,
    so callers can override the branch without reloading the module.

    Args:
        branch: Branch or ref to use. When ``None``, falls back to the
            ``BUNDLEWIZARD_BUNDLE_BRANCH`` env var, then to ``"main"``.

    Returns:
        A ``git+https://...`` bundle reference string.
    """
    resolved = branch or os.getenv(_ENV_BUNDLE_BRANCH, _DEFAULT_BRANCH)
    return (
        f"git+https://github.com/{BUNDLEWIZARD_GITHUB_ORG}/{BUNDLEWIZARD_REPO_NAME}"
        f"@{resolved}"
        f"#subdirectory={BUNDLEWIZARD_BUNDLE_SUBDIRECTORY}"
    )


#: Fully-qualified bundle reference used to load the Bundlewizard desktop bundle.
#: Represents the default ref at import time. Use :func:`build_bundle_ref` to
#: resolve the ref dynamically (e.g. when the env var is set after import).
BUNDLEWIZARD_BUNDLE_REF = build_bundle_ref()
