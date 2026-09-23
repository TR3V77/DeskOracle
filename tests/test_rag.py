import pytest

from backend.rag import KnowledgeBase


def test_kb_rejects_article_with_unknown_category(tmp_path):
    bad_article = tmp_path / "bad.md"
    bad_article.write_text(
        "# Some Issue\n\nCategory: Not_A_Real_Category\n\nBody text.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Not_A_Real_Category"):
        KnowledgeBase(kb_dir=tmp_path)


def test_kb_loads_articles():
    kb = KnowledgeBase()
    assert len(kb.articles) >= 10


def test_search_returns_relevant_article_for_vpn_query():
    kb = KnowledgeBase()
    results = kb.search("my VPN keeps disconnecting and won't authenticate", top_k=3)
    assert len(results) > 0
    top_article, score = results[0]
    assert top_article.category == "Network_VPN"
    assert score > 0


def test_search_returns_relevant_article_for_printer_query():
    kb = KnowledgeBase()
    results = kb.search("the printer on the third floor is stuck offline", top_k=3)
    assert len(results) > 0
    top_article, _ = results[0]
    assert top_article.category == "Printer"


def test_search_handles_unrelated_query_gracefully():
    kb = KnowledgeBase()
    results = kb.search("what time does the cafeteria close", top_k=3)
    # Should not error; may return zero or low-confidence matches.
    assert isinstance(results, list)
