"""Original-edge graph recovery, reimplemented without native dependencies.

Algorithm lineage: Vesuvius Lab's MIT ScrollFiesta experimental graft helper.
This module does not detect geometric conflicts; complete constraints are input.
"""
from collections import Counter, deque


def boundary_graft(labels, adjacency, conflicts, *, complete):
    """Return new labels atomically; never modify the caller's containers.

    Owners with at least 16 source faces stay fixed. Small-owner faces may
    attach along supplied original edges if no recorded conflict is joined.
    Incomplete evidence, invalid input and over-budget input fail closed.
    """
    original = list(labels)
    result = {"labels": original, "recovered": 0, "accepted": False}
    n = len(original)
    if complete is not True:
        return dict(result, reason="incomplete_conflict_evidence")
    if not n or n > 100000 or any(type(x) is not int or x < 0 or x >= n for x in original):
        return dict(result, reason="invalid_labels")
    if 512 * (n + len(adjacency) + len(conflicts)) > 128 * 1024**2:
        return dict(result, reason="scratch_budget")
    for edges in (adjacency, conflicts):
        if any(len(e) != 2 or any(type(x) is not int or x < 0 or x >= n for x in e) for e in edges):
            return dict(result, reason="invalid_pair")
    if any(original[a] == original[b] for a, b in conflicts):
        return dict(result, reason="preexisting_joined_conflict")
    counts = Counter(original)
    assigned = [x if counts[x] >= 16 else -1 for x in original]
    neighbors = [set() for _ in original]
    blocked = [set() for _ in original]
    for a, b in adjacency:
        if a == b:
            return dict(result, reason="invalid_self_adjacency")
        neighbors[a].add(b); neighbors[b].add(a)
    for a, b in conflicts:
        blocked[a].add(b); blocked[b].add(a)
    # Sorted sets give deterministic original-face traversal and owner ties.
    neighbors = [sorted(row) for row in neighbors]
    pending = deque(i for i in range(n) if assigned[i] < 0 and any(assigned[j] >= 0 for j in neighbors[i]))
    queued = set(pending)
    witnesses = []
    while pending:
        face = pending.popleft(); queued.remove(face)
        if assigned[face] >= 0:
            continue
        owners = Counter(assigned[j] for j in neighbors[face] if assigned[j] >= 0)
        safe = [owner for owner in owners if all(assigned[j] != owner for j in blocked[face])]
        if not safe:
            continue
        owner = min(safe, key=lambda x: (-owners[x], x))
        assigned[face] = owner
        witnesses.append({"face": face, "owner": owner, "shared_neighbors": [j for j in neighbors[face] if assigned[j] == owner]})
        for j in neighbors[face]:
            if assigned[j] < 0 and j not in queued:
                pending.append(j); queued.add(j)
    final = [owner if owner >= 0 else old for owner, old in zip(assigned, original)]
    if any(final[a] == final[b] for a, b in conflicts):
        return dict(result, reason="final_constraint_rejection")
    return {"labels": final, "recovered": len(witnesses), "accepted": True,
            "witnesses": witnesses, "reason": "completed",
            "scope": "Original-edge and supplied-conflict graph only; not an anatomical or geometric intersection certificate."}
