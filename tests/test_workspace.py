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
    name = resolve_workspace_name(workspace_name="TernakOS")
    assert name == "TernakOS"


def test_resolve_from_windows_path():
    path = r"C:\Projects\MyAwesomeApp"
    name = resolve_workspace_name(workspace_path=path)
    assert name == "MyAwesomeApp"


def test_resolve_from_posix_path():
    path = "/var/www/CompanyProfile"
    name = resolve_workspace_name(workspace_path=path)
    assert name == "CompanyProfile"


def test_resolve_with_alias():
    path = r"D:\Dokumen\02_Kerja_Profesional\Myself"
    name = resolve_workspace_name(workspace_path=path)
    assert name == "Myself"


def test_resolve_from_blob():
    blob = b"random\x00\x00d:\\Dokumen\\02_Kerja_Profesional\\Myself\\Vault\x00more"
    ws_name, ws_path = extract_workspace_from_blob(blob)
    assert ws_name == "Myself"


def test_resolve_fallback_unknown():
    name = resolve_workspace_name()
    assert name == "Unknown Workspace"
