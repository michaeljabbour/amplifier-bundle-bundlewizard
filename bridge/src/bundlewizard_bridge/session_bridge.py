"""Session bridge for Bundlewizard — connects to an Amplifier session.

This module provides the configuration and utilities needed to launch an
Amplifier session using the Bundlewizard bundle. Import BUNDLEWIZARD_BUNDLE_REF
to get the bundle reference URI.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Amplifier GitHub organisation that hosts the bundle.
BUNDLEWIZARD_GITHUB_ORG = "michaeljabbour"

#: Repository name inside the org.
BUNDLEWIZARD_REPO_NAME = "amplifier-bundle-bundlewizard"

#: Branch / ref to pin to. Override via env-var BUNDLEWIZARD_BUNDLE_BRANCH.
BUNDLEWIZARD_BUNDLE_BRANCH = os.getenv("BUNDLEWIZARD_BUNDLE_BRANCH", "main")

# ---------------------------------------------------------------------------
# Bundle reference
# ---------------------------------------------------------------------------

#: The fully-qualified bundle reference used to load the Bundlewizard desktop
#: bundle into an Amplifier session.
BUNDLEWIZARD_BUNDLE_REF = (
    "git+https://github.com/michaeljabbour/amplifier-bundle-bundlewizard@main"
    "#subdirectory=bundles/desktop.yaml"
)
