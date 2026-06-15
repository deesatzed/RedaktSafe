from pathlib import Path

from fastapi.testclient import TestClient

from redaktsafe.api.main import ALLOWED_ARTIFACTS, create_app


def test_health_returns_healthy_status(tmp_path):
    client = TestClient(create_app(run_root=tmp_path))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["network_required"] is False


def test_preflight_is_transient_and_does_not_write_files(tmp_path):
    client = TestClient(create_app(run_root=tmp_path))

    response = client.post("/api/preflight", json={"text": "Patient Jane Doe, phone 617-555-0142."})

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_lane"] == "NEEDS_MANUAL_REVIEW"
    assert payload["counts_by_entity_type"]["NAME"] == 1
    assert list(tmp_path.iterdir()) == []


def test_packet_writes_only_scoped_artifacts(tmp_path):
    client = TestClient(create_app(run_root=tmp_path))

    response = client.post("/api/packet", json={"text": "Patient Jane Doe, MRN E4567890.", "source_name": "api-test"})

    assert response.status_code == 200
    payload = response.json()
    run_id = payload["run_id"]
    run_dir = tmp_path / run_id
    assert run_dir.is_dir()
    assert {path.name for path in run_dir.iterdir()} == ALLOWED_ARTIFACTS
    assert payload["artifact_urls"]["receipt.json"] == f"/api/artifacts/{run_id}/receipt.json"


def test_artifact_route_serves_allowed_artifact_and_blocks_bad_names(tmp_path):
    client = TestClient(create_app(run_root=tmp_path))
    packet = client.post("/api/packet", json={"text": "Patient Jane Doe, MRN E4567890."}).json()
    run_id = packet["run_id"]

    ok = client.get(f"/api/artifacts/{run_id}/receipt.json")
    traversal = client.get(f"/api/artifacts/{run_id}/../receipt.json")
    unknown = client.get(f"/api/artifacts/{run_id}/not_allowed.txt")
    absolute = client.get(f"/api/artifacts/{run_id}/%2Fetc%2Fhosts")

    assert ok.status_code == 200
    assert traversal.status_code in {404, 422}
    assert unknown.status_code == 404
    assert absolute.status_code in {404, 422}


def test_artifact_route_blocks_symlink_escape(tmp_path):
    client = TestClient(create_app(run_root=tmp_path))
    packet = client.post("/api/packet", json={"text": "Patient Jane Doe, MRN E4567890."}).json()
    run_id = packet["run_id"]
    receipt_path = tmp_path / run_id / "receipt.json"
    receipt_path.unlink()
    receipt_path.symlink_to(Path("/etc/hosts"))

    response = client.get(f"/api/artifacts/{run_id}/receipt.json")

    assert response.status_code == 404


def test_input_size_limit_is_enforced(tmp_path):
    client = TestClient(create_app(run_root=tmp_path, max_input_chars=10))

    response = client.post("/api/preflight", json={"text": "x" * 11})

    assert response.status_code == 413

