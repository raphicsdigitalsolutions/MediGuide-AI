"""Switchable LangChain model caches required by the assignment."""

from pathlib import Path
from contextlib import contextmanager
from threading import RLock
from typing import Any

from langchain_community.cache import SQLiteCache
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache


_active_mode: str | None = None
_active_cache: Any | None = None
_cache_lock = RLock()


def configure_llm_cache(mode: str, sqlite_path: Path) -> str:
    """Set LangChain's process-wide cache to Off, In-memory, or SQLite."""
    global _active_mode, _active_cache

    with _cache_lock:
        if mode not in {"Off", "In-memory", "SQLite"}:
            raise ValueError(f"Unsupported cache mode: {mode}")

        if mode == _active_mode:
            return mode

        if mode == "Off":
            set_llm_cache(None)
            _active_cache = None
            _active_mode = mode
            return mode

        if mode == "In-memory":
            cache = InMemoryCache()
        else:
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            cache = SQLiteCache(database_path=str(sqlite_path))

        set_llm_cache(cache)
        _active_cache = cache
        _active_mode = mode
        return mode


@contextmanager
def llm_cache_context(mode: str, sqlite_path: Path):
    """Hold the process-wide LangChain cache steady for one model request."""
    with _cache_lock:
        configure_llm_cache(mode, sqlite_path)
        yield


def clear_active_cache() -> bool:
    """Clear the currently selected LangChain cache, if there is one."""
    with _cache_lock:
        if _active_cache is None:
            return False
        _active_cache.clear()
        return True

