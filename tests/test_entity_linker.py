"""
Tests for Financial Entity Linking & Relation Mining Engine.
"""

import pytest
from backend.entity_linker import EntityLinkingEngine
from backend.models import RelationType


@pytest.fixture
def linker():
    return EntityLinkingEngine()


def test_entity_linking_exact_ticker(linker):
    text = "NVIDIA Corporation (NVDA) reported record quarterly datacenter growth."
    res = linker.extract_and_link(text)
    assert res.total_mentions >= 1
    nvda_mentions = [m for m in res.mentions if m.matched_canonical.ticker == "NVDA"]
    assert len(nvda_mentions) >= 1
    assert nvda_mentions[0].matched_canonical.name == "NVIDIA Corporation"


def test_entity_linking_executives(linker):
    text = "Jensen Huang is the CEO of NVIDIA Corporation and delivered the keynote address."
    res = linker.extract_and_link(text)
    exec_mentions = [m for m in res.mentions if m.matched_canonical.canonical_id == "exec-jensen-huang"]
    assert len(exec_mentions) >= 1


def test_relation_extraction_supplies_to(linker):
    text = "ASML supplies equipment to Taiwan Semiconductor Manufacturing Company for chip production."
    res = linker.extract_and_link(text)
    supply_rels = [r for r in res.relations if r.relation_type == RelationType.SUPPLIES_TO]
    assert len(supply_rels) >= 1
    assert supply_rels[0].source_entity_id == "company-asml"
    assert supply_rels[0].target_entity_id == "company-tsm"


def test_relation_extraction_competes_with(linker):
    text = "Microsoft Corporation competes with Amazon.com, Inc. in cloud infrastructure services."
    res = linker.extract_and_link(text)
    compete_rels = [r for r in res.relations if r.relation_type == RelationType.COMPETES_WITH]
    assert len(compete_rels) >= 1
    assert compete_rels[0].source_entity_id == "company-msft"
    assert compete_rels[0].target_entity_id == "company-amzn"
