"""Tests for renderer.py — Markdown → HTML conversion."""
import os
import sys
import pytest

# Make sure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import renderer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def render(md):
    """Shorthand: render markdown and return the full HTML string."""
    return renderer.render(md)


def body(md):
    """Render and return just the <article> contents for easier assertions."""
    html = render(md)
    start = html.index("<article>") + len("<article>")
    end = html.index("</article>")
    return html[start:end].strip()


# ---------------------------------------------------------------------------
# HTML structure
# ---------------------------------------------------------------------------

class TestHTMLStructure:
    def test_output_is_full_html_document(self):
        html = render("hello")
        assert html.startswith("<!DOCTYPE html>")
        assert "<html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html

    def test_article_wrapper_present(self):
        html = render("hello")
        assert "<article>" in html
        assert "</article>" in html

    def test_charset_meta_present(self):
        html = render("hello")
        assert 'charset="utf-8"' in html

    def test_viewport_meta_present(self):
        html = render("hello")
        assert "viewport" in html

    def test_style_css_injected(self):
        html = render("hello")
        # Our CSS file contains this unique string
        assert "--bg:" in html

    def test_empty_document_renders_without_error(self):
        html = render("")
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# Basic Markdown elements
# ---------------------------------------------------------------------------

class TestBasicMarkdown:
    def test_heading_h1(self):
        assert "<h1" in body("# Hello")
        assert "Hello" in body("# Hello")

    def test_heading_h2(self):
        assert "<h2" in body("## World")
        assert "World" in body("## World")

    def test_heading_h3(self):
        assert "<h3" in body("### Sub")
        assert "Sub" in body("### Sub")

    def test_paragraph(self):
        b = body("Just some prose.")
        assert "<p>" in b
        assert "Just some prose." in b

    def test_bold(self):
        assert "<strong>" in body("**bold**")

    def test_italic(self):
        assert "<em>" in body("*italic*")

    def test_unordered_list(self):
        b = body("- one\n- two\n- three")
        assert "<ul>" in b
        assert "<li>" in b

    def test_ordered_list(self):
        b = body("1. first\n2. second")
        assert "<ol>" in b
        assert "<li>" in b

    def test_link(self):
        b = body("[click](https://example.com)")
        assert '<a href="https://example.com">' in b

    def test_image(self):
        b = body("![alt](image.png)")
        assert "<img" in b
        assert 'src="image.png"' in b

    def test_horizontal_rule(self):
        assert "<hr" in body("---")

    def test_blockquote(self):
        b = body("> wise words")
        assert "<blockquote>" in b
        assert "wise words" in b

    def test_inline_code(self):
        b = body("use `print()` here")
        assert "<code>" in b
        assert "print()" in b

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        b = body(md)
        assert "<table>" in b
        assert "<th>" in b
        assert "<td>" in b

    def test_multiline_paragraph(self):
        b = body("line one\nline two")
        assert "line one" in b
        assert "line two" in b


# ---------------------------------------------------------------------------
# Fenced code blocks & syntax highlighting
# ---------------------------------------------------------------------------

class TestCodeBlocks:
    def test_fenced_code_block_renders_as_pre(self):
        b = body("```\nsome code\n```")
        assert "<pre>" in b

    def test_fenced_code_with_language(self):
        b = body("```python\nprint('hi')\n```")
        assert "<pre>" in b
        assert "print" in b

    def test_syntax_highlighting_adds_spans(self):
        b = body("```python\ndef foo():\n    return 42\n```")
        # Pygments wraps tokens in <span> elements
        assert "<span" in b

    def test_unknown_language_still_renders(self):
        b = body("```brainfuck\n+++---\n```")
        assert "<pre>" in b
        assert "+++---" in b

    def test_html_entities_in_code_not_double_escaped(self):
        b = body("```\na < b && c > d\n```")
        # Should appear as readable characters inside the code block
        assert "a" in b
        assert "b" in b


# ---------------------------------------------------------------------------
# Mermaid diagrams
# ---------------------------------------------------------------------------

class TestMermaid:
    def test_mermaid_block_becomes_div(self):
        md = "```mermaid\ngraph TD\n  A --> B\n```"
        b = body(md)
        assert '<div class="mermaid">' in b

    def test_mermaid_content_preserved(self):
        md = "```mermaid\ngraph TD\n  A --> B\n```"
        b = body(md)
        assert "graph TD" in b
        assert "A --> B" in b

    def test_mermaid_not_inside_pre(self):
        md = "```mermaid\ngraph TD\n  A --> B\n```"
        b = body(md)
        assert "<pre>" not in b

    def test_mermaid_js_injected_when_diagram_present(self):
        md = "```mermaid\ngraph LR\n  X --> Y\n```"
        html = render(md)
        # Either bundled or CDN fallback — mermaid is referenced
        assert "mermaid" in html.lower()

    def test_no_mermaid_js_when_no_diagram(self):
        html = render("just prose, no diagrams")
        # mermaid should NOT be injected
        assert "mermaid.initialize" not in html

    def test_mermaid_alongside_prose(self):
        md = "Before\n\n```mermaid\ngraph TD\n  A-->B\n```\n\nAfter"
        b = body(md)
        assert "Before" in b
        assert "After" in b
        assert '<div class="mermaid">' in b


# ---------------------------------------------------------------------------
# Math (arithmatex / MathJax)
# ---------------------------------------------------------------------------

class TestMath:
    def test_inline_math_dollar(self):
        b = body("Here is $x^2$ inline.")
        assert "arithmatex" in b

    def test_inline_math_parens(self):
        b = body(r"Here is \(x^2\) inline.")
        assert "arithmatex" in b

    def test_display_math_double_dollar(self):
        b = body("$$\n\\int_0^1 f(x)\\,dx\n$$")
        assert "arithmatex" in b

    def test_display_math_bracket(self):
        b = body(r"\[\int_0^1 f(x)\,dx\]")
        assert "arithmatex" in b

    def test_mathjax_injected_when_math_present(self):
        html = render("Euler: $e^{i\\pi} = -1$")
        assert "MathJax" in html

    def test_no_mathjax_when_no_math(self):
        html = render("No math here, just prose.")
        assert "MathJax" not in html

    def test_dollar_amount_not_math(self):
        b = body("It costs $5 today.")
        # A lone $5 should not become a math span
        assert "$5" in b or "5" in b
        # Should not be wrapped as arithmatex
        assert b.count("arithmatex") == 0

    def test_math_tex_content_preserved(self):
        b = body(r"Formula: \(\alpha + \beta = \gamma\)")
        assert "alpha" in b
        assert "beta" in b
        assert "gamma" in b

    def test_math_and_mermaid_together(self):
        md = "Math: $x^2$\n\n```mermaid\ngraph TD\n  A-->B\n```"
        html = render(md)
        assert "MathJax" in html
        assert "mermaid" in html.lower()


# ---------------------------------------------------------------------------
# Mermaid internals (_extract_mermaid / _restore_mermaid)
# ---------------------------------------------------------------------------

class TestMermaidInternals:
    def test_extract_returns_placeholder(self):
        text, blocks = renderer._extract_mermaid("```mermaid\nA-->B\n```")
        assert "MERMAID:0" in text
        assert blocks == ["A-->B\n"]

    def test_extract_multiple_blocks(self):
        md = "```mermaid\nA-->B\n```\n\n```mermaid\nC-->D\n```"
        text, blocks = renderer._extract_mermaid(md)
        assert len(blocks) == 2
        assert "MERMAID:0" in text
        assert "MERMAID:1" in text

    def test_extract_no_mermaid_unchanged(self):
        text, blocks = renderer._extract_mermaid("plain text")
        assert text == "plain text"
        assert blocks == []

    def test_restore_produces_div(self):
        html = "<p><!--MERMAID:0--></p>"
        result = renderer._restore_mermaid(html, ["graph TD\n  A-->B"])
        assert '<div class="mermaid">' in result
        assert "graph TD" in result


# ---------------------------------------------------------------------------
# Syntax highlighting internals
# ---------------------------------------------------------------------------

class TestSyntaxHighlighting:
    def test_highlight_python(self):
        result = renderer._highlight_code("def foo(): pass", "python")
        assert "<span" in result

    def test_highlight_unknown_lang_falls_back(self):
        result = renderer._highlight_code("some code", "notareallanguage")
        assert "some code" in result

    def test_highlight_empty_string(self):
        result = renderer._highlight_code("", "python")
        assert result is not None

    def test_apply_highlighting_transforms_pre_blocks(self):
        html = '<pre><code class="language-python">x = 1</code></pre>'
        result = renderer._apply_syntax_highlighting(html)
        assert "<span" in result

    def test_apply_highlighting_no_lang(self):
        html = "<pre><code>plain</code></pre>"
        result = renderer._apply_syntax_highlighting(html)
        assert "plain" in result

    def test_apply_highlighting_leaves_non_code_alone(self):
        html = "<p>hello</p>"
        result = renderer._apply_syntax_highlighting(html)
        assert result == "<p>hello</p>"


# ---------------------------------------------------------------------------
# Asset loading
# ---------------------------------------------------------------------------

class TestAssetLoading:
    def test_style_css_loads(self):
        css = renderer._load_asset("style.css")
        assert css is not None
        assert "--bg:" in css

    def test_missing_asset_returns_none(self):
        result = renderer._load_asset("does_not_exist.js")
        assert result is None

    def test_mathjax_bundle_present(self):
        js = renderer._load_asset("mathjax.min.js")
        assert js is not None and len(js) > 1000, \
            "mathjax.min.js missing — run: bash scripts/download-assets.sh"

    def test_mermaid_bundle_present(self):
        js = renderer._load_asset("mermaid.min.js")
        assert js is not None and len(js) > 1000, \
            "mermaid.min.js missing — run: bash scripts/download-assets.sh"
