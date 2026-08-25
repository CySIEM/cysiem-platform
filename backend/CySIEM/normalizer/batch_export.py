"""
Layer 2 -- Rolling Batch JSON Export.

Independent, toggleable side-channel that buffers normalized CanonicalEvents
in memory and periodically flushes them to a local .json file, in addition
to (never instead of) the real-time Kafka/OpenSearch writes the normalizer
already does. This is purely an export/archive convenience - disabling it
has zero effect on ingestion, detection, or any other layer, by design.

WINDOW BEHAVIOR: rolling from process start, not clock-aligned. The first
window begins the instant BatchExporter is constructed; every
window_seconds after that opens a new window. A normalizer restart starts
a fresh window from wherever the clock happens to be at that moment - it
does NOT try to resume or align to the window the previous process instance
was in.

RESTART BEHAVIOR: whatever was buffered in the in-progress window at the
moment of a clean shutdown is FLUSHED to disk as a partial file (may cover
less than window_seconds of real time) via close(), called from
NormalizerService.run()'s shutdown path. On an unclean process kill (SIGKILL,
crash) with no chance to run close(), the in-memory buffer for that window
is lost - already-flushed prior windows are entirely unaffected, and the
next process start simply begins a new window from scratch. This matches
"keep existing logs, start a new file on restart" - no attempt is made to
append to or resume a prior window's file.

FILE NAMING: {output_dir}/{tenant_id}/{DD-MM-YYYY_HH-MM}.json, 24-hour time,
one subfolder per tenant so multi-tenant deployments never collide on
filenames. Directory is created if it doesn't exist.

FAILURE MODE: any exception while buffering or writing (disk full,
permission denied, path missing) is caught, logged, and never propagated -
this module can never be the reason the main ingestion pipeline stops
working. See config.py's batch_export_enabled for the on/off switch.
"""
from __future__ import annotations
import json
import logging
import os
import threading
import time
from datetime import datetime
from CySIEM.schemas.canonical import CanonicalEvent

logger = logging.getLogger("kksiem.normalizer.batch_export")


class BatchExporter:
    def __init__(self, output_dir: str, tenant_id: str, window_seconds: int = 1800):
        self.output_dir = output_dir
        self.tenant_id = tenant_id
        self.window_seconds = window_seconds

        self._lock = threading.Lock()
        self._buffer: list[dict] = []
        self._window_start: datetime | None = None
        self._window_start_monotonic: float = 0.0

        self._start_new_window()

    def _tenant_dir(self) -> str:
        return os.path.join(self.output_dir, self.tenant_id)

    def _window_filename(self, window_start: datetime) -> str:
        # 24-hour time, DD-MM-YYYY_HH-MM, e.g. 08-08-2026_14-30.json
        return window_start.strftime("%d-%m-%Y_%H-%M") + ".json"

    def _start_new_window(self):
        self._buffer = []
        self._window_start = datetime.now()
        self._window_start_monotonic = time.monotonic()

    def _write_window_file(self, window_start: datetime, events: list[dict]):
        if not events:
            return
        try:
            tenant_dir = self._tenant_dir()
            os.makedirs(tenant_dir, exist_ok=True)
            base_name = self._window_filename(window_start)
            path = os.path.join(tenant_dir, base_name)
            # Filename granularity is minutes; if a file for this exact
            # minute already exists (e.g. the normalizer crash-looped and
            # restarted twice within the same minute, or window_seconds is
            # configured very short), never silently overwrite prior
            # events - append a numeric suffix instead so each window's
            # data is preserved.
            if os.path.exists(path):
                stem, ext = os.path.splitext(base_name)
                n = 2
                while os.path.exists(os.path.join(tenant_dir, f"{stem}_{n}{ext}")):
                    n += 1
                path = os.path.join(tenant_dir, f"{stem}_{n}{ext}")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2, default=str)
            logger.info(f"Batch export wrote {len(events)} events to {path}")
        except Exception as e:
            # Never let a disk/permission problem here affect the caller -
            # this module is export-only, always fail soft.
            logger.error(f"Batch export failed to write window file (non-fatal): {e}")

    def add(self, event: CanonicalEvent):
        """Buffer one normalized event. Call on every clean event the
        normalizer produces - rolls the window over automatically once
        window_seconds has elapsed since this exporter's construction (or
        the last rollover)."""
        try:
            with self._lock:
                elapsed = time.monotonic() - self._window_start_monotonic
                if elapsed >= self.window_seconds:
                    self._flush_locked()
                    self._start_new_window()
                self._buffer.append(event.to_opensearch_doc())
        except Exception as e:
            logger.error(f"Batch export failed to buffer event (non-fatal): {e}")

    def _flush_locked(self):
        """Caller must hold self._lock."""
        if self._buffer:
            self._write_window_file(self._window_start, self._buffer)

    def close(self):
        """Flush whatever is currently buffered, as a partial window file.
        Call this once, from the normalizer's shutdown path, so a clean
        restart never silently drops up to window_seconds of already-
        normalized events."""
        try:
            with self._lock:
                self._flush_locked()
                self._buffer = []
        except Exception as e:
            logger.error(f"Batch export failed to flush on close (non-fatal): {e}")
