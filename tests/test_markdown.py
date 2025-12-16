"""Tests for markdown rendering."""

from botnotes.web.markdown import render_markdown


class TestRenderMarkdown:
    """Tests for render_markdown function."""

    def test_renders_heading(self) -> None:
        """Test heading is rendered to HTML."""
        result = render_markdown("# Hello")
        assert "<h1>Hello</h1>" in result

    def test_renders_bold(self) -> None:
        """Test bold text is rendered."""
        result = render_markdown("This is **bold** text.")
        assert "<strong>bold</strong>" in result

    def test_renders_italic(self) -> None:
        """Test italic text is rendered."""
        result = render_markdown("This is *italic* text.")
        assert "<em>italic</em>" in result

    def test_renders_inline_code(self) -> None:
        """Test inline code is rendered."""
        result = render_markdown("Use `code` here.")
        assert "<code>code</code>" in result

    def test_renders_code_block(self) -> None:
        """Test code blocks are rendered."""
        content = "```python\nprint('hello')\n```"
        result = render_markdown(content)
        assert "<pre>" in result
        assert "<code" in result  # May have class attribute

    def test_renders_list(self) -> None:
        """Test lists are rendered."""
        content = "- Item 1\n- Item 2\n- Item 3"
        result = render_markdown(content)
        assert "<ul>" in result
        assert "<li>" in result

    def test_renders_ordered_list(self) -> None:
        """Test ordered lists are rendered."""
        content = "1. First\n2. Second"
        result = render_markdown(content)
        assert "<ol>" in result
        assert "<li>" in result

    def test_renders_blockquote(self) -> None:
        """Test blockquotes are rendered."""
        result = render_markdown("> Quote text")
        assert "<blockquote>" in result

    def test_renders_link(self) -> None:
        """Test regular links are rendered."""
        result = render_markdown("[Click](https://example.com)")
        assert '<a href="https://example.com"' in result
        assert ">Click</a>" in result


class TestWikiLinks:
    """Tests for wiki link rendering."""

    def test_renders_simple_wiki_link(self) -> None:
        """Test simple wiki link [[path]] is rendered."""
        result = render_markdown("See [[projects/wiki-ai]] for details.")
        assert '<a href="/notes/projects/wiki-ai"' in result
        assert 'class="wiki-link"' in result
        assert ">projects/wiki-ai</a>" in result

    def test_renders_wiki_link_with_display_text(self) -> None:
        """Test wiki link with display text [[path|text]]."""
        result = render_markdown("See [[projects/wiki-ai|Wiki AI Project]].")
        assert '<a href="/notes/projects/wiki-ai"' in result
        assert ">Wiki AI Project</a>" in result

    def test_renders_multiple_wiki_links(self) -> None:
        """Test multiple wiki links in same content."""
        result = render_markdown("Links: [[a]] and [[b|B Note]]")
        assert '<a href="/notes/a"' in result
        assert '<a href="/notes/b"' in result
        assert ">a</a>" in result
        assert ">B Note</a>" in result

    def test_wiki_link_with_spaces_trimmed(self) -> None:
        """Test wiki link path is trimmed."""
        result = render_markdown("See [[ path/with/spaces ]]")
        assert 'href="/notes/path/with/spaces"' in result

    def test_wiki_link_in_list(self) -> None:
        """Test wiki link inside list item."""
        result = render_markdown("- See [[note1]]\n- And [[note2]]")
        assert '<a href="/notes/note1"' in result
        assert '<a href="/notes/note2"' in result

    def test_wiki_link_in_code_block_not_rendered(self) -> None:
        """Test wiki links inside code blocks are NOT converted."""
        content = "```\n[[not-a-link]]\n```"
        result = render_markdown(content)
        # Should appear as text, not as a link
        assert "[[not-a-link]]" in result
        assert 'href="/notes/not-a-link"' not in result

    def test_wiki_link_in_inline_code_not_rendered(self) -> None:
        """Test wiki links inside inline code are NOT converted."""
        content = "Use `[[not-a-link]]` syntax."
        result = render_markdown(content)
        assert "[[not-a-link]]" in result
        assert 'href="/notes/not-a-link"' not in result


class TestSanitization:
    """Tests for XSS prevention."""

    def test_sanitizes_script_tags(self) -> None:
        """Test script tags are removed."""
        content = "<script>alert('xss')</script>Hello"
        result = render_markdown(content)
        assert "<script>" not in result
        assert "alert" not in result
        assert "Hello" in result

    def test_sanitizes_onclick(self) -> None:
        """Test event handlers are removed."""
        content = '<a href="#" onclick="alert(1)">click</a>'
        result = render_markdown(content)
        assert "onclick" not in result

    def test_sanitizes_javascript_url(self) -> None:
        """Test javascript: URLs are removed."""
        content = '<a href="javascript:alert(1)">click</a>'
        result = render_markdown(content)
        assert "javascript:" not in result

    def test_sanitizes_img_onerror(self) -> None:
        """Test img onerror is removed."""
        content = '<img src="x" onerror="alert(1)">'
        result = render_markdown(content)
        assert "onerror" not in result

    def test_preserves_allowed_html(self) -> None:
        """Test that allowed HTML tags are preserved."""
        content = "**bold** and <em>italic</em>"
        result = render_markdown(content)
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_content(self) -> None:
        """Test empty content returns empty string."""
        assert render_markdown("") == ""

    def test_none_content(self) -> None:
        """Test None content returns empty string."""
        assert render_markdown(None) == ""

    def test_whitespace_only(self) -> None:
        """Test whitespace-only content."""
        result = render_markdown("   \n\n   ")
        # Should return something (possibly empty or whitespace)
        assert isinstance(result, str)

    def test_mixed_content(self) -> None:
        """Test complex mixed content."""
        content = """# Title

Some **bold** and *italic* text.

See [[wiki/link|Wiki Link]] for more info.

```python
code = "block"
```

- List item 1
- List item 2
"""
        result = render_markdown(content)
        assert "<h1>Title</h1>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert 'href="/notes/wiki/link"' in result
        assert ">Wiki Link</a>" in result
        assert "<pre>" in result
        assert "<ul>" in result
