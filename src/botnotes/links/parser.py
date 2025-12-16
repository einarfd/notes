"""Wiki link parser utilities."""

import re
from dataclasses import dataclass


@dataclass
class WikiLink:
    """Represents a parsed wiki link."""

    target_path: str
    display_text: str | None
    line_number: int


# Regex pattern for wiki links: [[path]] or [[path|text]]
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def extract_links(content: str) -> list[WikiLink]:
    """Extract all wiki links from content.

    Args:
        content: The markdown content to parse

    Returns:
        List of WikiLink objects with position information
    """
    links = []
    for line_num, line in enumerate(content.split("\n"), start=1):
        for match in WIKI_LINK_PATTERN.finditer(line):
            target_path = match.group(1).strip()
            display_text = match.group(2).strip() if match.group(2) else None

            links.append(
                WikiLink(
                    target_path=target_path,
                    display_text=display_text,
                    line_number=line_num,
                )
            )

    return links


def replace_link_target(content: str, old_path: str, new_path: str) -> str:
    """Replace all wiki links pointing to old_path with new_path.

    Preserves display text if present:
    - [[old/path]] -> [[new/path]]
    - [[old/path|Display]] -> [[new/path|Display]]

    Args:
        content: The markdown content
        old_path: The path to replace
        new_path: The new path to use

    Returns:
        Updated content with links replaced
    """

    def replacer(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        display = match.group(2)

        if target == old_path:
            if display:
                return f"[[{new_path}|{display}]]"
            return f"[[{new_path}]]"
        return match.group(0)

    return WIKI_LINK_PATTERN.sub(replacer, content)
