import pytest
import os
os.environ.setdefault("OPENAI_API_KEY", "test-key")
from app.helper.rag_engine import (
    normalise_level,
    get_collection_name,
)


# -----------------------------
# Tests for normalise_level()
# -----------------------------

def test_normalise_level_valid_inputs():
    assert normalise_level("UG") == "ug"
    assert normalise_level("ug") == "ug"
    assert normalise_level("Undergraduate") == "ug"
    assert normalise_level("postgraduate_taught") == "pgt"
    assert normalise_level("PG_ReSearch") == "pgr"


def test_normalise_level_strips_whitespace():
    assert normalise_level("  UG ") == "ug"


def test_normalise_level_invalid_raises():
    with pytest.raises(ValueError):
        normalise_level("")       # empty
    with pytest.raises(ValueError):
        normalise_level("   ")    # whitespace only
        

def test_normalise_level_falls_back_to_original():
    # something unknown → returned lowercased
    assert normalise_level("mystery") == "mystery"


# -----------------------------
# Tests for get_collection_name()
# -----------------------------

def test_get_collection_name_handbook_levels():
    assert get_collection_name("handbook", "UG") == "handbook_ug"
    assert get_collection_name("handbook", "pgt") == "handbook_pgt"
    assert get_collection_name("handbook", "Postgraduate_Research") == "handbook_pgr"


def test_get_collection_name_requires_level():
    with pytest.raises(ValueError):
        get_collection_name("handbook", None)

    with pytest.raises(ValueError):
        get_collection_name("handbook", "")   # empty string should fail


def test_get_collection_name_other_doc_types():
    assert get_collection_name("academic_integrity") == "academic_integrity"
    assert get_collection_name("  academic_integrity ") == "academic_integrity"


def test_get_collection_name_lowercase_doc_type():
    assert get_collection_name("HandBook", "UG") == "handbook_ug"