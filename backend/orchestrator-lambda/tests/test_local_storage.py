import json
import os
import time

import pytest

from src.services import local_storage


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage, "LOCAL_DATA_DIR", tmp_path)
    monkeypatch.setattr(local_storage, "OUTPUT_BUCKET", "output")
    monkeypatch.setattr(local_storage, "MARKET_ANALYSIS_BUCKET", "output")
    return tmp_path


def test_save_and_read_json_round_trip(data_dir):
    location = local_storage.save_json({"a": "č"}, "id-1", "market_position")

    assert location == str(data_dir / "output" / "market_position" / "id-1.json")
    assert local_storage.read_json("output", "market_position/id-1.json") == {"a": "č"}


def test_read_file_and_pdf(data_dir):
    (data_dir / "client" / "docs").mkdir(parents=True)
    (data_dir / "client" / "docs" / "a.txt").write_text("hello", encoding="utf-8")
    (data_dir / "client" / "docs" / "a.pdf").write_bytes(b"%PDF-1.4")

    assert local_storage.read_file("client", "docs/a.txt") == "hello"
    assert local_storage.read_pdf("client", "docs/a.pdf") == b"%PDF-1.4"


def test_keys_cannot_escape_the_bucket(data_dir):
    with pytest.raises(ValueError):
        local_storage.read_file("client", "../secret.txt")


def test_list_json_files_filters_prefix_and_sorts_newest_first(data_dir):
    local_storage.save_json({}, "old", "market_position")
    local_storage.save_json({}, "new", "market_position")
    local_storage.save_json({}, "other", "peer_analysis")
    old = data_dir / "output" / "market_position" / "old.json"
    past = time.time() - 60
    os.utime(old, (past, past))

    files = local_storage.list_json_files("output", "market_position/")

    assert [f["key"] for f in files] == ["market_position/new.json", "market_position/old.json"]
    assert local_storage.list_json_files("output", "market_position/", limit=1)[0]["filename"] == "new.json"
    assert local_storage.list_json_files("missing-bucket", "") == []


def test_fetch_files_with_metadata_filters_by_client_and_nace(data_dir):
    local_storage.save_json({"client_name": "Elektro Trade", "nace_code": "D35.14"}, "a", "market_position")
    local_storage.save_json({"client_name": "Žito d.o.o.", "nace_code": "A1.11"}, "b", "market_position")

    by_client = local_storage.fetch_files_with_metadata("output", "market_position/", client_name_filter="elektro")
    by_nace = local_storage.fetch_files_with_metadata("output", "market_position/", category_code_filter="A1")

    assert [f["content"]["client_name"] for f in by_client] == ["Elektro Trade"]
    assert [f["content"]["nace_code"] for f in by_nace] == ["A1.11"]


def test_read_json_metadata_keeps_listing_fields_only(data_dir):
    report = {"client_name": "X", "nace_code": "D35.14", "analysis_id": "market_position/a.json",
              "market_analysis_id": "m.json", "sections": ["big"]}
    (data_dir / "output" / "market_position").mkdir(parents=True)
    (data_dir / "output" / "market_position" / "a.json").write_text(json.dumps(report))

    assert local_storage.read_json_metadata("market_position/a.json") == {
        "nace_code": "D35.14", "analysis_id": "market_position/a.json",
        "market_analysis_id": "m.json", "client_name": "X",
    }
    assert local_storage.read_json_metadata("market_position/missing.json") is None
