"""Pytest configuration for tool-mode tests.

Adds the tool-mode and hooks-mode source directories to sys.path so that
amplifier_module_tool_mode and amplifier_module_hooks_mode can be imported
without requiring either package to be pip-installed.

Directory layout (relative to this file):
  tests/conftest.py               <- this file
  ../amplifier_module_tool_mode/  <- tool-mode package source
  ../../hooks-mode/               <- hooks-mode directory
    amplifier_module_hooks_mode/  <- hooks-mode package source
"""

from __future__ import annotations

import sys
from pathlib import Path

# amplifier-bundle-modes/modules/tool-mode/
_TOOL_MODE_DIR = Path(__file__).parent.parent.resolve()

# amplifier-bundle-modes/modules/hooks-mode/
_HOOKS_MODE_DIR = _TOOL_MODE_DIR.parent / "hooks-mode"

for _dir in (_TOOL_MODE_DIR, _HOOKS_MODE_DIR):
    _dir_str = str(_dir)
    if _dir_str not in sys.path:
        sys.path.insert(0, _dir_str)
