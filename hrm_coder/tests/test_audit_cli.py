import json
import sys

import hrm_coder.audit_cli as audit_cli
from hrm_coder.inventory import ModuleInventory


def test_perform_audit(monkeypatch):
    def fake_inventory_package(pkg):
        return {"mod": ModuleInventory("mod", ["CodeEncoder"], [])}

    def fake_find_injection_points(inv):
        return ["mod.CodeEncoder"]

    monkeypatch.setattr(audit_cli, "inventory_package", fake_inventory_package)
    monkeypatch.setattr(
        audit_cli, "find_injection_points", fake_find_injection_points
    )
    monkeypatch.setattr(
        audit_cli.sandbox_detector,
        "detect_sandboxes",
        lambda: {
            "isolate": {
                "available": True,
                "version": "1.0",
                "path": "/bin/isolate",
            }
        },
    )
    monkeypatch.setattr(
        audit_cli.toolchain_detector,
        "detect_toolchains",
        lambda: {
            "g++": {
                "available": True,
                "version": "13.1",
                "path": "/bin/g++",
                "meets_requirement": True,
            }
        },
    )
    data = audit_cli.perform_audit("fake")
    assert data["injection_points"] == ["mod.CodeEncoder"]
    assert data["sandboxes"]["isolate"]["available"] is True
    assert data["toolchains"]["g++"]["meets_requirement"] is True


def test_main_prints(monkeypatch, capsys):
    monkeypatch.setattr(
        audit_cli,
        "perform_audit",
        lambda pkg: {
            "injection_points": ["a.b"],
            "sandboxes": {},
            "toolchains": {},
        },
    )
    monkeypatch.setattr(sys, "argv", ["audit_cli"])
    audit_cli.main()
    out = capsys.readouterr().out
    assert "Injection points:" in out
    assert "a.b" in out


def test_main_json(monkeypatch, capsys):
    monkeypatch.setattr(
        audit_cli,
        "perform_audit",
        lambda pkg: {
            "injection_points": ["a.b"],
            "sandboxes": {},
            "toolchains": {},
        },
    )
    monkeypatch.setattr(sys, "argv", ["audit_cli", "--json"])
    audit_cli.main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["injection_points"] == ["a.b"]
