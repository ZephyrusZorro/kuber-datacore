"""
Kuber Data Core (कुबेर) — Financial Named Entity Linking & Relation Extractor
FIBO/SEC-aligned canonical disambiguation, fuzzy alias resolution,
and syntactic pattern-driven relationship mining.
"""

import re
import difflib
from typing import List, Dict, Any, Optional, Tuple
from backend.models import (
    CanonicalEntity,
    EntityType,
    RelationType,
    EntityMention,
    ExtractedRelation,
    EntityLinkingRequest,
    EntityLinkingResponse
)
from backend.sample_market_data import (
    CANONICAL_COMPANIES,
    CANONICAL_EXECUTIVES
)


class EntityLinkingEngine:
    """
    Financial Named Entity Recognition (NER) and Entity Disambiguation (NEL)
    engine targeting technology ecosystems, SEC filings, and supply chains.
    """

    RELATION_PATTERNS = [
        # SUPPLIES_TO patterns
        (
            re.compile(r"([A-Z][A-Za-z0-9\.\s&]+?)\s+(?:supplies|supplying|provides|ships chips to|delivers equipment to|manufactures cutting-edge silicon for|manufactures advanced lithography semiconductor chips for)\s+([A-Z][A-Za-z0-9\.\s&]+)", re.IGNORECASE),
            RelationType.SUPPLIES_TO,
            0.92
        ),
        (
            re.compile(r"([A-Z][A-Za-z0-9\.\s&]+?)\s+rel(?:ies|y)\s+on\s+([A-Z][A-Za-z0-9\.\s&]+?)\s+(?:to manufacture|for wafer|for extreme ultraviolet|as single-source foundry)", re.IGNORECASE),
            RelationType.SUPPLIES_TO, # Target supplies to Source (inverted in extraction)
            0.90
        ),
        # COMPETES_WITH patterns
        (
            re.compile(r"([A-Z][A-Za-z0-9\.\s&]+?)\s+(?:competes with|competes against|rivals|battles with|competing in)\s+([A-Z][A-Za-z0-9\.\s&]+)", re.IGNORECASE),
            RelationType.COMPETES_WITH,
            0.88
        ),
        # OFFICER_OF patterns
        (
            re.compile(r"([A-Z][A-Za-z\s]+?)\s+(?:is the CEO of|serves as Chief Executive of|President and CEO of|founder and CEO of)\s+([A-Z][A-Za-z0-9\.\s&]+)", re.IGNORECASE),
            RelationType.OFFICER_OF,
            0.95
        )
    ]

    def __init__(self):
        # Build canonical lookup lexicon
        self.all_canonicals: List[CanonicalEntity] = (
            list(CANONICAL_COMPANIES.values()) + list(CANONICAL_EXECUTIVES.values())
        )

    def extract_and_link(self, text: str, confidence_threshold: float = 0.70) -> EntityLinkingResponse:
        mentions: List[EntityMention] = []
        found_entity_ids = set()

        # Phase 1: Exact and alias regex scanning
        for canonical in self.all_canonicals:
            aliases_to_search = [canonical.name] + canonical.aliases
            if canonical.ticker:
                aliases_to_search.append(canonical.ticker)

            for alias in set(aliases_to_search):
                if len(alias) < 2:
                    continue

                pattern = r"\b" + re.escape(alias) + r"\b"
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    start = match.start()
                    end = match.end()
                    matched_str = match.group(0)

                    # Compute confidence
                    confidence = 1.0 if matched_str == canonical.name or (canonical.ticker and matched_str == canonical.ticker) else 0.90

                    if confidence >= confidence_threshold:
                        # Avoid overlapping identical mentions
                        overlap = any(
                            m.start_char == start and m.end_char == end and m.matched_canonical.canonical_id == canonical.canonical_id
                            for m in mentions
                        )
                        if not overlap:
                            mentions.append(EntityMention(
                                raw_text=matched_str,
                                start_char=start,
                                end_char=end,
                                confidence=confidence,
                                matched_canonical=canonical
                            ))
                            found_entity_ids.add(canonical.canonical_id)

        # Phase 2: Fuzzy matching for variant company spellings
        words = re.findall(r"\b[A-Z][a-zA-Z0-9\.\-]{2,}\b", text)
        for w in set(words):
            if any(m.raw_text.lower() == w.lower() for m in mentions):
                continue
            for canonical in CANONICAL_COMPANIES.values():
                ratio = difflib.SequenceMatcher(None, w.lower(), canonical.name.lower()).ratio()
                if ratio >= 0.82 and ratio >= confidence_threshold:
                    match_pos = text.find(w)
                    if match_pos != -1:
                        mentions.append(EntityMention(
                            raw_text=w,
                            start_char=match_pos,
                            end_char=match_pos + len(w),
                            confidence=round(ratio, 2),
                            matched_canonical=canonical
                        ))
                        found_entity_ids.add(canonical.canonical_id)

        # Sort mentions by appearance in document
        mentions.sort(key=lambda m: m.start_char)

        # Phase 3: Relation extraction between detected entities
        relations = self._extract_relations(text, mentions)

        return EntityLinkingResponse(
            total_mentions=len(mentions),
            unique_entities=len(found_entity_ids),
            mentions=mentions,
            relations=relations
        )

    def _extract_relations(self, text: str, mentions: List[EntityMention]) -> List[ExtractedRelation]:
        relations: List[ExtractedRelation] = []
        entity_by_canonical = {m.matched_canonical.canonical_id: m.matched_canonical for m in mentions}

        # Check for sentence-level co-occurrence and syntactic patterns
        sentences = re.split(r"[.\n]\s+", text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            for pattern, rel_type, base_conf in self.RELATION_PATTERNS:
                matches = pattern.finditer(sentence)
                for match in matches:
                    src_phrase = match.group(1).strip()
                    tgt_phrase = match.group(2).strip()

                    src_canonical = self._resolve_phrase_to_canonical(src_phrase)
                    tgt_canonical = self._resolve_phrase_to_canonical(tgt_phrase)

                    if src_canonical and tgt_canonical and src_canonical.canonical_id != tgt_canonical.canonical_id:
                        # Specific handling for "X relies on Y to manufacture..."
                        if "relies on" in match.group(0).lower() or "rely on" in match.group(0).lower():
                            # Y supplies to X
                            rel = ExtractedRelation(
                                source_entity_id=tgt_canonical.canonical_id,
                                target_entity_id=src_canonical.canonical_id,
                                relation_type=RelationType.SUPPLIES_TO,
                                confidence=base_conf,
                                evidence_quote=match.group(0).strip(),
                                weight=1.0
                            )
                        else:
                            rel = ExtractedRelation(
                                source_entity_id=src_canonical.canonical_id,
                                target_entity_id=tgt_canonical.canonical_id,
                                relation_type=rel_type,
                                confidence=base_conf,
                                evidence_quote=match.group(0).strip(),
                                weight=1.0
                            )

                        if not any(
                            r.source_entity_id == rel.source_entity_id and
                            r.target_entity_id == rel.target_entity_id and
                            r.relation_type == rel.relation_type
                            for r in relations
                        ):
                            relations.append(rel)

        return relations

    def _resolve_phrase_to_canonical(self, phrase: str) -> Optional[CanonicalEntity]:
        phrase_clean = phrase.lower().strip()
        for c in self.all_canonicals:
            if phrase_clean == c.name.lower():
                return c
            if c.ticker and phrase_clean == c.ticker.lower():
                return c
            for alias in c.aliases:
                if phrase_clean == alias.lower() or alias.lower() in phrase_clean:
                    return c
        return None
