"""
Prerequisite Graph Service — Phase 3.

Builds a DAG from the curriculum CONCEPTS data (education.py) and any
DB-stored relationships. Cycle detection excludes problem nodes.

The curriculum graph is cached with lru_cache (read-only, immutable between requests).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List, Set, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ── Graph build ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_curriculum_edges() -> Dict[str, List[str]]:
    """
    Load prerequisite edges from the curriculum static data.
    Returns {concept_id: [prerequisite_concept_id, ...]}
    Cached indefinitely (static data).
    """
    try:
        from app.api.education import CONCEPTS
        graph: Dict[str, List[str]] = {}
        for c in CONCEPTS:
            cid = c.get("id") or c.get("slug") or ""
            prereqs = c.get("prerequisites") or []
            graph[cid] = [str(p) for p in prereqs]
        return graph
    except Exception as exc:
        logger.error(f"[prerequisite_graph] failed to load curriculum: {exc}")
        return {}


def build_curriculum_graph() -> Dict[str, List[str]]:
    """
    Build the prerequisite graph from curriculum + detect/exclude cycles.
    Returns safe DAG: {concept_id: [prerequisite_concept_ids]}
    """
    raw = dict(_get_curriculum_edges())
    cycles = detect_cycles(raw)
    if cycles:
        logger.warning(f"[prerequisite_graph] cycles detected involving: {cycles}. Excluding from graph.")
        for cid in cycles:
            raw.pop(cid, None)
        # Also remove cycle nodes from other nodes' prereq lists
        for cid in list(raw.keys()):
            raw[cid] = [p for p in raw[cid] if p not in cycles]
    return raw


def get_prerequisites(concept_id: str) -> List[str]:
    """Return direct prerequisite concept IDs for concept_id. Empty list if none."""
    graph = build_curriculum_graph()
    return graph.get(concept_id, [])


def get_dependents(concept_id: str) -> List[str]:
    """Return all concept IDs that directly depend on concept_id."""
    graph = build_curriculum_graph()
    return [cid for cid, prereqs in graph.items() if concept_id in prereqs]


def detect_cycles(graph: Dict[str, List[str]]) -> Set[str]:
    """
    DFS-based cycle detection.
    Returns the set of all concept IDs involved in any cycle.
    """
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    cycle_nodes: Set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbour in graph.get(node, []):
            if neighbour not in visited:
                if dfs(neighbour):
                    cycle_nodes.add(neighbour)
                    return True
            elif neighbour in rec_stack:
                cycle_nodes.add(neighbour)
                cycle_nodes.add(node)
                return True
        rec_stack.discard(node)
        return False

    for node in list(graph.keys()):
        if node not in visited:
            dfs(node)

    return cycle_nodes


# ── DB-aware mastery check ─────────────────────────────────────────────────────

PREREQUISITE_MASTERY_THRESHOLD: float = 60.0


async def is_prerequisite_mastered(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
) -> bool:
    """
    Returns True when all direct prerequisites of concept_id have
    mastery_score ≥ PREREQUISITE_MASTERY_THRESHOLD for the given user,
    or when concept_id has no direct prerequisites.

    Returns True for unknown concept_id (fail-open: don't block access to unknown concepts).
    """
    prereqs = get_prerequisites(concept_id)
    if not prereqs:
        return True

    from app.models.academic import ConceptMastery
    rows = (
        await db.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.concept_id.in_(prereqs),
            )
        )
    ).scalars().all()

    mastery_map = {r.concept_id: (r.mastery_score or 0.0) for r in rows}
    for pid in prereqs:
        if mastery_map.get(pid, 0.0) < PREREQUISITE_MASTERY_THRESHOLD:
            return False
    return True


async def get_unmastered_prerequisites(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
) -> List[str]:
    """Return list of prerequisite concept IDs that are not yet mastered."""
    prereqs = get_prerequisites(concept_id)
    if not prereqs:
        return []
    from app.models.academic import ConceptMastery
    rows = (
        await db.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.concept_id.in_(prereqs),
            )
        )
    ).scalars().all()
    mastery_map = {r.concept_id: (r.mastery_score or 0.0) for r in rows}
    return [p for p in prereqs if mastery_map.get(p, 0.0) < PREREQUISITE_MASTERY_THRESHOLD]
