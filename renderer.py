import re
import os
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.sane_lists import SaneListsExtension
from markdown.extensions.smarty import SmartyExtension
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


class _HighlightingFencedCode(FencedCodeExtension):
    """FencedCode that routes blocks through Pygments."""

    def extendMarkdown(self, md):
        super().extendMarkdown(md)


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


def render(text):
    """Convert Markdown text to a full HTML document string."""
    text, mermaid_blocks = _extract_mermaid(text)

    md = markdown.Markdown(
        extensions=[
            FencedCodeExtension(),
            TableExtension(),
            Nl2BrExtension(),
            SaneListsExtension(),
            "markdown.extensions.attr_list",
            "markdown.extensions.def_list",
            "markdown.extensions.admonition",
            "markdown.extensions.toc",
            ArithmatexExtension(generic=True),
        ]
    )
    body = md.convert(text)
    body = _restore_mermaid(body, mermaid_blocks)
    body = _apply_syntax_highlighting(body)

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
<article>
{body}
</article>
</body>
</html>"""
