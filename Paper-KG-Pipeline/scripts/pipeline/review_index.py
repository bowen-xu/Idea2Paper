import math
from typing import Dict, List, Optional, Iterable


class ReviewIndex:
    """Index papers by pattern_id and provide deterministic anchor selection."""

    def __init__(self, papers: List[Dict]):
        self.papers = papers or []
        self.pattern_to_papers: Dict[str, List[Dict]] = {}
        self.paper_id_to_summary: Dict[str, Dict] = {}
        self.global_scores_sorted: List[float] = []
        self._build_index()

    def _build_index(self):
        for paper in self.papers:
            pattern_id = paper.get("pattern_id", "")
            paper_id = paper.get("paper_id", "")
            if not pattern_id or not paper_id:
                continue

            review_stats = paper.get("review_stats", {}) or {}
            avg_score = float(review_stats.get("avg_score", 0.5))
            review_count = int(review_stats.get("review_count", 0))
            highest = float(review_stats.get("highest_score", avg_score))
            lowest = float(review_stats.get("lowest_score", avg_score))

            score10 = 1 + 9 * avg_score
            dispersion10 = 9 * (highest - lowest)
            weight = math.log(1 + review_count) / (1 + max(dispersion10, 0.0))

            summary = {
                "paper_id": paper_id,
                "title": paper.get("title", ""),
                "pattern_id": pattern_id,
                "score10": score10,
                "review_count": review_count,
                "dispersion10": dispersion10,
                "weight": weight,
            }

            self.paper_id_to_summary[paper_id] = summary
            self.pattern_to_papers.setdefault(pattern_id, []).append(summary)

        # keep deterministic order
        for pattern_id, plist in self.pattern_to_papers.items():
            plist.sort(key=lambda x: (x["score10"], x["paper_id"]))

        self.global_scores_sorted = sorted(
            [p["score10"] for p in self.paper_id_to_summary.values() if "score10" in p]
        )

    def get_pattern_papers(self, pattern_id: str) -> List[Dict]:
        return list(self.pattern_to_papers.get(pattern_id, []))

    @staticmethod
    def _quantile(sorted_values: List[float], q: float) -> Optional[float]:
        if not sorted_values:
            return None
        n = len(sorted_values)
        if n == 1:
            return float(sorted_values[0])
        idx = int(round(q * (n - 1)))
        idx = max(0, min(n - 1, idx))
        return float(sorted_values[idx])

    def get_pattern_score10_values(self, pattern_id: str) -> List[float]:
        papers = self.get_pattern_papers(pattern_id)
        if not papers:
            return []
        return [p["score10"] for p in papers]

    def get_pattern_quantiles(self, pattern_id: str, quantiles: Optional[List[float]] = None) -> Dict:
        quantiles = quantiles or [0.5, 0.75]
        values = sorted(self.get_pattern_score10_values(pattern_id))
        data = {"n": len(values)}
        for q in quantiles:
            key = f"q{int(q * 100)}"
            data[key] = self._quantile(values, q)
        return data

    def get_global_quantiles(self, quantiles: Optional[List[float]] = None) -> Dict:
        quantiles = quantiles or [0.5, 0.75]
        values = self.global_scores_sorted or []
        data = {"n": len(values)}
        for q in quantiles:
            key = f"q{int(q * 100)}"
            data[key] = self._quantile(values, q)
        return data

    def _select_by_quantiles(self, papers: List[Dict], quantiles: Iterable[float]) -> List[Dict]:
        if not papers:
            return []
        n = len(papers)
        anchors = []
        for q in quantiles:
            if n == 1:
                idx = 0
            else:
                idx = int(round(q * (n - 1)))
            idx = max(0, min(n - 1, idx))
            anchors.append(papers[idx])
        return anchors

    def get_quantile_anchors(self, pattern_id: str, quantiles: Optional[List[float]] = None) -> List[Dict]:
        quantiles = quantiles or [0.1, 0.25, 0.5, 0.75, 0.9]
        papers = self.get_pattern_papers(pattern_id)
        if len(papers) <= len(quantiles):
            return papers
        return self._select_by_quantiles(papers, quantiles)

    def add_exemplar_anchors(self, anchors: List[Dict], pattern_info: Optional[Dict], max_exemplars: int = 2) -> List[Dict]:
        pattern_info = pattern_info or {}
        exemplar_ids = pattern_info.get("exemplar_paper_ids", []) or []
        if not exemplar_ids:
            return anchors

        anchor_ids = {a["paper_id"] for a in anchors}
        candidates = []
        for pid in exemplar_ids:
            summary = self.paper_id_to_summary.get(pid)
            if summary and summary["paper_id"] not in anchor_ids:
                candidates.append(summary)

        # choose most reliable exemplars
        candidates.sort(key=lambda x: (-x["weight"], -x["review_count"], x["paper_id"]))
        selected = candidates[:max_exemplars]
        return anchors + selected

    def _dedupe(self, papers: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for p in papers:
            pid = p["paper_id"]
            if pid in seen:
                continue
            seen.add(pid)
            unique.append(p)
        return unique

    def select_initial_anchors(self, pattern_id: str, pattern_info: Optional[Dict], max_initial: int = 7,
                               quantiles: Optional[List[float]] = None, max_exemplars: int = 2) -> List[Dict]:
        anchors = self.get_quantile_anchors(pattern_id, quantiles=quantiles)
        anchors = self._dedupe(anchors)
        anchors = self.add_exemplar_anchors(anchors, pattern_info, max_exemplars=max_exemplars)
        anchors = self._dedupe(anchors)
        # trim deterministically by weight then score proximity to median
        if len(anchors) > max_initial:
            anchors.sort(key=lambda x: (-x["weight"], x["score10"], x["paper_id"]))
            anchors = anchors[:max_initial]
        return anchors

    def select_adaptive_anchors(self, pattern_id: str, selected_ids: List[str], S_hint: float,
                                offsets: Optional[List[float]] = None, max_total: int = 9) -> List[Dict]:
        offsets = offsets or [-0.5, 0.5, -0.25, 0.25]
        papers = self.get_pattern_papers(pattern_id)
        if not papers:
            return []
        selected = set(selected_ids)
        supplements = []
        for off in offsets:
            target = S_hint + off
            best = None
            best_dist = None
            for p in papers:
                if p["paper_id"] in selected:
                    continue
                dist = abs(p["score10"] - target)
                if best is None or dist < best_dist or (dist == best_dist and p["weight"] > best["weight"]):
                    best = p
                    best_dist = dist
            if best:
                selected.add(best["paper_id"])
                supplements.append(best)
            if len(selected) >= max_total:
                break
        return supplements
