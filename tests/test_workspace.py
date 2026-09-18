"""
Tests for workspace_resolver.py
"""

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from providers.antigravity.workspace import resolve_workspace_name, extract_workspace_from_blob


def test_resolve_from_direct_name():
    name = resolve_workspace_name(workspace_name="AwesomeSaas")
    assert name == "AwesomeSaas"


def test_resolve_from_windows_path():
    path = r"C:\Projects\MyAwesomeApp"
    name = resolve_workspace_name(workspace_path=path)
    assert name == "MyAwesomeApp"


def test_resolve_from_posix_path():
    path = "/var/www/CompanyProfile"
    name = resolve_workspace_name(workspace_path=path)
    assert name == "CompanyProfile"


def test_resolve_with_custom_alias():
    from providers.antigravity.workspace import resolve_workspace
    path = r"C:\Projects\custom-dir"
    name, _ = resolve_workspace(
        workspace_path_or_uri=path,
        custom_aliases={"custom-dir": "MyCanonicalProject"}
    )
    assert name == "MyCanonicalProject"


def test_resolve_from_blob():
    blob = b"random\x00\x00/Users/dev/Projects/MicroserviceAPI\x00more"
    ws_name, ws_path = extract_workspace_from_blob(blob)
    assert ws_name == "MicroserviceAPI"


def test_resolve_fallback_unknown():
    name = resolve_workspace_name()
    assert name == "Unknown Workspace"
