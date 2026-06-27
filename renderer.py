import re
import os
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.sane_lists import SaneListExtension
from markdown.extensions.toc import TocExtension
from pymdownx.arithmatex import ArithmatexExtension
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


def _load_asset(name):
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _highlight_code(code, lang):
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
    except ClassNotFound:
        lexer = TextLexer()
    formatter = HtmlFormatter(nowrap=True)
    return highlight(code, lexer, formatter)


def _extract_mermaid(text):
    """Replace ```mermaid blocks with placeholders before markdown processing."""
    blocks = []

    def replacer(m):
        idx = len(blocks)
        blocks.append(m.group(1))
        return f"\n\n<!--MERMAID:{idx}-->\n\n"

    text = re.sub(r"```mermaid\n(.*?)```", replacer, text, flags=re.DOTALL)
    return text, blocks


def _restore_mermaid(html, blocks):
    for idx, code in enumerate(blocks):
        html = html.replace(
            f"<p><!--MERMAID:{idx}--></p>",
            f'<div class="mermaid">{code}</div>',
        )
        # fallback if markdown didn't wrap it in <p>
        html = html.replace(
            f"<!--MERMAID:{idx}-->",
            f'<div class="mermaid">{code}</div>',
        )
    return html


def _apply_syntax_highlighting(html):
    """Post-process <code class="language-X"> blocks with Pygments."""

    def replacer(m):
        lang = m.group(1) or ""
        code = m.group(2)
        # unescape HTML entities that markdown put in
        code = (
            code.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )
        highlighted = _highlight_code(code, lang)
        lang_class = f' class="language-{lang}"' if lang else ""
        return f"<pre><code{lang_class}>{highlighted}</code></pre>"

    return re.sub(
        r'<pre><code(?:\s+class="language-([^"]*)")?>(.*?)</code></pre>',
        replacer,
        html,
        flags=re.DOTALL,
    )


# Inline JS for search, zoom, and TOC active-section tracking
_UI_JS = """
(function () {
  // ── Zoom ──────────────────────────────────────────────────────────────
  // localStorage throws SecurityError in null-origin contexts (load_html / set_content)
  var zoom = 1;
  try { zoom = parseFloat(localStorage.getItem('chomnu-zoom') || '1') || 1; } catch (e) {}
  function applyZoom() {
    document.documentElement.style.fontSize = (16 * zoom) + 'px';
    try { localStorage.setItem('chomnu-zoom', String(zoom)); } catch (e) {}
  }
  applyZoom();

  // ── TOC: hide sidebar when empty, highlight active section ────────────
  var sidebar = document.getElementById('toc-sidebar');
  var mainContent = document.getElementById('main-content');
  if (sidebar && !sidebar.querySelector('a')) {
    sidebar.style.display = 'none';
    if (mainContent) mainContent.style.marginLeft = '0';
  } else if (sidebar) {
    // rootMargin must use px (not %) when root is null — WKWebView throws otherwise
    try {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          var link = sidebar.querySelector('a[href="#' + e.target.id + '"]');
          if (link) link.classList.toggle('toc-active', e.isIntersecting);
        });
      }, { rootMargin: '-80px 0px -300px 0px' });
      document.querySelectorAll('article [id]').forEach(function (el) {
        observer.observe(el);
      });
    } catch (err) { /* IntersectionObserver unsupported or bad config — skip active tracking */ }
  }

  // ── Search ────────────────────────────────────────────────────────────
  var searchBar = document.getElementById('search-bar');
  var searchInput = document.getElementById('search-input');
  var searchInfo = document.getElementById('search-info');
  var article = document.querySelector('article');

  var marks = [];
  var currentIdx = -1;
  var searchVisible = false;

  function clearMarks() {
    marks.forEach(function (m) {
      if (m.parentNode) {
        // Don't call normalize() here — it can invalidate sibling mark references
        m.parentNode.replaceChild(document.createTextNode(m.textContent), m);
      }
    });
    marks = [];
    currentIdx = -1;
    updateInfo();
  }

  function updateInfo() {
    if (!marks.length) {
      searchInfo.textContent = searchInput.value ? 'No results' : '';
    } else {
      searchInfo.textContent = (currentIdx + 1) + ' / ' + marks.length;
    }
  }

  function doSearch(query) {
    clearMarks();
    if (!query) return;
    var lower = query.toLowerCase();
    var walker = document.createTreeWalker(article, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        var tag = node.parentElement && node.parentElement.tagName.toLowerCase();
        return ['script', 'style', 'mark'].indexOf(tag) !== -1
          ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      }
    });
    var textNodes = [];
    var n;
    while ((n = walker.nextNode())) textNodes.push(n);
    textNodes.forEach(function (textNode) {
      var text = textNode.textContent;
      var lText = text.toLowerCase();
      if (lText.indexOf(lower) === -1) return;
      var frag = document.createDocumentFragment();
      var last = 0, idx;
      while ((idx = lText.indexOf(lower, last)) !== -1) {
        if (idx > last) frag.appendChild(document.createTextNode(text.slice(last, idx)));
        var mark = document.createElement('mark');
        mark.className = 'chomnu-match';
        mark.textContent = text.slice(idx, idx + query.length);
        frag.appendChild(mark);
        marks.push(mark);
        last = idx + query.length;
      }
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      textNode.parentNode.replaceChild(frag, textNode);
    });
    if (marks.length) gotoMatch(0); else updateInfo();
  }

  function gotoMatch(idx) {
    if (!marks.length) return;
    if (currentIdx >= 0) marks[currentIdx].classList.remove('chomnu-current');
    currentIdx = ((idx % marks.length) + marks.length) % marks.length;
    marks[currentIdx].classList.add('chomnu-current');
    marks[currentIdx].scrollIntoView({ behavior: 'smooth', block: 'center' });
    updateInfo();
  }

  function showSearch() {
    searchBar.style.display = 'flex';
    searchVisible = true;
    searchInput.focus();
    searchInput.select();
  }

  function hideSearch() {
    searchBar.style.display = 'none';
    searchVisible = false;
    clearMarks();
    searchInput.value = '';
  }

  searchInput.addEventListener('input', function () { doSearch(searchInput.value); });
  searchInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); gotoMatch(e.shiftKey ? currentIdx - 1 : currentIdx + 1); }
  });
  document.getElementById('search-prev').addEventListener('click', function () { gotoMatch(currentIdx - 1); });
  document.getElementById('search-next').addEventListener('click', function () { gotoMatch(currentIdx + 1); });
  document.getElementById('search-close').addEventListener('click', hideSearch);

  // ── Controls bar buttons ──────────────────────────────────────────────
  document.getElementById('ctrl-search').addEventListener('click', function () {
    if (searchVisible) { hideSearch(); } else { showSearch(); }
  });
  document.getElementById('ctrl-zoom-out').addEventListener('click', function () {
    zoom = Math.max(0.5, parseFloat((zoom - 0.1).toFixed(1))); applyZoom();
  });
  document.getElementById('ctrl-zoom-in').addEventListener('click', function () {
    zoom = Math.min(2.5, parseFloat((zoom + 0.1).toFixed(1))); applyZoom();
  });
  document.getElementById('ctrl-zoom-reset').addEventListener('click', function () {
    zoom = 1; applyZoom();
  });

  // ── Keyboard shortcuts (Ctrl, not Cmd — WKWebView intercepts Cmd+F/+/-) ──
  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey && e.key === 'f') { e.preventDefault(); showSearch(); }
    if (e.ctrlKey && (e.key === '=' || e.key === '+')) {
      e.preventDefault(); zoom = Math.min(2.5, parseFloat((zoom + 0.1).toFixed(1))); applyZoom();
    }
    if (e.ctrlKey && e.key === '-') {
      e.preventDefault(); zoom = Math.max(0.5, parseFloat((zoom - 0.1).toFixed(1))); applyZoom();
    }
    if (e.ctrlKey && e.key === '0') { e.preventDefault(); zoom = 1; applyZoom(); }
    if (e.key === 'Escape' && searchBar.style.display !== 'none') { e.preventDefault(); hideSearch(); }
  }, true);
})();
"""


def render(text):
    """Convert Markdown text to a full HTML document string."""
    text, mermaid_blocks = _extract_mermaid(text)

    md = markdown.Markdown(
        extensions=[
            FencedCodeExtension(),
            TableExtension(),
            Nl2BrExtension(),
            SaneListExtension(),
            "markdown.extensions.attr_list",
            "markdown.extensions.def_list",
            "markdown.extensions.admonition",
            TocExtension(toc_depth="2-4"),
            ArithmatexExtension(generic=True),
        ]
    )
    body = md.convert(text)
    body = _restore_mermaid(body, mermaid_blocks)
    body = _apply_syntax_highlighting(body)
    toc_html = md.toc  # empty string when no headings

    css = _load_asset("style.css") or ""
    pygments_css = HtmlFormatter().get_style_defs(".highlight")
    mathjax_js = _load_asset("mathjax.min.js")
    mermaid_js = _load_asset("mermaid.min.js")

    has_math = "arithmatex" in body
    has_mermaid = bool(mermaid_blocks)

    math_block = ""
    if has_math and mathjax_js:
        math_block = f"""
        <script>
        window.MathJax = {{
            tex: {{ inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] }},
            svg: {{ fontCache: 'local' }},
            options: {{ enableMenu: false, enableAssistiveMml: false }},
            startup: {{ typeset: true }}
        }};
        </script>
        <script>{mathjax_js}</script>"""
    elif has_math:
        math_block = """
        <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg-full.js"></script>
        <script>window.MathJax = {{ tex: {{ inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']] }}, options: {{ enableMenu: false }} }};</script>"""

    mermaid_block = ""
    if has_mermaid and mermaid_js:
        mermaid_block = f"""
        <script>{mermaid_js}</script>
        <script>mermaid.initialize({{ startOnLoad: true, theme: 'default' }});</script>"""
    elif has_mermaid:
        mermaid_block = """
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{ startOnLoad: true }});</script>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
{css}
{pygments_css}
</style>
{math_block}
{mermaid_block}
</head>
<body>
<aside id="toc-sidebar">
  <div class="toc-title">Contents</div>
  {toc_html}
</aside>
<div id="main-content">
<article>
{body}
</article>
</div>
<div id="controls">
  <button id="ctrl-search" title="Search (Ctrl+F)">⌕</button>
  <button id="ctrl-zoom-out" title="Zoom out (Ctrl+-)">−</button>
  <button id="ctrl-zoom-reset" title="Reset zoom (Ctrl+0)">A</button>
  <button id="ctrl-zoom-in" title="Zoom in (Ctrl+=)">+</button>
</div>
<div id="search-bar">
  <input type="text" id="search-input" placeholder="Search…" autocomplete="off" spellcheck="false">
  <span id="search-info"></span>
  <button id="search-prev" title="Previous (Shift+Enter)">↑</button>
  <button id="search-next" title="Next (Enter)">↓</button>
  <button id="search-close" title="Close (Esc)">✕</button>
</div>
<script>{_UI_JS}</script>
</body>
</html>"""
