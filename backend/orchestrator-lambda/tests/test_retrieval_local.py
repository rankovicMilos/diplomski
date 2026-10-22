import pytest

from src.retrieval import local


def test_equals_filter():
    assert local.to_chroma_where({"equals": {"key": "industry", "value": "electricity"}}) == {
        "industry": "electricity"
    }


def test_combined_filters():
    where = local.to_chroma_where({"andAll": [
        {"equals": {"key": "industry", "value": "cereals"}},
        {"in": {"key": "year", "value": [2024, 2025]}},
    ]})
    assert where == {"$and": [{"industry": "cereals"}, {"year": {"$in": [2024, 2025]}}]}


def test_no_filter():
    assert local.to_chroma_where(None) is None


def test_unsupported_filter():
    with pytest.raises(ValueError):
        local.to_chroma_where({"startsWith": {"key": "industry", "value": "el"}})


def test_metadata_round_trip_keeps_lists():
    sidecar = {"industry": "cereals", "industries": ["cereals", "livestock"],
               "sections": ["price_analysis"], "year": 2025, "period": None}

    flat = local.to_chroma_metadata(sidecar)
    assert flat == {"industry": "cereals", "industries": "cereals,livestock",
                    "sections": "price_analysis", "year": 2025}
    assert local.from_chroma_metadata(flat)["industries"] == ["cereals", "livestock"]
