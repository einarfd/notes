"""Tests for wiki link parser."""

from notes.links.parser import extract_links, replace_link_target


class TestExtractLinks:
    """Tests for extract_links function."""

    def test_extract_simple_link(self):
        """Test extracting a simple wiki link."""
        content = "See [[projects/wiki-ai]]"
        links = extract_links(content)

        assert len(links) == 1
        assert links[0].target_path == "projects/wiki-ai"
        assert links[0].display_text is None
        assert links[0].line_number == 1

    def test_extract_link_with_display_text(self):
        """Test extracting a wiki link with display text."""
        content = "See [[projects/wiki-ai|Wiki AI Project]]"
        links = extract_links(content)

        assert len(links) == 1
        assert links[0].target_path == "projects/wiki-ai"
        assert links[0].display_text == "Wiki AI Project"
        assert links[0].line_number == 1

    def test_extract_multiple_links(self):
        """Test extracting multiple wiki links from a single line."""
        content = "Link [[a]] and [[b|B]] here"
        links = extract_links(content)

        assert len(links) == 2
        assert links[0].target_path == "a"
        assert links[0].display_text is None
        assert links[1].target_path == "b"
        assert links[1].display_text == "B"

    def test_extract_links_multiline(self):
        """Test extracting links from multiple lines."""
        content = "Line 1 [[a]]\nLine 2\nLine 3 [[b]]"
        links = extract_links(content)

        assert len(links) == 2
        assert links[0].target_path == "a"
        assert links[0].line_number == 1
        assert links[1].target_path == "b"
        assert links[1].line_number == 3

    def test_extract_no_links(self):
        """Test extracting from content with no links."""
        content = "No links here, just plain text."
        links = extract_links(content)

        assert links == []

    def test_extract_link_strips_whitespace(self):
        """Test that paths are stripped of whitespace."""
        content = "See [[ projects/wiki-ai ]]"
        links = extract_links(content)

        assert len(links) == 1
        assert links[0].target_path == "projects/wiki-ai"

    def test_extract_link_with_nested_path(self):
        """Test extracting links with deeply nested paths."""
        content = "See [[projects/wiki-ai/research/mcp]]"
        links = extract_links(content)

        assert len(links) == 1
        assert links[0].target_path == "projects/wiki-ai/research/mcp"

    def test_extract_multiple_links_per_line(self):
        """Test extracting multiple links on the same line."""
        content = "Related: [[a]], [[b]], and [[c|C Note]]"
        links = extract_links(content)

        assert len(links) == 3
        assert all(link.line_number == 1 for link in links)
        assert links[0].target_path == "a"
        assert links[1].target_path == "b"
        assert links[2].target_path == "c"
        assert links[2].display_text == "C Note"


class TestReplaceLinkTarget:
    """Tests for replace_link_target function."""

    def test_replace_simple_link(self):
        """Test replacing a simple link target."""
        content = "See [[old/path]] for details"
        result = replace_link_target(content, "old/path", "new/path")

        assert result == "See [[new/path]] for details"

    def test_replace_link_preserves_display_text(self):
        """Test that display text is preserved when replacing."""
        content = "See [[old/path|Display Text]]"
        result = replace_link_target(content, "old/path", "new/path")

        assert result == "See [[new/path|Display Text]]"

    def test_replace_link_no_match(self):
        """Test that non-matching links are not modified."""
        content = "See [[other/path]]"
        result = replace_link_target(content, "old/path", "new/path")

        assert result == "See [[other/path]]"

    def test_replace_multiple_links(self):
        """Test replacing multiple instances of the same link."""
        content = "Link [[old/path]] and again [[old/path|Display]]"
        result = replace_link_target(content, "old/path", "new/path")

        assert result == "Link [[new/path]] and again [[new/path|Display]]"

    def test_replace_only_exact_match(self):
        """Test that only exact path matches are replaced."""
        content = "Links: [[old/path]] and [[old/path/sub]]"
        result = replace_link_target(content, "old/path", "new/path")

        # Only exact match is replaced, not partial prefix match
        assert "[[new/path]]" in result
        assert "[[old/path/sub]]" in result

    def test_replace_multiline(self):
        """Test replacing links across multiple lines."""
        content = "Line 1 [[old/path]]\nLine 2 [[other]]\nLine 3 [[old/path|Text]]"
        result = replace_link_target(content, "old/path", "new/path")

        assert "Line 1 [[new/path]]" in result
        assert "[[other]]" in result
        assert "[[new/path|Text]]" in result

    def test_replace_empty_content(self):
        """Test replacing in empty content."""
        content = ""
        result = replace_link_target(content, "old/path", "new/path")

        assert result == ""

    def test_replace_no_links_content(self):
        """Test replacing when content has no links."""
        content = "Just plain text with no links."
        result = replace_link_target(content, "old/path", "new/path")

        assert result == "Just plain text with no links."
