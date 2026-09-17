import time
import threading
from typing import Optional, Dict, Any

LOCK_TIMEOUT_SECONDS = 180  # 3-minute fail-safe auto-release

class ExtractionStateManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.is_busy: bool = False
        self.filename: Optional[str] = None
        self.started_at: Optional[float] = None
        self.last_completed_recipe: Optional[Dict[str, Any]] = None
        self.last_completed_at: Optional[float] = None

    def acquire(self, filename: str) -> bool:
        with self._lock:
            now = time.time()
            if self.is_busy and self.started_at and (now - self.started_at) > LOCK_TIMEOUT_SECONDS:
                # Auto-release stale lock
                self.is_busy = False

            if self.is_busy:
                return False

            self.is_busy = True
            self.filename = filename
            self.started_at = now
            return True

    def release(self, recipe_data: Optional[Dict[str, Any]] = None):
        with self._lock:
            self.is_busy = False
            self.filename = None
            self.started_at = None
            if recipe_data:
                self.last_completed_recipe = recipe_data
                self.last_completed_at = time.time()

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            if self.is_busy and self.started_at and (now - self.started_at) > LOCK_TIMEOUT_SECONDS:
                self.is_busy = False
                self.filename = None
                self.started_at = None

            return {
                "is_busy": self.is_busy,
                "filename": self.filename,
                "started_at": self.started_at,
                "last_completed_recipe": self.last_completed_recipe,
                "last_completed_at": self.last_completed_at,
            }

extraction_state = ExtractionStateManager()
