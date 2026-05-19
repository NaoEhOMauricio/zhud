"""
File watcher: monitors PokerStars HandHistory folder for new/modified .txt files.
Uses watchdog for real-time events + a periodic scanner thread every 30s as fallback
(watchdog on Windows sometimes misses on_created events for new tournament files).
"""
import os
import time
import asyncio
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from parser import HandParser
from stats import process_hand

_loop: asyncio.AbstractEventLoop = None


def _fix_path(raw: str) -> str:
    """Strip trailing/leading whitespace from every path component."""
    p = Path(raw.strip())
    fixed_parts = [part.strip() for part in p.parts]
    return str(Path(*fixed_parts)) if fixed_parts else raw.strip()


class _HandHistoryHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue):
        self._queue   = queue
        self._parser  = HandParser()
        self._positions: dict = {}   # filepath -> byte offset
        self._lock    = threading.Lock()

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".txt"):
            self._process(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".txt"):
            self._process(event.src_path)

    def _process(self, raw_path: str):
        filepath = _fix_path(raw_path)
        try:
            if not os.path.isfile(filepath):
                return

            with self._lock:
                offset = self._positions.get(filepath, 0)

            hands, new_offset = self._parser.parse_file_from(filepath, offset)

            with self._lock:
                # Only advance position if file grew
                if new_offset > self._positions.get(filepath, 0):
                    self._positions[filepath] = new_offset

            for hand in hands:
                updates = process_hand(hand)
                if updates and _loop:
                    _loop.call_soon_threadsafe(
                        self._queue.put_nowait,
                        {
                            "type":       "hand",
                            "updates":    updates,
                            "hand_id":    hand.hand_id,
                            "table_name": hand.table_name,
                            "game_type":  hand.game_type,
                            "hand_time":  hand.hand_time,
                            "players":    [info["name"] for info in hand.players.values()],
                        },
                    )
        except Exception as exc:
            print(f"[watcher] Error processing {filepath}: {exc}")

    def scan_directory(self, hh_path: str):
        """Scan all .txt files in directory (used for startup + periodic fallback)."""
        for root, _dirs, files in os.walk(hh_path):
            for fname in sorted(files):
                if fname.lower().endswith(".txt"):
                    self._process(os.path.join(root, fname))


class _PeriodicScanner(threading.Thread):
    """
    Runs every INTERVAL seconds and rescans the HH directory.
    Catches any files that watchdog's on_created/on_modified missed.
    """
    INTERVAL = 15   # seconds between scans

    def __init__(self, handler: _HandHistoryHandler, hh_path: str):
        super().__init__(daemon=True, name="zhud-periodic-scanner")
        self._handler  = handler
        self._hh_path  = hh_path

    def run(self):
        while True:
            time.sleep(self.INTERVAL)
            try:
                self._handler.scan_directory(self._hh_path)
            except Exception as exc:
                print(f"[scanner] Error: {exc}")


def start_watching(hh_path: str, queue: asyncio.Queue) -> Observer:
    global _loop
    _loop = asyncio.get_event_loop()

    hh_path = _fix_path(hh_path)

    if not os.path.exists(hh_path):
        print(f"[watcher] WARNING: path not found: {hh_path}")
        os.makedirs(hh_path, exist_ok=True)

    handler = _HandHistoryHandler(queue)

    # ── Startup scan ──────────────────────────────────────────────────────────
    print(f"[watcher] Scanning existing files in: {hh_path}")
    handler.scan_directory(hh_path)
    print(f"[watcher] Startup scan complete")

    # ── Watchdog real-time observer ───────────────────────────────────────────
    observer = Observer()
    observer.schedule(handler, hh_path, recursive=True)
    observer.start()
    print(f"[watcher] Watching: {hh_path}")

    # ── Periodic fallback scanner (every 15s) ─────────────────────────────────
    scanner = _PeriodicScanner(handler, hh_path)
    scanner.start()
    print(f"[watcher] Periodic scanner started (every {_PeriodicScanner.INTERVAL}s)")

    return observer
