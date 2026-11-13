"""Reproducible, offline property profiles; no database or timing dependency."""

import os

from hypothesis import settings

settings.register_profile(
    "offline_ci", max_examples=100, derandomize=True, database=None, deadline=None, print_blob=True
)
settings.register_profile(
    "offline_dev", max_examples=30, derandomize=True, database=None, deadline=None, print_blob=True
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "offline_ci"))
