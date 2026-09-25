"""Public non-poll data some reports use (World Bank indicators and similar).

Snapshots whose licence allows redistribution are committed in
reports/external/. Others (for example sources licensed for non-commercial
use only) are not redistributed here: reports/external/fetch_external.py
downloads them into reports/external/downloaded/, which git ignores.
Without them, the findings that need them are reported as EXTERNAL_ONLY
and every other finding still runs. reports/external/README.md lists each
source, its licence and whether it is committed.
"""

from .data import REPO_ROOT

EXTERNAL_DIR = REPO_ROOT / "reports" / "external"


class ExternalDataRequired(RuntimeError):
    """A finding needs non-poll data that is not in the repository."""


def external_path(name):
    """Path to an external data file, committed or downloaded."""
    for folder in (EXTERNAL_DIR, EXTERNAL_DIR / "downloaded"):
        if (folder / name).exists():
            return folder / name
    raise ExternalDataRequired(
        f"needs {name}, which is not redistributed here; "
        "run python reports/external/fetch_external.py to download it"
    )
