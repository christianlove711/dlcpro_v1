from __future__ import annotations


class DlcproControlStub:
    """Placeholder for the future DLC pro hardware control adapter.

    Replace this class with SDK-backed calls when the real connection path is ready.
    The oscilloscope capture path can be validated before enabling any hardware writes.
    """

    def set_scan_offset(self, voltage_v: float) -> None:
        raise NotImplementedError("DLC pro scan offset control is not connected yet.")

    def set_pzt_fine(self, voltage_v: float) -> None:
        raise NotImplementedError("DLC pro PZT fine control is not connected yet.")

    def set_scan_amplitude(self, amplitude_vpp: float) -> None:
        raise NotImplementedError("DLC pro scan amplitude control is not connected yet.")

    def enable_falc(self) -> None:
        raise NotImplementedError("FALC enable control is not connected yet.")

    def disable_falc(self) -> None:
        raise NotImplementedError("FALC disable control is not connected yet.")
