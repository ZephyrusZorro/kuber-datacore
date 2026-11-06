"""
Kuber Data Core (कुबेर) — Crawl4AI-Style DOM Pruning & Markdown Engine
High-efficiency HTML boilerplate elimination, text-to-link density pruning,
BM25 content ranking, and semantic heading-aware chunking.
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup, Tag, NavigableString
from backend.models import (
    FilterStrategy,
    DOMPruneRequest,
    DOMPruneResponse,
    TextChunk
)


class DOMPruningEngine:
    """
    Intelligent DOM pruning and markdown synthesizer designed for
    converting bloated financial web pages into clean LLM-ready markdown.
    """

    STRIP_TAGS = {
        "script", "style", "noscript", "iframe", "svg", "canvas",
        "nav", "footer", "aside", "form", "button", "select", "input",
        "header", "video", "audio", "map", "object", "embed"
    }

    BOILERPLATE_CLASS_REGEX = re.compile(
        r"(ad-|advertisement|banner|cookie|popup|modal|newsletter|social-share|sidebar|widget|promo|sponsored|tracker|disclaimer-footer)",
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def prune_and_convert(
        self,
        raw_html: str,
        strategy: FilterStrategy = FilterStrategy.PRUNING_LXML,
        query_context: Optional[str] = None,
        chunk_size_words: int = 400,
        chunk_overlap_words: int = 50
    ) -> DOMPruneResponse:
        raw_char_count = len(raw_html)

        # Parse HTML safely
        soup = BeautifulSoup(raw_html, "html.parser")

        # Step 1: Strip unwanted tags
        for tag in soup.find_all(self.STRIP_TAGS):
            tag.decompose()

        # Step 2: Strip class/id matching boilerplate regex
        for tag in soup.find_all(True):
            attrs_str = " ".join(tag.get("class", [])) + " " + str(tag.get("id", ""))
            if self.BOILERPLATE_CLASS_REGEX.search(attrs_str):
                # Only decompose if not the main container
                if tag.name not in ["main", "article", "body"]:
                    tag.decompose()

        # Step 3: Text-to-link density pruning (navigational list elimination)
        self._prune_high_link_density_elements(soup)

        # Step 4: Convert retained tree to clean structured markdown
        body_tag = soup.body if soup.body else soup
        markdown_text = self._convert_tag_to_markdown(body_tag)

        # Clean excess blank lines
        markdown_text = re.sub(r"\n{3,}", "\n\n", markdown_text).strip()

        # Step 5: Apply strategy (BM25 filtering or chunking)
        final_markdown = markdown_text
        chunks: List[TextChunk] = []

        if strategy == FilterStrategy.BM25_RELEVANCE and query_context:
            final_markdown = self._apply_bm25_filter(markdown_text, query_context)
        elif strategy == FilterStrategy.TOKEN_WINDOW_CHUNK:
            chunks = self._chunk_markdown(markdown_text, chunk_size_words, chunk_overlap_words)

        cleaned_char_count = len(final_markdown)
        compression_ratio = 0.0
        if raw_char_count > 0:
            compression_ratio = round((1.0 - (cleaned_char_count / raw_char_count)) * 100.0, 2)

        return DOMPruneResponse(
            strategy=strategy,
            raw_char_count=raw_char_count,
            cleaned_char_count=cleaned_char_count,
            compression_ratio_pct=compression_ratio,
            markdown_content=final_markdown,
            chunks=chunks,
            extracted_metadata={
                "title": soup.title.get_text().strip() if soup.title else "Untitled Financial Document",
                "h1_headers": [h.get_text().strip() for h in soup.find_all("h1")],
                "table_count": len(soup.find_all("table")),
            }
        )

    def _prune_high_link_density_elements(self, soup: BeautifulSoup) -> None:
        """Removes blocks where anchor tags comprise > 50% of text (e.g. side menus)."""
        candidates = soup.find_all(["div", "section", "ul"])
        for el in candidates:
            total_text = el.get_text(strip=True)
            if not total_text or len(total_text) > 400:
                continue

            link_text_len = sum(len(a.get_text(strip=True)) for a in el.find_all("a"))
            if total_text:
                density = link_text_len / len(total_text)
                if density > 0.55:
                    el.decompose()

    def _convert_tag_to_markdown(self, element: Tag) -> str:
        """Recursive conversion of DOM elements into Markdown."""
        if isinstance(element, NavigableString):
            text = str(element).strip()
            return f" {text} " if text else ""

        tag_name = element.name.lower() if element.name else ""

        # Headings
        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag_name[1])
            heading_text = element.get_text().strip()
            return f"\n\n{'#' * level} {heading_text}\n\n"

        # Paragraphs and divs
        if tag_name in ["p"]:
            inner = "".join(self._convert_tag_to_markdown(child) for child in element.children).strip()
            return f"\n\n{inner}\n\n" if inner else ""

        # Blockquote
        if tag_name == "blockquote":
            inner = element.get_text().strip()
            return f"\n\n> {inner}\n\n"

        # Lists
        if tag_name in ["ul", "ol"]:
            items = []
            for idx, li in enumerate(element.find_all("li", recursive=False)):
                prefix = f"{idx + 1}." if tag_name == "ol" else "*"
                li_text = li.get_text().strip()
                if li_text:
                    items.append(f"{prefix} {li_text}")
            return "\n" + "\n".join(items) + "\n\n"

        # Tables (GFM Markdown Table parser)
        if tag_name == "table":
            return self._convert_table_to_markdown(element)

        # Code blocks
        if tag_name == "pre" or tag_name == "code":
            code_text = element.get_text()
            return f"\n```\n{code_text}\n```\n"

        # Bold / Italic
        if tag_name in ["strong", "b"]:
            inner = element.get_text().strip()
            return f"**{inner}**" if inner else ""
        if tag_name in ["em", "i"]:
            inner = element.get_text().strip()
            return f"*{inner}*" if inner else ""

        # Recursive for containers
        return "".join(self._convert_tag_to_markdown(child) for child in element.children)

    def _convert_table_to_markdown(self, table_tag: Tag) -> str:
        """Extracts HTML table rows into clean GitHub Flavored Markdown table."""
        rows = table_tag.find_all("tr")
        if not rows:
            return ""

        table_matrix: List[List[str]] = []
        for r in rows:
            cells = r.find_all(["th", "td"])
            row_data = [re.sub(r"\s+", " ", cell.get_text().strip()) for cell in cells]
            if any(row_data):
                table_matrix.append(row_data)

        if not table_matrix:
            return ""

        # Normalize column count
        col_count = max(len(r) for r in table_matrix)
        for r in table_matrix:
            while len(r) < col_count:
                r.append("")

        md_lines = []
        # Header row
        header = table_matrix[0]
        md_lines.append("| " + " | ".join(header) + " |")
        md_lines.append("| " + " | ".join(["---"] * col_count) + " |")

        for row in table_matrix[1:]:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n\n" + "\n".join(md_lines) + "\n\n"

    def _apply_bm25_filter(self, markdown_text: str, query: str) -> str:
        """
        Lightweight BM25 paragraph ranking.
        Retains the top most relevant paragraphs to the query context.
        """
        paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]
        if not paragraphs:
            return markdown_text

        query_terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        if not query_terms:
            return markdown_text

        scored_paras: List[Tuple[float, str]] = []
        for p in paragraphs:
            score = 0.0
            p_lower = p.lower()
            words = re.findall(r"\w+", p_lower)
            doc_len = len(words)
            if doc_len == 0:
                continue

            for term in query_terms:
                tf = words.count(term)
                if tf > 0:
                    # BM25 term weighting formula
                    k1 = 1.2
                    b = 0.75
                    avgdl = 40.0
                    term_score = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                    score += term_score

            scored_paras.append((score, p))

        # Sort by relevance and retain top 65% of paragraphs with score > 0
        positive_scored = [p for p in scored_paras if p[0] > 0]
        positive_scored.sort(key=lambda x: x[0], reverse=True)

        if not positive_scored:
            return markdown_text

        top_k = max(3, int(len(positive_scored) * 0.75))
        retained = [p[1] for p in positive_scored[:top_k]]
        return "\n\n".join(retained)

    def _chunk_markdown(self, markdown_text: str, chunk_size: int, overlap: int) -> List[TextChunk]:
        """
        Semantic chunker that splits document into overlapping word windows,
        tracking the closest preceding heading for contextual clarity.
        """
        lines = markdown_text.split("\n")
        chunks: List[TextChunk] = []
        current_heading = "Overview"
        current_words: List[str] = []

        chunk_idx = 1
        for line in lines:
            if line.startswith("#"):
                current_heading = line.lstrip("#").strip()

            words = line.split()
            current_words.extend(words)

            while len(current_words) >= chunk_size:
                chunk_slice = current_words[:chunk_size]
                chunk_text = " ".join(chunk_slice)
                chunks.append(TextChunk(
                    chunk_index=chunk_idx,
                    heading_context=current_heading,
                    word_count=len(chunk_slice),
                    char_count=len(chunk_text),
                    content=chunk_text
                ))
                chunk_idx += 1
                # Advance with overlap
                current_words = current_words[chunk_size - overlap:]

        # Remainder chunk
        if current_words:
            chunk_text = " ".join(current_words)
            chunks.append(TextChunk(
                chunk_index=chunk_idx,
                heading_context=current_heading,
                word_count=len(current_words),
                char_count=len(chunk_text),
                content=chunk_text
            ))

        return chunks
