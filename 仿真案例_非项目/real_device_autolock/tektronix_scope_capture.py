from __future__ import annotations

import argparse
import csv
import ipaddress
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Waveform:
    times: list[float]
    values: list[float]


class RawSocketScope:
    def __init__(self, host: str, port: int = 4000, timeout_s: float = 5.0) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout_s)
        self.sock.settimeout(timeout_s)

    def write(self, command: str) -> None:
        self.sock.sendall((command.rstrip() + "\n").encode("ascii"))

    def query(self, command: str) -> str:
        self.write(command)
        chunks: list[bytes] = []
        while True:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
        return b"".join(chunks).decode("ascii", errors="replace").strip()

    def query_binary_values(self, command: str, datatype: str = "b", container=list):
        self.write(command)
        first = self._recv_exact(1)
        if first != b"#":
            rest = first + self.sock.recv(4096)
            raise RuntimeError(f"Expected SCPI binary block, got: {rest[:80]!r}")
        digits = int(self._recv_exact(1).decode("ascii"))
        size = int(self._recv_exact(digits).decode("ascii"))
        payload = self._recv_exact(size)
        previous_timeout = self.sock.gettimeout()
        try:
            self.sock.settimeout(0.05)
            self.sock.recv(1)
        except socket.timeout:
            pass
        finally:
            self.sock.settimeout(previous_timeout)
        if datatype != "b":
            raise NotImplementedError("Raw socket fallback currently supports signed byte waveforms only.")
        values = [(byte - 256 if byte > 127 else byte) for byte in payload]
        return container(values)

    def _recv_exact(self, size: int) -> bytes:
        data = bytearray()
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise RuntimeError("Socket closed while reading oscilloscope data.")
            data.extend(chunk)
        return bytes(data)

    def close(self) -> None:
        self.sock.close()


def require_pyvisa():
    try:
        import pyvisa  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "pyvisa is not installed.\n\n"
            "Install a VISA driver first, preferably TekVISA/OpenChoice or NI-VISA.\n"
            "Then run:\n"
            "  C:\\Users\\chris\\anaconda3\\python.exe -m pip install pyvisa\n"
        ) from exc
    return pyvisa


def raw_socket_idn(host: str, port: int = 4000, timeout_s: float = 0.7) -> str | None:
    try:
        scope = RawSocketScope(host, port, timeout_s)
        idn = scope.query("*IDN?")
        scope.close()
        return idn
    except Exception:
        return None


def query_idn(resource: str, timeout_ms: int = 1200) -> str | None:
    if resource.startswith("SOCKET::"):
        parts = resource.split("::")
        return raw_socket_idn(parts[1], int(parts[2]), timeout_ms / 1000.0)
    pyvisa = require_pyvisa()
    rm = pyvisa.ResourceManager()
    try:
        inst = rm.open_resource(resource)
        inst.timeout = timeout_ms
        inst.write_termination = "\n"
        inst.read_termination = "\n"
        idn = inst.query("*IDN?").strip()
        inst.close()
        return idn
    except Exception:
        return None


def local_ipv4_networks() -> list[ipaddress.IPv4Network]:
    networks: list[ipaddress.IPv4Network] = []
    for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_STREAM):
        ip = ipaddress.IPv4Address(info[4][0])
        if ip.is_loopback or ip.is_link_local:
            continue
        network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
        if network not in networks:
            networks.append(network)
    return networks


def is_tektronix_scope(idn: str) -> bool:
    text = idn.upper()
    return "TEKTRONIX" in text and ("MDO" in text or "MSO" in text or "DPO" in text)


def discover_scope(scan_lan: bool = True) -> str:
    if not scan_lan:
        raise SystemExit("No Tektronix MDO/MSO oscilloscope found in VISA resources.")

    print("Searching Tektronix oscilloscope by raw LAN socket on port 4000...")
    networks = local_ipv4_networks()
    if not networks:
        print("No local IPv4 network found for LAN scan.")
    for network in networks:
        print(f"  Scanning {network} ...")
        hosts = [str(ip) for ip in network.hosts()]
        with ThreadPoolExecutor(max_workers=64) as executor:
            futures = {executor.submit(raw_socket_idn, host, 4000, 0.45): host for host in hosts}
            for future in as_completed(futures):
                host = futures[future]
                idn = future.result()
                if idn and is_tektronix_scope(idn):
                    resource = f"SOCKET::{host}::4000"
                    print(f"Selected oscilloscope: {resource} -> {idn}")
                    return resource

    raise SystemExit(
        "No Tektronix oscilloscope found automatically.\n\n"
        "Check these items:\n"
        "  1. MDO3024 LAN cable is connected.\n"
        "  2. The oscilloscope has an IP address.\n"
        "  3. Windows firewall is not blocking Python.\n"
        "  4. If auto-discovery fails, run with --resource SOCKET::<scope-ip>::4000 manually."
    )


def list_resources() -> None:
    print("Local IPv4 networks for auto LAN scan:")
    for network in local_ipv4_networks():
        print(f"  {network}")
    print("Run without --list to auto-scan these networks for Tektronix port 4000.")


def open_scope(resource: str):
    if resource.startswith("SOCKET::"):
        parts = resource.split("::")
        scope = RawSocketScope(parts[1], int(parts[2]), timeout_s=60.0)
        print(scope.query("*IDN?"))
        return scope
    pyvisa = require_pyvisa()
    rm = pyvisa.ResourceManager()
    scope = rm.open_resource(resource)
    scope.timeout = 10000
    scope.write_termination = "\n"
    scope.read_termination = "\n"
    print(scope.query("*IDN?").strip())
    return scope


def query_int(scope, commands: list[str]) -> int | None:
    for command in commands:
        try:
            value = scope.query(command).strip()
            if value:
                return int(float(value))
        except Exception:
            continue
    return None


def scope_record_length(scope) -> int:
    record_length = query_int(
        scope,
        [
            "HORizontal:MODE:RECOrdlength?",
            "HORizontal:RECOrdlength?",
            "WFMPRE:NR_PT?",
        ],
    )
    if record_length is None or record_length <= 0:
        raise RuntimeError("Could not read oscilloscope record length for full-screen capture.")
    return record_length


def read_waveform(scope, channel: int, points: int | None) -> Waveform:
    scope.write(f"DATA:SOURCE CH{channel}")
    scope.write("DATA:START 1")
    stop_point = points if points and points > 0 else scope_record_length(scope)
    scope.write(f"DATA:STOP {stop_point}")
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


def capture_once(
    resource: str,
    output: Path,
    points: int | None,
    ch_transmission: int,
    ch_error: int,
    freeze_acquisition: bool = False,
) -> None:
    scope = open_scope(resource)
    try:
        if freeze_acquisition:
            scope.write("ACQUIRE:STATE STOP")
        transmission = read_waveform(scope, ch_transmission, points)
        error = read_waveform(scope, ch_error, points)
        save_csv(output, transmission, error)
    finally:
        if freeze_acquisition:
            try:
                scope.write("ACQUIRE:STATE RUN")
            except Exception:
                pass
        scope.close()


def capture_loop(
    resource: str,
    output_dir: Path,
    points: int | None,
    interval_s: float,
    ch_transmission: int,
    ch_error: int,
) -> None:
    scope = open_scope(resource)
    output_dir.mkdir(parents=True, exist_ok=True)
    index = 0
    print("Capturing CH%d as transmission and CH%d as error." % (ch_transmission, ch_error))
    if points and points > 0:
        print(f"Waveform length: {points} points per channel.")
    else:
        print("Waveform length: full current oscilloscope record length.")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            started = time.time()
            scope.write("ACQUIRE:STATE STOP")
            transmission = read_waveform(scope, ch_transmission, points)
            error = read_waveform(scope, ch_error, points)
            scope.write("ACQUIRE:STATE RUN")
            stamp = time.strftime("%Y%m%d_%H%M%S")
            frame_path = output_dir / f"scope_frame_{stamp}_{index:04d}.csv"
            latest_path = output_dir / "latest_scope_frame.csv"
            save_csv(frame_path, transmission, error)
            save_csv(latest_path, transmission, error)
            index += 1
            elapsed = time.time() - started
            time.sleep(max(0.0, interval_s - elapsed))
    finally:
        try:
            scope.write("ACQUIRE:STATE RUN")
            scope.close()
        except Exception:
            pass


def auto_capture(output_dir: Path, points: int | None, interval_s: float, ch_transmission: int, ch_error: int) -> None:
    resource = discover_scope(scan_lan=True)
    capture_loop(resource, output_dir, points, interval_s, ch_transmission, ch_error)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-capture CH1/CH2 waveforms from a Tektronix MDO/MSO scope.")
    parser.add_argument("--auto", action="store_true", help="Auto-discover Tektronix scope and start loop capture.")
    parser.add_argument("--list", action="store_true", help="List VISA resources and exit.")
    parser.add_argument("--resource", help="Manual VISA resource, for example TCPIP0::192.168.1.50::INSTR.")
    parser.add_argument("--once", action="store_true", help="Capture one frame to CSV.")
    parser.add_argument("--loop", action="store_true", help="Capture frames repeatedly.")
    parser.add_argument("--output", default="scope_captures/latest_scope_frame.csv", help="Output CSV for --once.")
    parser.add_argument("--output-dir", default="scope_captures", help="Output folder for --auto/--loop.")
    parser.add_argument(
        "--points",
        type=int,
        default=None,
        help="Waveform points per channel. Default: read the oscilloscope's full current record length.",
    )
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between loop captures.")
    parser.add_argument("--transmission-channel", type=int, default=1, choices=[1, 2, 3, 4])
    parser.add_argument("--error-channel", type=int, default=2, choices=[1, 2, 3, 4])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (args.auto or args.list or args.once or args.loop or args.resource):
        print("No mode selected; starting automatic discovery and capture.")
        args.auto = True

    if args.list:
        list_resources()
        return 0

    if args.auto:
        auto_capture(
            Path(args.output_dir),
            args.points,
            args.interval,
            args.transmission_channel,
            args.error_channel,
        )
        return 0

    if not args.resource:
        raise SystemExit("Use --resource, --auto, or --list.")

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

    capture_loop(
        args.resource,
        Path(args.output_dir),
        args.points,
        args.interval,
        args.transmission_channel,
        args.error_channel,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
