"""
Lightweight retrieval-augmented generation (RAG) over the local IT knowledge
base. Uses TF-IDF + cosine similarity instead of a vector database or
embeddings API so the whole pipeline runs offline with no external
dependencies or cost -- appropriate for a knowledge base of this size.
"""
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.categories import CATEGORIES

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "kb_articles"


@dataclass
class KBArticle:
    filename: str
    category: str
    title: str
    body: str


def _parse_article(path: Path) -> KBArticle:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    category = "Other"
    for line in lines:
        if line.lower().startswith("category:"):
            category = line.split(":", 1)[1].strip()
            break
    if category not in CATEGORIES:
        raise ValueError(
            f"{path.name}: 'Category: {category}' does not match any of "
            f"backend.categories.CATEGORIES ({', '.join(CATEGORIES)}) -- "
            f"fix the typo/rename in the article or add the category upstream."
        )
    return KBArticle(filename=path.name, category=category, title=title, body=text)


class KnowledgeBase:
    """Loads all KB articles and answers similarity queries against them."""

    def __init__(self, kb_dir: Path = KB_DIR):
        self.articles = [_parse_article(p) for p in sorted(kb_dir.glob("*.md"))]
        if not self.articles:
            raise RuntimeError(f"No knowledge base articles found in {kb_dir}")
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform([a.body for a in self.articles])

    def search(self, query: str, top_k: int = 3) -> list[tuple[KBArticle, float]]:
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(zip(self.articles, scores), key=lambda pair: pair[1], reverse=True)
        return [pair for pair in ranked[:top_k] if pair[1] > 0]

    def categories(self) -> list[str]:
        return sorted({a.category for a in self.articles})
