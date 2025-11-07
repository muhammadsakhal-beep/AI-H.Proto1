# brain.py
"""
DroneBrain module

Kelas:
- DroneBrain: otak drone yang memutuskan kapan peringatan, kapan menyerang (pursuit),
  mengunci target, membroadcast lokasi target, dan melepas lock.
Aturan utama:
- Jika target berbahaya (threat > threshold) DAN target **masuk ke dalam protected_zone** -> drone boleh menyerang (pursue).
- Jika target berbahaya tapi BELUM masuk protected_zone -> drone hanya memberi PERINGATAN (broadcast), tidak mengejar.
- shared_targets menyimpan status awareness (pos, locked_by, warning_only flag).
"""

import time
import math
from typing import Dict, Tuple

class DroneBrain:
    def __init__(self, drone_id: str, shared_targets: Dict, scan_cells: int = 5, threshold: float = 0.66):
        """
        drone_id: identifier drone (mis. "D0")
        shared_targets: shared registry (dict) bersama antar drone
        scan_cells: radius scan dalam satuan cell grid
        threshold: nilai ambang threat
        """
        self.id = drone_id
        self.shared_targets = shared_targets
        self.scan_cells = scan_cells
        self.threshold = threshold
        self.target_id = None  # id person yang sedang di-lock untuk pursuit

    def in_scan_range(self, drone_cell: Tuple[int,int], person_cell: Tuple[int,int]) -> bool:
        dx = abs(drone_cell[0] - person_cell[0])
        dy = abs(drone_cell[1] - person_cell[1])
        return dx <= self.scan_cells and dy <= self.scan_cells

    def decide(self, drone_cell: Tuple[int,int], persons: list, protected_zone: Tuple[int,int,int,int]):
        """
        Scan persons and decide:
        - If a person has threat > threshold AND is inside protected_zone -> try lock + pursue.
        - Else if threat > threshold but outside protected_zone AND within scan range -> issue warning (broadcast) only.
        - If locked target is no longer valid, release it.
        Returns action string for logging.
        """
        # Release target if invalid
        if self.target_id:
            # check if still exists & still in shared_targets and locked by me
            rec = self.shared_targets.get(self.target_id)
            if rec is None or rec.get("locked_by") != self.id:
                self.target_id = None

        # scan nearby persons
        best_candidate = None  # (person, score)
        for p in persons:
            if p.caught:
                continue
            if p.threat <= 0:
                continue
            if not self.in_scan_range(drone_cell, (p.cell_x, p.cell_y)):
                continue

            inside_protected = self._in_zone((p.cell_x, p.cell_y), protected_zone)
            if inside_protected and p.threat > self.threshold:
                # immediate high-priority pursuit candidate
                score = (p.threat, -self._manhattan(drone_cell, (p.cell_x, p.cell_y)))
                if (best_candidate is None) or (score > best_candidate[1]):
                    best_candidate = (p, score, "PURSUE")
            elif p.threat > self.threshold:
                # warning candidate (lower priority)
                score = (p.threat * 0.8, -self._manhattan(drone_cell, (p.cell_x, p.cell_y)))
                if (best_candidate is None) or (score > best_candidate[1]):
                    best_candidate = (p, score, "WARN")

        if best_candidate:
            person, _score, mode = best_candidate
            pid = person.id
            if mode == "PURSUE":
                # try to lock for pursuit
                rec = self.shared_targets.get(pid)
                if rec is None or rec.get("locked_by") is None:
                    # lock for pursuit
                    self.shared_targets[pid] = {
                        "pos": (person.cell_x, person.cell_y),
                        "locked_by": self.id,
                        "by": [self.id],
                        "ts": time.time(),
                        "warning_only": False
                    }
                    self.target_id = pid
                    return f"LOCK+PURSUE {pid}"
                else:
                    # someone else locked it; just broadcast location
                    self.shared_targets[pid]["pos"] = (person.cell_x, person.cell_y)
                    self.shared_targets[pid].setdefault("by", []).append(self.id)
                    self.shared_targets[pid]["ts"] = time.time()
                    return f"ALREADY_LOCKED {pid} by {rec.get('locked_by')}"
            else:
                # WARN: do not lock; broadcast as warning_only
                rec = self.shared_targets.get(pid)
                if rec is None:
                    self.shared_targets[pid] = {
                        "pos": (person.cell_x, person.cell_y),
                        "locked_by": None,
                        "by": [self.id],
                        "ts": time.time(),
                        "warning_only": True
                    }
                else:
                    # update
                    rec["pos"] = (person.cell_x, person.cell_y)
                    rec.setdefault("by", []).append(self.id)
                    rec["ts"] = time.time()
                    rec["warning_only"] = True
                return f"WARN {pid}"
        else:
            return "NO_ACTION"

    def release_lock(self, pid: str):
        """Release lock if this drone holds it."""
        rec = self.shared_targets.get(pid)
        if rec and rec.get("locked_by") == self.id:
            rec["locked_by"] = None
            rec["ts"] = time.time()
            rec.setdefault("by", []).append(self.id)
        if self.target_id == pid:
            self.target_id = None

    def capture_occurred(self, pid: str):
        """Called when target is captured — remove from shared targets."""
        if pid in self.shared_targets:
            del self.shared_targets[pid]
        if self.target_id == pid:
            self.target_id = None

    @staticmethod
    def _in_zone(cell: Tuple[int,int], zone: Tuple[int,int,int,int]) -> bool:
        # zone = (x1,y1,x2,y2) inclusive cell coords
        x1,y1,x2,y2 = zone
        return x1 <= cell[0] <= x2 and y1 <= cell[1] <= y2

    @staticmethod
    def _manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
        return abs(a[0]-b[0]) + abs(a[1]-b[1])
