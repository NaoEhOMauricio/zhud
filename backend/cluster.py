"""
K-means player clustering (pure Python, zero dependencies).
Groups players into 6 behavioral clusters based on VPIP, PFR, AF, 3BET.
Clusters are sorted by aggression (tight/passive → loose/aggressive).
"""
import math
import random

K = 6

CLUSTER_NAMES = [
    "Nit Extremo",     # 0 — tightest, lowest aggression
    "Nit / TAG",       # 1
    "TAG Sólido",      # 2
    "LAG Controlado",  # 3
    "LAG Agressivo",   # 4
    "Maniac / Station",# 5 — loosest
]


def _norm(points: list) -> list:
    """Min-max normalize each feature column."""
    if not points:
        return points
    n_feat = len(points[0])
    mins = [min(p[i] for p in points) for i in range(n_feat)]
    maxs = [max(p[i] for p in points) for i in range(n_feat)]
    ranges = [max(mx - mn, 1e-9) for mn, mx in zip(mins, maxs)]
    return [[(p[i] - mins[i]) / ranges[i] for i in range(n_feat)] for p in points]


def _dist(a: list, b: list) -> float:
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def _kmeans_run(pts_norm: list, k: int, max_iter: int = 60):
    """Single K-means++ run. Returns (labels, centroids, inertia)."""
    n = len(pts_norm)

    # K-means++ initialization
    centroids = [random.choice(pts_norm)]
    for _ in range(k - 1):
        dists = [min(_dist(p, c) for c in centroids) for p in pts_norm]
        total = sum(dists)
        if total == 0:
            centroids.append(random.choice(pts_norm))
            continue
        r = random.uniform(0, total)
        cum = 0.0
        chosen = pts_norm[-1]
        for p, d in zip(pts_norm, dists):
            cum += d
            if cum >= r:
                chosen = p
                break
        centroids.append(chosen)

    labels = [0] * n
    for _ in range(max_iter):
        new_labels = [
            min(range(k), key=lambda i, p=p: _dist(p, centroids[i]))
            for p in pts_norm
        ]
        if new_labels == labels:
            break
        labels = new_labels
        for i in range(k):
            cluster_pts = [pts_norm[j] for j in range(n) if labels[j] == i]
            if cluster_pts:
                centroids[i] = [
                    sum(x) / len(x) for x in zip(*cluster_pts)
                ]

    inertia = sum(
        _dist(pts_norm[j], centroids[labels[j]]) ** 2 for j in range(n)
    )
    return labels, centroids, inertia


def run_clustering(players: list) -> list:
    """
    Cluster players by (vpip, pfr, af, threebet).
    Adds 'cluster_id' and 'cluster_label' to each player dict in-place.
    Only clusters players with >= 20 hands; others get cluster_id=-1.

    Returns the same list with clusters assigned.
    """
    eligible = [(i, p) for i, p in enumerate(players) if p.get("hands", 0) >= 20]

    if len(eligible) < K:
        for p in players:
            p.setdefault("cluster_id", -1)
            p.setdefault("cluster_label", "")
        return players

    # Feature vectors: [vpip, pfr, af*10, threebet]  (scale AF to similar magnitude)
    raw_pts = [
        [p["vpip"], p["pfr"], p.get("af", 0) * 10, p.get("threebet", 0)]
        for _, p in eligible
    ]
    pts_norm = _norm(raw_pts)

    best_labels = None
    best_inertia = float("inf")
    for _ in range(7):  # multiple restarts for stability
        labels, _, inertia = _kmeans_run(pts_norm, K)
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels

    # Sort clusters by mean aggression (vpip + pfr) so label 0 = most passive
    cluster_vpip_pfr: dict = {}
    for j, (_, p) in enumerate(eligible):
        cid = best_labels[j]
        cluster_vpip_pfr.setdefault(cid, []).append(p["vpip"] + p["pfr"])

    cluster_mean = {
        cid: sum(vals) / len(vals) for cid, vals in cluster_vpip_pfr.items()
    }
    sorted_ids = sorted(cluster_mean, key=lambda x: cluster_mean[x])
    remap = {old: new for new, old in enumerate(sorted_ids)}

    for j, (orig_i, p) in enumerate(eligible):
        mapped = remap[best_labels[j]]
        p["cluster_id"] = mapped
        p["cluster_label"] = CLUSTER_NAMES[min(mapped, len(CLUSTER_NAMES) - 1)]

    for p in players:
        p.setdefault("cluster_id", -1)
        p.setdefault("cluster_label", "")

    return players
