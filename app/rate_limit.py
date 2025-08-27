import time
from typing import Dict, Tuple


class SessionCounter:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._store: Dict[str, Tuple[int, float]] = {}

    def _purge_if_expired(self, session_id: str) -> None:
        if session_id in self._store:
            count, ts = self._store[session_id]
            if time.time() - ts > self._ttl:
                del self._store[session_id]

    def increment_and_get(self, session_id: str) -> int:
        self._purge_if_expired(session_id)
        if session_id not in self._store:
            self._store[session_id] = (1, time.time())
        else:
            count, ts = self._store[session_id]
            self._store[session_id] = (count + 1, ts)
        return self._store[session_id][0]

    def get(self, session_id: str) -> int:
        self._purge_if_expired(session_id)
        return self._store.get(session_id, (0, 0.0))[0]


