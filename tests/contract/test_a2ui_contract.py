"""
Contract Tests: Verify Frontend A2UI Web Component contracts and JSON manifests.
"""
import json
import os


def test_web_package_json_a2ui_references():
    package_json_path = os.path.join("apps", "web", "package.json")
    assert os.path.exists(package_json_path), "apps/web/package.json must exist"

    with open(package_json_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    deps = pkg.get("dependencies", {})
    assert "@a2ui/lit" in deps, "@a2ui/lit dependency must be present"
    assert "@a2ui/web_core" in deps, "@a2ui/web_core dependency must be present"
    assert "lit" in deps, "lit dependency must be present"


def test_a2ui_component_contract_file():
    viewer_ts_path = os.path.join("apps", "web", "src", "components", "radiology-study-viewer.ts")
    assert os.path.exists(viewer_ts_path), "A2UI study viewer component must exist"

    with open(viewer_ts_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "radiology-study-viewer" in content
    assert "studyInstanceUid" in content
    assert "Finding" in content or "findings" in content
