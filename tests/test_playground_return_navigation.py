from pathlib import Path

HTML = (Path(__file__).parents[1] / "playground" / "before-with-tria.html").read_text(encoding="utf-8")


def test_comparison_page_has_prominent_return_navigation():
    assert HTML.count('href="./"') >= 3
    assert "Return to TRIA Playground" in HTML
    assert "Back to the Playground" in HTML
