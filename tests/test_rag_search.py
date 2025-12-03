import pytest
from unittest.mock import patch, MagicMock

from app.helper.rag_engine import search_similar_chunks

@patch("app.helper.rag_engine.embed_text")
@patch("app.helper.rag_engine.get_or_create_collection")
def test_search_similar_chunks_basic(mock_get_collection, mock_embed):
    # Mock embed_text to avoid OpenAI call
    mock_embed.return_value = [[0.1, 0.2, 0.3]]  

    # Mock Chroma collection
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [
            ["chunk A", "chunk B", "chunk C"]
        ]
    }
    mock_get_collection.return_value = mock_collection

    # Call function
    chunks = search_similar_chunks(
        query="what is the deadline?",
        doc_type="handbook",
        level="ug",
        top_k=3
    )

    # Assertions
    assert chunks == ["chunk A", "chunk B", "chunk C"]
    mock_embed.assert_called_once()
    mock_get_collection.assert_called_once()
    mock_collection.query.assert_called_once()


@patch("app.helper.rag_engine.embed_text")
@patch("app.helper.rag_engine.get_or_create_collection")
def test_search_similar_chunks_empty_results(mock_get_collection, mock_embed):
    mock_embed.return_value = [[0.1, 0.2, 0.3]] 
    # Mock collection with empty results
    mock_collection = MagicMock()
    mock_collection.query.return_value = {"documents": [[]]}
    mock_get_collection.return_value = mock_collection

    chunks = search_similar_chunks(
        query="nonsense query",
        doc_type="handbook",
        level="ug",
        top_k=3
    )

    assert chunks == []


@patch("app.helper.rag_engine.embed_text")
@patch("app.helper.rag_engine.get_or_create_collection")
def test_search_calls_collection_with_correct_level(mock_get_collection, mock_embed):
    mock_embed.return_value = [[0.5, 0.5, 0.5]]

    mock_collection = MagicMock()
    mock_collection.query.return_value = {"documents": [["example chunk"]]}
    mock_get_collection.return_value = mock_collection

    chunks = search_similar_chunks("hello", "handbook", "pgt")

    assert chunks == ["example chunk"]

    # Ensure correct call based on doc_type + level
    mock_get_collection.assert_called_with("handbook", "pgt")
