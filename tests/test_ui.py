"""UI behaviour tests — runs the rendered HTML in a real WebKit browser via Playwright.

These tests verify that the interactive JS features (search bar, zoom controls,
keyboard shortcuts) actually work, not just that the HTML markup is present.

Requires: pip install playwright && playwright install webkit
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import renderer

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _PLAYWRIGHT_AVAILABLE,
    reason="playwright not installed — run: pip install playwright && playwright install webkit",
)

# Document with multiple headings (triggers TOC) and repeated searchable words
_TEST_MD = """# Main Title

## Section Alpha
Some text containing the word **findme** right here.

## Section Beta
More content. Also contains findme a second time.

### Subsection
Even deeper content.
"""


@pytest.fixture(scope="module")
def test_html():
    return renderer.render(_TEST_MD)


@pytest.fixture(scope="module")
def _pw():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="module")
def browser(_pw):
    b = _pw.webkit.launch()
    yield b
    b.close()


@pytest.fixture
def page(browser, test_html):
    """Fresh isolated page per test — no shared localStorage or DOM state."""
    ctx = browser.new_context()
    pg = ctx.new_page()
    pg.set_content(test_html, wait_until="domcontentloaded")
    yield pg
    ctx.close()


# ---------------------------------------------------------------------------
# Controls bar
# ---------------------------------------------------------------------------

class TestControlsBar:
    def test_controls_bar_is_rendered(self, page):
        assert page.query_selector("#controls") is not None

    def test_all_buttons_present(self, page):
        for btn in ["ctrl-search", "ctrl-zoom-out", "ctrl-zoom-reset", "ctrl-zoom-in"]:
            assert page.query_selector(f"#{btn}") is not None, f"#{btn} not found"


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_bar_hidden_on_load(self, page):
        assert not page.is_visible("#search-bar")

    def test_search_button_opens_bar(self, page):
        page.click("#ctrl-search")
        assert page.is_visible("#search-bar")

    def test_search_button_toggles_closed(self, page):
        page.click("#ctrl-search")
        page.click("#ctrl-search")
        assert not page.is_visible("#search-bar")

    def test_ctrl_f_opens_search(self, page):
        page.keyboard.press("Control+f")
        assert page.is_visible("#search-bar")

    def test_escape_closes_search(self, page):
        page.click("#ctrl-search")
        page.keyboard.press("Escape")
        assert not page.is_visible("#search-bar")

    def test_close_button_hides_bar(self, page):
        page.click("#ctrl-search")
        page.click("#search-close")
        assert not page.is_visible("#search-bar")

    def test_typing_highlights_matches(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "findme")
        assert len(page.query_selector_all("mark.chomnu-match")) > 0

    def test_match_count_shown_in_info(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "findme")
        info = page.inner_text("#search-info")
        assert "/" in info  # e.g. "1 / 2"

    def test_multiple_matches_found(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "findme")
        # "findme" appears twice in _TEST_MD
        assert len(page.query_selector_all("mark.chomnu-match")) == 2

    def test_no_results_message(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "xyzzy_absent_99999")
        assert page.inner_text("#search-info") == "No results"

    def test_clearing_query_removes_highlights(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "findme")
        page.fill("#search-input", "")
        assert len(page.query_selector_all("mark.chomnu-match")) == 0

    def test_next_button_advances_match(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "findme")
        first = page.inner_text("#search-info")
        page.click("#search-next")
        assert page.inner_text("#search-info") != first

    def test_prev_button_goes_back(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "findme")
        page.click("#search-next")
        after_next = page.inner_text("#search-info")
        page.click("#search-prev")
        assert page.inner_text("#search-info") != after_next

    def test_enter_advances_match(self, page):
        page.click("#ctrl-search")
        page.fill("#search-input", "findme")
        first = page.inner_text("#search-info")
        page.keyboard.press("Enter")
        assert page.inner_text("#search-info") != first


# ---------------------------------------------------------------------------
# Zoom
# ---------------------------------------------------------------------------

class TestZoom:
    def _font_size(self, page) -> float:
        return page.evaluate(
            "parseFloat(document.documentElement.style.fontSize) || 16"
        )

    def test_default_font_size_is_16px(self, page):
        assert self._font_size(page) == pytest.approx(16.0, abs=0.5)

    def test_zoom_in_button_increases_size(self, page):
        before = self._font_size(page)
        page.click("#ctrl-zoom-in")
        assert self._font_size(page) > before

    def test_zoom_out_button_decreases_size(self, page):
        page.click("#ctrl-zoom-in")
        zoomed = self._font_size(page)
        page.click("#ctrl-zoom-out")
        assert self._font_size(page) < zoomed

    def test_zoom_reset_restores_16px(self, page):
        page.click("#ctrl-zoom-in")
        page.click("#ctrl-zoom-in")
        page.click("#ctrl-zoom-reset")
        assert self._font_size(page) == pytest.approx(16.0, abs=0.5)

    def test_ctrl_equal_zooms_in(self, page):
        before = self._font_size(page)
        page.keyboard.press("Control+Equal")
        assert self._font_size(page) > before

    def test_ctrl_minus_zooms_out(self, page):
        page.click("#ctrl-zoom-in")
        zoomed = self._font_size(page)
        page.keyboard.press("Control+Minus")
        assert self._font_size(page) < zoomed

    def test_ctrl_zero_resets_zoom(self, page):
        page.click("#ctrl-zoom-in")
        page.click("#ctrl-zoom-in")
        page.keyboard.press("Control+0")
        assert self._font_size(page) == pytest.approx(16.0, abs=0.5)

    def test_zoom_does_not_exceed_max(self, page):
        for _ in range(25):  # 25 × +0.1 from 1.0 → well past 2.5 cap
            page.click("#ctrl-zoom-in")
        assert self._font_size(page) <= 16 * 2.5 + 0.5  # max zoom = 2.5×

    def test_zoom_does_not_go_below_min(self, page):
        for _ in range(20):  # 20 × -0.1 → well past 0.5 floor
            page.click("#ctrl-zoom-out")
        assert self._font_size(page) >= 16 * 0.5 - 0.5  # min zoom = 0.5×
