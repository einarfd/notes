"""Markdown rendering with wiki link support and HTML sanitization."""

import re
from re import Match

import mistune
import nh3
from mistune import InlineState
from mistune.inline_parser import InlineParser

# Define safe HTML elements and attributes for nh3
ALLOWED_TAGS = {
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "code",
    "dd",
    "del",
    "dl",
    "dt",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "ins",
    "kbd",
    "li",
    "ol",
    "p",
    "pre",
    "q",
    "s",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "tt",
    "u",
    "ul",
    "var",
}

ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "class"},
    "abbr": {"title"},
    "*": {"class"},
}


# Wiki link regex for manual parsing inside the match
WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


class WikiLinkRenderer(mistune.HTMLRenderer):
    """HTML renderer with wiki link support."""

    def wiki_link(self, target: str, display: str) -> str:
        """Render a wiki link as an HTML anchor tag."""
        escaped_display = mistune.escape(display)
        return f'<a href="/notes/{target}" class="wiki-link">{escaped_display}</a>'


def parse_wiki_link(
    inline: InlineParser, m: Match[str], state: InlineState
) -> int:
    """Parse a wiki link match and add token to state."""
    full_match = m.group(0)
    # Parse the wiki link manually from the match
    inner = WIKI_LINK_RE.match(full_match)
    if inner:
        target = inner.group(1).strip()
        display = inner.group(2)
        display = display.strip() if display else target

        state.append_token(
            {
                "type": "wiki_link",
                "attrs": {"target": target, "display": display},
            }
        )
    return m.end()


def wiki_link_plugin(md: mistune.Markdown) -> None:
    """Mistune plugin to parse wiki links [[path]] and [[path|text]]."""
    # Use non-capturing groups in the pattern since mistune wraps in a named group
    md.inline.register(
        "wiki_link",
        r"\[\[(?:[^\]|]+)(?:\|(?:[^\]]+))?\]\]",
        parse_wiki_link,
        before="link",
    )


def create_markdown_renderer() -> mistune.Markdown:
    """Create a configured mistune Markdown renderer."""
    renderer = WikiLinkRenderer(escape=False)
    md = mistune.Markdown(renderer=renderer, plugins=[wiki_link_plugin])
    return md


# Module-level renderer instance (singleton pattern)
_markdown_renderer: mistune.Markdown | None = None


def get_markdown_renderer() -> mistune.Markdown:
    """Get or create the markdown renderer (singleton pattern)."""
    global _markdown_renderer
    if _markdown_renderer is None:
        _markdown_renderer = create_markdown_renderer()
    return _markdown_renderer


def render_markdown(content: str | None) -> str:
    """Render markdown content to sanitized HTML.

    Args:
        content: Raw markdown text with optional wiki links

    Returns:
        Sanitized HTML string
    """
    if not content:
        return ""

    # Step 1: Convert markdown to HTML (including wiki links)
    md = get_markdown_renderer()
    html = md(content)
    assert isinstance(html, str)  # Markdown always returns str for string input

    # Step 2: Sanitize HTML to prevent XSS
    clean_html: str = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel="noopener noreferrer",
    )

    return clean_html
