from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Waveform:
    times: list[float]
    values: list[float]


def require_pyvisa():
    try:
        import pyvisa  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "pyvisa is not installed. Install TekVISA or NI-VISA first, then run:\n"
            "  C:\\Users\\chris\\anaconda3\\python.exe -m pip install pyvisa\n"
        ) from exc
    return pyvisa


def list_resources() -> None:
    pyvisa = require_pyvisa()
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    if not resources:
        print("No VISA instruments found.")
        print("Check USB Device/LAN cable, VISA driver, and oscilloscope remote settings.")
        return
    print("Found VISA resources:")
    for resource in resources:
        print(f"  {resource}")


def open_scope(resource: str):
    pyvisa = require_pyvisa()
    rm = pyvisa.ResourceManager()
    scope = rm.open_resource(resource)
    scope.timeout = 10000
    scope.write_termination = "\n"
    scope.read_termination = "\n"
    print(scope.query("*IDN?").strip())
    return scope


def read_waveform(scope, channel: int, points: int) -> Waveform:
    scope.write(f"DATA:SOURCE CH{channel}")
    scope.write("DATA:START 1")
    scope.write(f"DATA:STOP {points}")
    scope.write("DATA:WIDTH 1")
    scope.write("DATA:ENC RIBINARY")

    ymult = float(scope.query("WFMPRE:YMULT?"))
    yzero = float(scope.query("WFMPRE:YZERO?"))
    yoff = float(scope.query("WFMPRE:YOFF?"))
    xincr = float(scope.query("WFMPRE:XINCR?"))
    xzero = float(scope.query("WFMPRE:XZERO?"))

    raw = scope.query_binary_values("CURVE?", datatype="b", container=list)
    values = [(sample - yoff) * ymult + yzero for sample in raw]
    times = [xzero + index * xincr for index in range(len(values))]
    return Waveform(times=times, values=values)


def save_csv(path: Path, transmission: Waveform, error: Waveform) -> None:
    n = min(len(transmission.times), len(transmission.values), len(error.values))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "transmission", "error"])
        for i in range(n):
            writer.writerow([transmission.times[i], transmission.values[i], error.values[i]])
    print(f"Saved {n} samples to {path}")


def capture_once(resource: str, output: Path, points: int, ch_transmission: int, ch_error: int) -> None:
    scope = open_scope(resource)
    scope.write("ACQUIRE:STATE STOP")
    transmission = read_waveform(scope, ch_transmission, points)
    error = read_waveform(scope, ch_error, points)
    save_csv(output, transmission, error)
    scope.write("ACQUIRE:STATE RUN")


def capture_loop(
    resource: str,
    output_dir: Path,
    points: int,
    interval_s: float,
    ch_transmission: int,
    ch_error: int,
) -> None:
    scope = open_scope(resource)
    output_dir.mkdir(parents=True, exist_ok=True)
    index = 0
    print("Press Ctrl+C to stop.")
    while True:
        started = time.time()
        scope.write("ACQUIRE:STATE STOP")
        transmission = read_waveform(scope, ch_transmission, points)
        error = read_waveform(scope, ch_error, points)
        scope.write("ACQUIRE:STATE RUN")
        stamp = time.strftime("%Y%m%d_%H%M%S")
        save_csv(output_dir / f"scope_frame_{stamp}_{index:04d}.csv", transmission, error)
        index += 1
        elapsed = time.time() - started
        time.sleep(max(0.0, interval_s - elapsed))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture CH1/CH2 waveforms from a Tektronix MDO/MSO oscilloscope.")
    parser.add_argument("--list", action="store_true", help="List VISA resources and exit.")
    parser.add_argument("--resource", help="VISA resource, for example TCPIP0::192.168.1.50::INSTR.")
    parser.add_argument("--once", action="store_true", help="Capture one frame to CSV.")
    parser.add_argument("--loop", action="store_true", help="Capture frames repeatedly.")
    parser.add_argument("--output", default="scope_captures/latest_scope_frame.csv", help="Output CSV for --once.")
    parser.add_argument("--output-dir", default="scope_captures", help="Output folder for --loop.")
    parser.add_argument("--points", type=int, default=10000, help="Waveform points per channel.")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between loop captures.")
    parser.add_argument("--transmission-channel", type=int, default=1, choices=[1, 2, 3, 4])
    parser.add_argument("--error-channel", type=int, default=2, choices=[1, 2, 3, 4])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        list_resources()
        return 0
    if not args.resource:
        raise SystemExit("Use --resource or run --list first.")
    if args.once:
        capture_once(
            args.resource,
            Path(args.output),
            args.points,
            args.transmission_channel,
            args.error_channel,
        )
        return 0
    if args.loop:
        capture_loop(
            args.resource,
            Path(args.output_dir),
            args.points,
            args.interval,
            args.transmission_channel,
            args.error_channel,
        )
        return 0
    raise SystemExit("Choose --list, --once, or --loop.")


if __name__ == "__main__":
    raise SystemExit(main())
