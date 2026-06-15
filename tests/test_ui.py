from pathlib import Path

from fastapi.testclient import TestClient

from redaktsafe.api.main import create_app


def test_ui_files_contain_required_workflow_and_no_remote_calls():
    index = Path("frontend/index.html").read_text(encoding="utf-8")
    app_js = Path("frontend/app.js").read_text(encoding="utf-8")
    combined = index + app_js + Path("frontend/styles.css").read_text(encoding="utf-8")

    assert "Run Local Preflight" in combined
    assert "risk lane" in combined.lower()
    assert "redacted text" in combined.lower()
    assert "entity summary" in combined.lower()
    assert "limitations" in combined.lower()
    assert "download" in combined.lower()
    assert "residual" in combined.lower()
    assert "review" in combined.lower()
    assert "fetch(\"/api/preflight\"" in app_js
    assert "fetch(\"/api/packet\"" in app_js
    assert "http://" not in app_js
    assert "https://" not in app_js
    assert "analytics" not in combined.lower()


def test_api_serves_ui_and_static_assets(tmp_path):
    client = TestClient(create_app(run_root=tmp_path))

    index = client.get("/")
    app_js = client.get("/frontend/app.js")
    styles = client.get("/frontend/styles.css")

    assert index.status_code == 200
    assert app_js.status_code == 200
    assert styles.status_code == 200
    assert "RedaktSafe Trust Packet Workbench" in index.text

