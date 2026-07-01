from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
ROOT = APP_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from real_device_autolock.tektronix_scope_capture import capture_once, query_idn  # noqa: E402
from one_click_lock_app.models import SignalFrame  # noqa: E402


class ScopeService:
    def __init__(self, capture_dir: Path | None = None) -> None:
        self.capture_dir = capture_dir or (APP_DIR / "captures")
        self.resource: str | None = None
        self.idn: str | None = None

    def resource_from_lan(self, host: str, port: int = 4000) -> str:
        return f"SOCKET::{host.strip()}::{port}"

    def test_connection(self, resource: str) -> str:
        idn = query_idn(resource, timeout_ms=3500)
        if not idn:
            raise RuntimeError("No *IDN? response from oscilloscope.")
        self.resource = resource
        self.idn = idn
        return idn

    def capture_frame(
        self,
        resource: str,
        transmission_channel: int = 1,
        error_channel: int = 2,
        points: int | None = None,
    ) -> SignalFrame:
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = self.capture_dir / f"scope_frame_{stamp}.csv"
        capture_once(
            resource,
            csv_path,
            points,
            transmission_channel,
            error_channel,
            freeze_acquisition=False,
        )
        latest = self.capture_dir / "latest_scope_frame.csv"
        latest.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
        return load_signal_frame(csv_path)


def load_signal_frame(path: Path) -> SignalFrame:
    time_s: list[float] = []
    transmission_v: list[float] = []
    error_v: list[float] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_s.append(float(row["time"]))
            transmission_v.append(float(row["transmission"]))
            error_v.append(float(row["error"]))
    if not time_s:
        raise RuntimeError(f"CSV is empty: {path}")
    t0 = time_s[0]
    return SignalFrame(
        time_s=[t - t0 for t in time_s],
        transmission_v=transmission_v,
        error_v=error_v,
        csv_path=path,
    )
