from pathlib import Path

HTML = (Path(__file__).parents[1] / "playground" / "index.html").read_text(encoding="utf-8")


def test_playground_answers_core_adoption_questions():
    assert "What is TRIA?" in HTML
    assert "Why use it?" in HTML
    assert "How do I build with it?" in HTML


def test_playground_links_to_applied_comparison_and_quickstart():
    assert 'href="before-with-tria.html"' in HTML
    assert "docs/quickstart.md" in HTML


def test_playground_plain_language_definition_is_present():
    assert "open-source relational governance layer" in HTML
    assert "consent, authority, claims, and relationship state" in HTML
