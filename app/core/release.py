import os
import socket
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PYPROJECT = _PROJECT_ROOT / "pyproject.toml"
_BUILT_AT = _PROJECT_ROOT / "BUILT_AT"


@cache
def project_version() -> str:
    with _PYPROJECT.open("rb") as file:
        return str(tomllib.load(file)["project"]["version"])


def built_at() -> str:
    if _BUILT_AT.is_file():
        return _BUILT_AT.read_text().strip()
    return "unknown"


@dataclass(frozen=True)
class ReleaseInfo:
    app: str
    version: str
    git_sha: str
    built_at: str
    color: str
    hostname: str
    started_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_release(*, app_name: str, color: str) -> ReleaseInfo:
    return ReleaseInfo(
        app=app_name,
        version=project_version(),
        git_sha=os.environ.get("GIT_SHA", "unknown"),
        built_at=built_at(),
        color=color,
        hostname=socket.gethostname(),
        started_at=datetime.now(tz=UTC).isoformat(timespec="seconds"),
    )
