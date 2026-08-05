from __future__ import annotations

from dataclasses import fields

import pytest

import dlcpro_service
from toptica.lasersdk.client import DecopError, DeviceNotFoundError
from dlcpro_service import (
    ConnectionSettings,
    DeviceSnapshot,
    DlcProService,
    SnapshotRequest,
    SnapshotSection,
)


def _empty_snapshot() -> DeviceSnapshot:
    values = {}
    string_fields = {
        "connection_mode",
        "connection_target",
        "system_label",
        "serial_number",
        "fw_ver",
        "system_type",
        "system_model",
        "uptime_txt",
        "latest_message",
        "cc_status_txt",
        "sc_unit",
        "lock_state_txt",
    }
    bool_fields = {
        field.name
        for field in fields(DeviceSnapshot)
        if any(token in field.name for token in ("enabled", "emission", "hold", "interlock", "sign", "writable"))
    }
    for field in fields(DeviceSnapshot):
        if field.name in {"stabilization", "falc1"}:
            values[field.name] = None
        elif field.name in string_fields:
            values[field.name] = ""
        elif field.name in bool_fields:
            values[field.name] = False
        else:
            values[field.name] = 0
    return DeviceSnapshot(**values)


def test_partial_snapshot_merges_into_full_cache(monkeypatch) -> None:
    service = DlcProService()
    service._snapshot_cache = _empty_snapshot()
    monkeypatch.setattr(service, "_device_required", lambda: object())
    monkeypatch.setattr(service, "_read_core_values", lambda device: {"uptime_txt": "01:23", "current_act": 4.2})

    updated = service._read_snapshot_request_unlocked(SnapshotRequest.core())
    assert updated.uptime_txt == "01:23"
    assert updated.current_act == 4.2
    assert updated.sc_frequency == 0


def test_section_request_updates_only_requested_reader(monkeypatch) -> None:
    service = DlcProService()
    service._snapshot_cache = _empty_snapshot()
    monkeypatch.setattr(service, "_device_required", lambda: object())
    monkeypatch.setattr(service, "_read_laser_values", lambda device: {"current_set": 11.5})
    monkeypatch.setattr(
        service,
        "_read_scan_lock_values",
        lambda device: (_ for _ in ()).throw(AssertionError("unexpected scan read")),
    )

    updated = service._read_snapshot_request_unlocked(
        SnapshotRequest.for_sections(SnapshotSection.LASER)
    )
    assert updated.current_set == 11.5


def test_connect_cleans_up_when_initial_snapshot_is_rejected(monkeypatch) -> None:
    class FakeDevice:
        def __init__(self, connection) -> None:
            self.connection = connection
            self.opened = False
            self.closed = False

        def open(self) -> None:
            self.opened = True

        def close(self) -> None:
            self.closed = True

    created = []

    def make_device(connection):
        device = FakeDevice(connection)
        created.append(device)
        return device

    service = DlcProService()
    monkeypatch.setattr(service, "_build_connection", lambda settings: object())
    monkeypatch.setattr(dlcpro_service, "DLCpro", make_device)
    monkeypatch.setattr(
        service,
        "_read_core_values",
        lambda device: (_ for _ in ()).throw(RuntimeError("Error: -22 no access")),
    )

    with pytest.raises(RuntimeError, match="no access"):
        service.connect(ConnectionSettings(mode="network", target="169.254.18.52"))

    assert created[0].opened is True
    assert created[0].closed is True
    assert service.is_connected is False
    assert service._settings is None
    assert service._snapshot_cache is None


def test_optional_section_no_access_does_not_drop_connection(monkeypatch) -> None:
    service = DlcProService()
    service._settings = ConnectionSettings(mode="network", target="169.254.18.52")
    service._snapshot_cache = service._empty_snapshot(service._settings)
    service._device = object()
    monkeypatch.setattr(
        service,
        "_read_laser_values",
        lambda device: (_ for _ in ()).throw(DecopError(-22, "no access")),
    )

    updated = service._read_snapshot_request_unlocked(
        SnapshotRequest.for_sections(SnapshotSection.LASER)
    )

    assert service.is_connected is True
    assert updated.current_set == 0.0
    assert SnapshotSection.LASER in service._unavailable_sections


def test_windows_socket_access_denied_error_points_to_vpn_or_firewall() -> None:
    message = DlcProService.format_error(
        DeviceNotFoundError("[WinError 5] 拒绝访问")
    )

    assert "Windows 阻止" in message
    assert "VPN" in message
    assert "169.254.0.0/16" in message


def test_sdk_timeout_error_points_to_competing_topas_client() -> None:
    message = DlcProService.format_error(
        DeviceNotFoundError("[WinError 121] 信号灯超时时间已到")
    )

    assert "SDK 连接端口响应超时" in message
    assert "1998/1999" in message
    assert "TOPAS_DLC_pro.exe" in message


def test_network_connection_uses_configured_command_and_monitoring_ports(monkeypatch) -> None:
    captured = {}

    def fake_network_connection(host, **kwargs):
        captured["host"] = host
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(dlcpro_service, "NetworkConnection", fake_network_connection)
    service = DlcProService()
    service._build_connection(ConnectionSettings(
        mode="network",
        target="169.254.18.52",
        timeout=7,
        command_line_port=2198,
        monitoring_line_port=2199,
    ))

    assert captured == {
        "host": "169.254.18.52",
        "command_line_port": 2198,
        "monitoring_line_port": 2199,
        "timeout": 7,
    }


def test_engage_falc_uses_current_path_selection_without_tuning_writes(monkeypatch) -> None:
    class Parameter:
        def __init__(self, value):
            self.value = value
            self.writes = []

        def get(self):
            return self.value

        def set(self, value):
            self.value = value
            self.writes.append(value)

    scan_enabled = Parameter(True)
    main_enabled = Parameter(False)
    unlim_enabled = Parameter(False)
    board = type("Board", (), {
        "path_selection": Parameter(3),
        "main": type("Main", (), {"enabled": main_enabled})(),
        "unlim": type("Unlim", (), {"enabled": unlim_enabled})(),
    })()
    service = DlcProService()
    monkeypatch.setattr(service, "_falc", lambda _index: board)
    monkeypatch.setattr(
        service, "_scan", lambda: type("Scan", (), {"enabled": scan_enabled})()
    )
    sentinel = object()
    monkeypatch.setattr(
        service, "_read_snapshot_request_unlocked", lambda _request: sentinel
    )

    assert service.engage_falc1_configured_paths() is sentinel
    assert scan_enabled.writes == [False]
    assert unlim_enabled.writes == [True]
    assert main_enabled.writes == [True]


def test_engage_falc_rejects_none_path_before_stopping_scan(monkeypatch) -> None:
    class Parameter:
        def __init__(self, value):
            self.value = value
            self.writes = []

        def get(self):
            return self.value

        def set(self, value):
            self.value = value
            self.writes.append(value)

    scan_enabled = Parameter(True)
    board = type("Board", (), {"path_selection": Parameter(0)})()
    service = DlcProService()
    monkeypatch.setattr(service, "_falc", lambda _index: board)
    monkeypatch.setattr(
        service, "_scan", lambda: type("Scan", (), {"enabled": scan_enabled})()
    )

    with pytest.raises(RuntimeError, match="Path Selection"):
        service.engage_falc1_configured_paths()
    assert scan_enabled.writes == []


def test_engage_falc_rolls_back_partial_enable_failure(monkeypatch) -> None:
    class Parameter:
        def __init__(self, value, fail_on_true=False):
            self.value = value
            self.fail_on_true = fail_on_true
            self.writes = []

        def get(self):
            return self.value

        def set(self, value):
            self.writes.append(value)
            if self.fail_on_true and value is True:
                raise RuntimeError("simulated Main enable failure")
            self.value = value

    scan_enabled = Parameter(True)
    unlim_enabled = Parameter(False)
    main_enabled = Parameter(False, fail_on_true=True)
    board = type("Board", (), {
        "path_selection": Parameter(3),
        "main": type("Main", (), {"enabled": main_enabled})(),
        "unlim": type("Unlim", (), {"enabled": unlim_enabled})(),
    })()
    service = DlcProService()
    monkeypatch.setattr(service, "_falc", lambda _index: board)
    monkeypatch.setattr(
        service, "_scan", lambda: type("Scan", (), {"enabled": scan_enabled})()
    )

    with pytest.raises(RuntimeError, match="simulated Main"):
        service.engage_falc1_configured_paths()
    assert scan_enabled.value is True
    assert unlim_enabled.value is False
    assert main_enabled.value is False
