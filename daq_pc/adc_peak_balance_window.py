"""Independent ADC raw-code 00-mode automatic centering window."""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QAbstractSpinBox, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox,
    QTextEdit, QVBoxLayout, QWidget,
)

from widgets.common_controls import VisibleCheckBox

from .adc_peak_balance_algorithm import PeakBalanceSettings


PEAK_LOCK_STYLE = """
QMainWindow, QWidget#peakLockRoot { background:#f3f6fa; color:#172033;
    font-family:"Microsoft YaHei UI","Segoe UI"; font-size:13px; }
QScrollArea#peakLockScroll { background:#f3f6fa; border:0; }
QScrollBar:vertical { background:#eef2f7; width:10px; margin:0; }
QScrollBar::handle:vertical { background:#b9c6d8; border-radius:5px;
    min-height:36px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar:horizontal { background:#eef2f7; height:10px; margin:0; }
QScrollBar::handle:horizontal { background:#b9c6d8; border-radius:5px;
    min-width:36px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
QLabel { background:transparent; color:#172033; }
QFrame#card { background:#ffffff; border:1px solid #dce3ed;
    border-radius:10px; }
QWidget#parameterField { background:transparent; }
QLabel#title { font-size:21px; font-weight:700; color:#12233f; }
QLabel#muted { color:#69758a; }
QLabel#state { background:#e9f2ff; border:1px solid #bdd5fa;
    border-radius:8px; color:#195ca8; font-weight:700; padding:7px 10px; }
QLabel#manualAdvice { background:#fff7e8; border:1px solid #e0bd7b;
    border-radius:8px; color:#74470b; font-weight:600; padding:10px 12px; }
QLabel#manualAdvice:hover { background:#fff1d3; border-color:#d5a64f; }
QCheckBox#observeOnly { min-height:32px; spacing:8px; color:#195ca8;
    font-weight:700; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { min-height:32px; padding:0 8px;
    background:#ffffff; border:1px solid #cfd8e6; border-radius:6px;
    color:#172033; selection-color:#ffffff;
    selection-background-color:#2f6fcb; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
    border-color:#4b82cf; }
QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QLineEdit:disabled {
    background:#f0f2f5; border-color:#e0e5ec; color:#8993a4; }
QComboBox::drop-down { border:0; width:28px; }
QPushButton { min-height:34px; padding:0 16px; background:#ffffff;
    border:1px solid #cbd5e1; border-radius:7px; color:#25324a;
    font-weight:600; }
QPushButton:hover { background:#f6f8fb; border-color:#9eacbf; }
QPushButton:disabled { background:#f0f2f5; border-color:#e0e5ec;
    color:#a3adbb; }
QPushButton#start { background:#178455; border-color:#178455; color:white; }
QPushButton#stop { color:#ad2b34; border-color:#e3a7ab; }
QPushButton#save { background:#2774c8; border-color:#2774c8; color:white; }
QPushButton#infoButton { min-width:26px; max-width:26px;
    min-height:26px; max-height:26px; padding:0; border-radius:13px;
    background:#e8f2ff; color:#195ca8; border:1px solid #9fc5f3;
    font-weight:800; }
QMessageBox { background:#f3f6fa; color:#172033; }
QMessageBox QLabel { background:transparent; color:#172033;
    min-width:360px; padding:4px; }
QMessageBox QPushButton { min-width:78px; background:#ffffff;
    color:#25324a; border:1px solid #cbd5e1; }
QTextEdit { background:#ffffff; color:#475569; border:1px solid #dce3ed;
    border-radius:8px; padding:8px;
    selection-color:#ffffff; selection-background-color:#2f6fcb;
    font-family:Consolas,"Microsoft YaHei UI"; }
"""


PARAMETER_HELP = {
    "透射峰通道": "选择与示波器显示一致的逻辑ADC通道。默认：通道 A。",
    "峰极性": "指定正峰、负峰或自动判断。默认：自动判断。",
    "最小峰突出度（ADC码）": "峰相对鲁棒基线的最小突出度。默认：50 ADC码。",
    "噪声门槛倍数": "MAD噪声估计的倍数，与最小突出度取较大值。默认：6.0。",
    "主峰族最小强度比": "最强完整物理峰族相对第二峰族的最低突出度比。默认：5.0。",
    "峰周期允许误差": "主峰族实测周期相对1/f的允许误差。默认：10%。",
    "窄扫主峰最低保留比例": "最终幅度主峰至少保留宽扫参考主峰高度的比例。默认：5%。",
    "无效窗口原地重采次数": "周期、峰族或数据异常时Offset不动的最多复测次数。默认：3。",
    "快速扫频频率": "自动模式启动时写入；观察模式只使用设备读回值。默认：10 Hz。",
    "初始化Scan Amplitude": "自动模式宽扫入口幅度。默认：2.5 Vpp。",
    "初始化无峰搜索步长": "宽扫无主峰时按+1、-1、+2、-2步搜索。默认：1 V。",
    "宽扫方向试探步长": "宽扫仅用于判断理论跳转方向的一次试探。默认：0.05 V。",
    "宽扫缩幅门槛": "低于该不均匀度后停止调Offset并开始缩幅确认。默认：8%。",
    "宽扫缩幅确认窗口": "连续达标多少个独立窗口后直接缩至最终幅度。默认：2。",
    "宽扫理论残差修正次数": "完整理论跳转后允许的最多残差修正次数。默认：2。",
    "最终Scan Amplitude": "宽扫通过后一步写入的最终幅度，不会自动恢复到宽扫。默认：0.2 Vpp。",
    "最终粗调步长": "最终阶段距离目标较远或重新捕获时使用。默认：0.01 V。",
    "最终精调步长": "接近目标、误差过零或包围最佳点后使用。默认：0.001 V。",
    "最终最大Offset偏移": "相对缩幅入口Offset允许的最终阶段最大偏移。默认：0.09 V。",
    "最终锁定不均匀度门槛": "最终窗口的锁定判据。默认：5%。",
    "自动FALC确认窗口": "仅勾选自动FALC时使用；未勾选时首次达标立即停止写入。默认：3。",
}


class _ManualValueEditMixin:
    """Manual text editing without spin, wheel, or arrow-key stepping."""

    def _configure_manual_edit(self):
        self.setKeyboardTracking(False)
        self.setAccelerated(False)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)

    def wheelEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Up, Qt.Key_Down,
                           Qt.Key_PageUp, Qt.Key_PageDown):
            event.ignore()
            return
        super().keyPressEvent(event)


class ParameterDoubleSpinBox(_ManualValueEditMixin, QDoubleSpinBox):
    """Manual-only decimal parameter editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_manual_edit()

    def stepBy(self, steps: int) -> None:  # noqa: N802
        return


class ParameterSpinBox(_ManualValueEditMixin, QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_manual_edit()

    def stepBy(self, steps: int) -> None:  # noqa: N802
        return


class ClickableAdviceLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AdviceHistoryDialog(QDialog):
    """Non-modal, copyable operator guidance history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("人工操作建议记录")
        self.resize(820, 520)
        self.setMinimumSize(660, 420)
        self.setStyleSheet(PEAK_LOCK_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)
        title = QLabel("当前建议")
        title.setObjectName("title")
        layout.addWidget(title)
        self.current = QTextEdit()
        self.current.setReadOnly(True)
        self.current.setMinimumHeight(105)
        layout.addWidget(self.current)
        layout.addWidget(QLabel("建议历史（可选择并复制）"))
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        layout.addWidget(self.history, 1)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close_button)
        layout.addLayout(footer)

    def update_contents(self, current: str, history: list[str]) -> None:
        self.current.setPlainText(current)
        self.history.setPlainText("\n\n".join(history))
        cursor = self.history.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.history.setTextCursor(cursor)


class ParameterHelpDialog(QDialog):
    """Compact, consistently styled explanation for one algorithm setting."""

    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"参数说明：{title}")
        self.setModal(True)
        self.setFixedWidth(500)
        self.setSizeGripEnabled(False)
        self.setStyleSheet(PEAK_LOCK_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setStyleSheet(
            "font-size:16px; font-weight:700; color:#12233f;"
        )
        layout.addWidget(heading)

        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.description_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.description_label.setFixedWidth(458)
        self.description_label.setStyleSheet(
            "background:#f7f9fc; border:1px solid #dce3ed;"
            "border-radius:8px; padding:12px; color:#344054;"
        )
        layout.addWidget(self.description_label)

        footer = QHBoxLayout()
        footer.addStretch(1)
        close_button = QPushButton("确定")
        close_button.setDefault(True)
        close_button.setMinimumWidth(88)
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)


class AdcPeakBalanceWindow(QMainWindow):
    scope_requested = Signal(str)
    scan_control_requested = Signal()

    def __init__(self, controller, settings_store, parent=None,
                 falc_window_opener=None, embedded: bool = False):
        super().__init__(parent, Qt.Widget if embedded else Qt.Window)
        self.controller = controller
        self.settings_store = settings_store
        self.advice_history: list[str] = []
        self._last_advice = ""
        self.advice_dialog: AdviceHistoryDialog | None = None
        self.falc_window_opener = falc_window_opener
        self.setWindowTitle("ADC 00模自动锁频")
        if embedded:
            self.setMinimumSize(0, 520)
        else:
            self.resize(720, 740)
            self.setMinimumSize(380, 620)
        self.setStyleSheet(PEAK_LOCK_STYLE)

        scroll = QScrollArea()
        scroll.setObjectName("peakLockScroll")
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        # The independent window is freely resizable.  A horizontal bar only
        # appears when the operator makes it narrower than the parameter grid.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.main_scroll = scroll
        self.setCentralWidget(scroll)

        root = QWidget()
        root.setObjectName("peakLockRoot")
        root.setMinimumHeight(760)
        if embedded:
            # Preserve the control grid instead of letting it paint underneath
            # the scope pane when the combined workspace is narrow.
            root.setMinimumWidth(680)
        scroll.setWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(20, 18, 20, 20)
        page.setSpacing(12)
        title = QLabel("ADC原始码 00模自动居中与缩幅")
        title.setObjectName("title")
        note = QLabel(
            "仅用ADC原始码调整Scan Offset与Scan Amplitude；强制使用PC Voltage（PZT电压）扫描；"
            "达到最终幅度和峰间隔标准后可按当前配置使能FALC pro"
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        self.observe_only = VisibleCheckBox("仅观察算法判断（绝不写入DLC pro）")
        self.observe_only.setObjectName("observeOnly")
        self.observe_only.setChecked(True)
        self.observe_only.setToolTip(
            "勾选后只分析原始ADC码并显示判断结果，不修改Scan Offset或Scan Amplitude"
        )
        page.addWidget(title)
        page.addWidget(note)
        page.addWidget(self.observe_only)

        quick_actions = QHBoxLayout()
        self.algorithm_settings_button = QPushButton("隐藏算法参数")
        self.algorithm_settings_button.setCheckable(True)
        self.algorithm_settings_button.setChecked(True)
        self.algorithm_settings_button.setObjectName("save")
        self.show_scope_a_button = QPushButton("显示通道 A")
        self.show_scope_b_button = QPushButton("显示通道 B")
        self.scan_control_button = QPushButton("扫频控制")
        self.show_scope_a_button.setToolTip(
            "打开独立的通道A示波器，并排列到自动锁频窗口右侧"
        )
        self.show_scope_b_button.setToolTip(
            "打开独立的通道B示波器，并排列到自动锁频窗口右侧"
        )
        self.scan_control_button.setToolTip("打开主界面使用的同一个扫频控制窗口")
        quick_actions.addWidget(self.algorithm_settings_button)
        quick_actions.addWidget(self.show_scope_a_button)
        quick_actions.addWidget(self.show_scope_b_button)
        quick_actions.addWidget(self.scan_control_button)
        quick_actions.addStretch(1)
        page.addLayout(quick_actions)

        self.algorithm_settings_panel = QWidget()
        settings_layout = QVBoxLayout(self.algorithm_settings_panel)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        config = QWidget()
        grid = QVBoxLayout(config)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)
        self.parameter_info_buttons = {}

        def parameter_group(title):
            frame = QFrame()
            frame.setObjectName("card")
            box = QVBoxLayout(frame)
            box.setContentsMargins(16, 14, 16, 14)
            heading = QLabel(title)
            heading.setStyleSheet("font-weight:700; font-size:15px;")
            box.addWidget(heading)
            columns = QHBoxLayout()
            left_form, right_form = QFormLayout(), QFormLayout()
            for form in (left_form, right_form):
                form.setHorizontalSpacing(14)
                form.setVerticalSpacing(10)
            columns.addLayout(left_form, 1)
            columns.addLayout(right_form, 1)
            box.addLayout(columns)
            grid.addWidget(frame)
            return left_form, right_form

        peak_left, peak_right = parameter_group("峰识别参数")
        wide_left, wide_right = parameter_group("宽扫参数")
        final_left, final_right = parameter_group("最终锁定参数")
        self.parameter_form_left = peak_left
        self.parameter_form_right = peak_right
        self.channel = QComboBox()
        self.channel.addItem("通道 A", "A")
        self.channel.addItem("通道 B", "B")
        self.polarity = QComboBox()
        self.polarity.addItem("自动判断", "auto")
        self.polarity.addItem("正峰", "positive")
        self.polarity.addItem("负峰", "negative")
        self.min_prominence = ParameterSpinBox()
        self.min_prominence.setRange(0, 32767)
        self.min_prominence.setValue(50)
        self.noise_sigma = ParameterDoubleSpinBox()
        self.noise_sigma.setRange(1.0, 30.0)
        self.noise_sigma.setValue(6.0)
        self.noise_sigma.setDecimals(1)
        self.dominance = ParameterDoubleSpinBox()
        self.dominance.setRange(1.01, 20.0)
        self.dominance.setValue(5.0)
        self.dominance.setDecimals(2)
        self.period_tolerance = ParameterDoubleSpinBox()
        self.period_tolerance.setRange(0.1, 100.0)
        self.period_tolerance.setValue(10.0)
        self.period_tolerance.setSuffix(" %")
        self.narrow_main_height_ratio = ParameterDoubleSpinBox()
        self.narrow_main_height_ratio.setRange(0.1, 100.0)
        self.narrow_main_height_ratio.setValue(5.0)
        self.narrow_main_height_ratio.setSuffix(" %")
        self.invalid_retry_windows = ParameterSpinBox()
        self.invalid_retry_windows.setRange(0, 20)
        self.invalid_retry_windows.setValue(3)
        self._add_parameter_row(peak_left, "透射峰通道", self.channel)
        self._add_parameter_row(peak_left, "峰极性", self.polarity)
        self._add_parameter_row(peak_left, "最小峰突出度（ADC码）", self.min_prominence)
        self._add_parameter_row(peak_left, "噪声门槛倍数", self.noise_sigma)
        self._add_parameter_row(peak_right, "主峰族最小强度比", self.dominance)
        self._add_parameter_row(peak_right, "峰周期允许误差", self.period_tolerance)
        self._add_parameter_row(peak_right, "窄扫主峰最低保留比例", self.narrow_main_height_ratio)
        self._add_parameter_row(peak_right, "无效窗口原地重采次数", self.invalid_retry_windows)

        self.offset_step = ParameterDoubleSpinBox()
        self.offset_step.setRange(0.000001, 1_000_000.0)
        self.offset_step.setDecimals(6)
        self.offset_step.setValue(0.05)
        self.search_frequency = ParameterDoubleSpinBox()
        self.search_frequency.setRange(0.01, 1000.0)
        self.search_frequency.setDecimals(2)
        self.search_frequency.setValue(10.0)
        self.search_frequency.setSuffix(" Hz")
        self.initial_search_amplitude = ParameterDoubleSpinBox()
        self.initial_search_amplitude.setRange(0.000001, 1_000_000.0)
        self.initial_search_amplitude.setDecimals(6)
        self.initial_search_amplitude.setValue(2.5)
        self.initial_offset_search_step = ParameterDoubleSpinBox()
        self.initial_offset_search_step.setRange(0.000001, 1_000_000.0)
        self.initial_offset_search_step.setDecimals(6)
        self.initial_offset_search_step.setValue(1.0)
        self.min_offset_step = ParameterDoubleSpinBox()
        self.min_offset_step.setRange(0.000001, 1_000_000.0)
        self.min_offset_step.setDecimals(6)
        self.min_offset_step.setValue(0.001)
        self.target_amplitude = ParameterDoubleSpinBox()
        self.target_amplitude.setRange(0.000001, 1_000_000.0)
        self.target_amplitude.setDecimals(6)
        self.target_amplitude.setValue(0.2)
        self.search_tolerance = ParameterDoubleSpinBox()
        self.search_tolerance.setRange(0.1, 25.0)
        self.search_tolerance.setValue(8.0)
        self.search_tolerance.setSuffix(" %")
        self.model_corrections = ParameterSpinBox()
        self.model_corrections.setRange(0, 10)
        self.model_corrections.setValue(2)
        self.search_windows = ParameterSpinBox()
        self.search_windows.setRange(1, 10)
        self.search_windows.setValue(2)
        self.final_windows = ParameterSpinBox()
        self.final_windows.setRange(1, 10)
        self.final_windows.setValue(3)
        self.balance_tolerance = ParameterDoubleSpinBox()
        self.balance_tolerance.setRange(0.1, 25.0)
        self.balance_tolerance.setValue(5.0)
        self.balance_tolerance.setSuffix(" %")
        self.final_coarse_step = ParameterDoubleSpinBox()
        self.final_coarse_step.setRange(0.000001, 1_000_000.0)
        self.final_coarse_step.setDecimals(6)
        self.final_coarse_step.setValue(0.01)
        self.final_max_offset_deviation = ParameterDoubleSpinBox()
        self.final_max_offset_deviation.setRange(0.000001, 1_000_000.0)
        self.final_max_offset_deviation.setDecimals(6)
        self.final_max_offset_deviation.setValue(0.09)
        self._add_parameter_row(wide_left, "快速扫频频率", self.search_frequency)
        self._add_parameter_row(wide_left, "初始化Scan Amplitude", self.initial_search_amplitude)
        self._add_parameter_row(wide_left, "初始化无峰搜索步长", self.initial_offset_search_step)
        self._add_parameter_row(wide_left, "宽扫方向试探步长", self.offset_step)
        self._add_parameter_row(wide_right, "宽扫缩幅门槛", self.search_tolerance)
        self._add_parameter_row(wide_right, "宽扫缩幅确认窗口", self.search_windows)
        self._add_parameter_row(wide_right, "宽扫理论残差修正次数", self.model_corrections)
        self._add_parameter_row(final_left, "最终Scan Amplitude", self.target_amplitude)
        self._add_parameter_row(final_left, "最终粗调步长", self.final_coarse_step)
        self._add_parameter_row(final_left, "最终精调步长", self.min_offset_step)
        self._add_parameter_row(final_right, "最终最大Offset偏移", self.final_max_offset_deviation)
        self._add_parameter_row(final_right, "最终锁定不均匀度门槛", self.balance_tolerance)
        self._add_parameter_row(final_right, "自动FALC确认窗口", self.final_windows)
        settings_layout.addWidget(config)

        strategy = QFrame()
        strategy.setObjectName("card")
        strategy_box = QVBoxLayout(strategy)
        strategy_box.setContentsMargins(16, 14, 16, 14)
        strategy_title = QLabel("两级自动居中策略（PC Voltage）")
        strategy_title.setStyleSheet("font-weight:700; font-size:15px;")
        strategy_box.addWidget(strategy_title)
        strategy_note = QLabel(
            "自动模式先写入初始化Amplitude；无峰时以初始化步长左右搜索Offset。"
            "找到主峰族后只做一次方向试探，再跳完整理论距离；"
            "达到宽扫门槛后一步缩到最终幅度，随后按改善方向粗调并自动转精调。"
            "最终阶段不执行网格遍历，也不会恢复或扩大Amplitude。"
        )
        strategy_note.setObjectName("muted")
        strategy_note.setWordWrap(True)
        strategy_box.addWidget(strategy_note)
        stage_grid = QGridLayout()
        stage_grid.setHorizontalSpacing(9)
        stage_grid.setVerticalSpacing(8)
        for column, text in enumerate((
            "阶段", "Amplitude", "允许不均匀度", "Offset策略", "独立窗口",
        )):
            header = QLabel(text)
            header.setStyleSheet("font-weight:700; color:#475569;")
            stage_grid.addWidget(header, 0, column)
        self.strategy_edits = {}
        self.strategy_labels = {}
        stage_rows = (
            ("快速寻峰", "启动幅度", "8%", "理论预测 + 单次方向试探", "2"),
            ("最终锁定", "0.200 Vpp", "5%", "定向0.01 V → 0.001 V", "3（仅FALC）"),
        )
        for row, values in enumerate(stage_rows, start=1):
            for column, value in enumerate(values):
                label = QLabel(value)
                label.setWordWrap(True)
                stage_grid.addWidget(label, row, column)
                self.strategy_labels[(row, column)] = label
        for control in (
            self.initial_search_amplitude, self.target_amplitude,
            self.search_tolerance,
            self.balance_tolerance, self.min_offset_step,
            self.final_coarse_step, self.final_max_offset_deviation,
            self.search_windows,
            self.final_windows,
        ):
            control.valueChanged.connect(self._update_strategy_summary)
        self._update_strategy_summary()
        strategy_box.addLayout(stage_grid)
        settings_layout.addWidget(strategy)

        settings_footer = QHBoxLayout()
        settings_footer.addStretch(1)
        self.save_button = QPushButton("保存算法参数")
        self.save_button.setObjectName("save")
        settings_footer.addWidget(self.save_button)
        # Keep Save visible at the top of the expanded section; the parameter
        # list is long and operators should not need to scroll to its end.
        settings_layout.insertLayout(0, settings_footer)
        page.addWidget(self.algorithm_settings_panel)

        status = QFrame()
        status.setObjectName("card")
        status_grid = QGridLayout(status)
        status_grid.setContentsMargins(16, 14, 16, 14)
        self.state_label = QLabel("未开始")
        self.state_label.setObjectName("state")
        status_grid.addWidget(self.state_label, 0, 0, 1, 4)
        self.values = {}
        for row, (key, title) in enumerate((
            ("offset", "Offset 当前/启动"),
            ("amplitude", "Amplitude 当前/目标/可靠/启动"),
            ("period", "扫描频率/设备周期/实测周期"),
            ("peaks", "主峰族/第二峰族/强度比/SNR"),
            ("spacing", "Δt1/Δt2/不均匀度"),
        ), start=1):
            status_grid.addWidget(QLabel(title), row, 0)
            label = QLabel("--")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            status_grid.addWidget(label, row, 1, 1, 3)
            self.values[key] = label
        status_grid.addWidget(QLabel("Offset当前步进"), 6, 0)
        step_label = QLabel("--")
        step_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        status_grid.addWidget(step_label, 6, 1, 1, 3)
        self.values["step"] = step_label
        status_grid.addWidget(QLabel("当前阶段"), 7, 0)
        stage_label = QLabel("--")
        stage_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        status_grid.addWidget(stage_label, 7, 1, 1, 3)
        self.values["stage"] = stage_label
        status_grid.addWidget(QLabel("人工操作建议"), 8, 0, Qt.AlignTop)
        self.manual_advice_label = ClickableAdviceLabel(
            "开始观察后，这里会给出保持、修改Offset或修改Amplitude的具体建议。"
        )
        self.manual_advice_label.setObjectName("manualAdvice")
        self.manual_advice_label.setWordWrap(True)
        self.manual_advice_label.setMinimumHeight(74)
        self.manual_advice_label.setCursor(Qt.PointingHandCursor)
        self.manual_advice_label.setToolTip("点击打开完整建议与历史记录")
        self.manual_advice_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        status_grid.addWidget(self.manual_advice_label, 8, 1, 1, 3)
        page.addWidget(status)

        controls = QHBoxLayout()
        self.start_button = QPushButton("开始自动锁频")
        self.start_button.setObjectName("start")
        self.stop_button = QPushButton("停止")
        self.stop_button.setObjectName("stop")
        self.restore_button = QPushButton("恢复启动Offset/Amplitude")
        self.falc_button = QPushButton("FALC pro设置")
        self.falc_button.setToolTip("打开现有FALC pro控制界面；自动流程不会修改其中参数")
        self.auto_falc = VisibleCheckBox("达到设定标准后自动使能FALC pro")
        self.auto_falc.setToolTip(
            "仅在自动控制模式下生效。停止Scan后按FALC pro当前Path Selection使能，"
            "不修改增益、滤波或范围参数；未勾选时最终验收通过即停止自动调节，"
            "保持当前Scan和锁定参数。"
        )
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.restore_button)
        controls.addStretch(1)
        page.addLayout(controls)
        falc_options = QHBoxLayout()
        falc_options.addWidget(self.auto_falc)
        falc_options.addStretch(1)
        falc_options.addWidget(self.falc_button)
        page.addLayout(falc_options)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(90)
        self.log.setMaximumHeight(140)
        page.addWidget(self.log)

        self.save_button.clicked.connect(self._save_parameters)
        self.algorithm_settings_button.toggled.connect(
            self._toggle_algorithm_settings
        )
        self.show_scope_a_button.clicked.connect(
            lambda: self.scope_requested.emit("A")
        )
        self.show_scope_b_button.clicked.connect(
            lambda: self.scope_requested.emit("B")
        )
        self.scan_control_button.clicked.connect(
            self.scan_control_requested.emit
        )
        self.start_button.clicked.connect(self._start)
        self.stop_button.clicked.connect(lambda: self.controller.stop())
        self.restore_button.clicked.connect(self._restore)
        self.falc_button.clicked.connect(self._open_falc_window)
        self.controller.running_changed.connect(self._running_changed)
        self.controller.status_changed.connect(self._render_status)
        self.controller.log_message.connect(self.log.append)
        self.observe_only.toggled.connect(self._mode_changed)
        self.manual_advice_label.clicked.connect(self._show_advice_history)
        self._restore_ui_settings()
        self._mode_changed()
        self._running_changed(False)

    def _toggle_algorithm_settings(self, visible: bool) -> None:
        self.algorithm_settings_panel.setVisible(bool(visible))
        self.algorithm_settings_button.setText(
            "隐藏算法参数" if visible else "显示算法参数"
        )

    def _update_strategy_summary(self, *_args) -> None:
        labels = getattr(self, "strategy_labels", {})
        if not labels:
            return
        labels[(1, 2)].setText(f"{self.search_tolerance.value():g}%")
        labels[(1, 1)].setText(
            f"{self.initial_search_amplitude.value():.3f} Vpp"
        )
        labels[(1, 4)].setText(str(self.search_windows.value()))
        labels[(2, 1)].setText(f"{self.target_amplitude.value():.3f} Vpp")
        labels[(2, 2)].setText(f"{self.balance_tolerance.value():g}%")
        labels[(2, 3)].setText(
            f"定向{self.final_coarse_step.value():.3f} V → "
            f"{self.min_offset_step.value():.3f} V，"
            f"边界±{self.final_max_offset_deviation.value():.3f} V"
        )
        labels[(2, 4)].setText(f"{self.final_windows.value()}（仅FALC）")

    def _add_parameter_row(self, form: QFormLayout, title: str,
                           control: QWidget) -> None:
        field = QWidget()
        field.setObjectName("parameterField")
        field.setAttribute(Qt.WA_StyledBackground, True)
        field.setMinimumWidth(176)
        field.setMaximumWidth(214)
        field_layout = QHBoxLayout(field)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(7)
        field_layout.addWidget(control, 1)
        info = QPushButton("!")
        info.setObjectName("infoButton")
        info.setToolTip(f"查看“{title}”的说明和软件允许范围")
        info.setAccessibleName(f"{title}参数说明")
        info.clicked.connect(
            lambda _checked=False, name=title: self._show_parameter_help(name)
        )
        field_layout.addWidget(info, 0, Qt.AlignVCenter)
        self.parameter_info_buttons[title] = info
        form.addRow(title, field)

    def _show_parameter_help(self, title: str) -> None:
        ParameterHelpDialog(title, PARAMETER_HELP[title], self).exec()

    def _numeric_parameter_widgets(self):
        return (
            self.min_prominence, self.noise_sigma, self.dominance,
            self.period_tolerance, self.narrow_main_height_ratio,
            self.invalid_retry_windows,
            self.offset_step, self.search_frequency,
            self.initial_search_amplitude, self.initial_offset_search_step,
            self.target_amplitude, self.final_coarse_step, self.min_offset_step,
            self.final_max_offset_deviation, self.search_tolerance,
            self.model_corrections,
            self.search_windows, self.balance_tolerance, self.final_windows,
        )

    def _commit_parameter_edits(self) -> None:
        for widget in self._numeric_parameter_widgets():
            widget.interpretText()

    def _save_parameters(self) -> None:
        try:
            self._commit_parameter_edits()
            self.current_settings()
            self._save_ui_settings()
        except Exception as exc:
            QMessageBox.warning(self, "参数无法保存", str(exc))
            return
        QMessageBox.information(
            self,
            "参数已保存",
            "自动锁频参数已保存。下次开始观察或自动锁频时生效。",
        )

    def current_settings(self) -> PeakBalanceSettings:
        return PeakBalanceSettings(
            channel=str(self.channel.currentData()),
            polarity=str(self.polarity.currentData()),
            min_prominence_codes=float(self.min_prominence.value()),
            noise_sigma=float(self.noise_sigma.value()),
            main_family_ratio=float(self.dominance.value()),
            period_tolerance=float(self.period_tolerance.value()) / 100.0,
            narrow_main_height_ratio=float(self.narrow_main_height_ratio.value()) / 100.0,
            invalid_retry_windows=int(self.invalid_retry_windows.value()),
            wide_probe_step=float(self.offset_step.value()),
            final_fine_step=float(self.min_offset_step.value()),
            final_amplitude=float(self.target_amplitude.value()),
            final_coarse_step=float(self.final_coarse_step.value()),
            final_max_offset_deviation=float(self.final_max_offset_deviation.value()),
            final_balance_tolerance=float(self.balance_tolerance.value()) / 100.0,
            falc_confirm_windows=int(self.final_windows.value()),
            wide_shrink_tolerance=float(self.search_tolerance.value()) / 100.0,
            wide_confirm_windows=int(self.search_windows.value()),
            wide_model_corrections=int(self.model_corrections.value()),
            search_frequency_hz=float(self.search_frequency.value()),
            initial_search_amplitude=float(self.initial_search_amplitude.value()),
            initial_offset_search_step=float(self.initial_offset_search_step.value()),
        ).validated()

    def _start(self):
        try:
            self._commit_parameter_edits()
            settings = self.current_settings()
            self._save_ui_settings()
            self.controller.start(
                settings,
                observe_only=self.observe_only.isChecked(),
                auto_engage_falc=self.auto_falc.isChecked(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "无法开始自动锁频", str(exc))

    def _restore(self):
        try:
            self.controller.restore_start_values()
        except Exception as exc:
            QMessageBox.warning(self, "无法恢复启动参数", str(exc))

    def _running_changed(self, running: bool):
        self.save_button.setEnabled(not running)
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.restore_button.setEnabled(not running)
        self.observe_only.setEnabled(not running)
        self.auto_falc.setEnabled(not running and not self.observe_only.isChecked())
        self.falc_button.setEnabled(not running and self.falc_window_opener is not None)
        for widget in (
            self.channel, self.polarity, self.min_prominence,
            self.noise_sigma, self.dominance, self.offset_step,
            self.period_tolerance, self.narrow_main_height_ratio,
            self.invalid_retry_windows,
            self.search_frequency,
            self.initial_search_amplitude, self.initial_offset_search_step,
            self.target_amplitude, self.final_coarse_step, self.min_offset_step,
            self.final_max_offset_deviation, self.search_tolerance,
            self.model_corrections,
            self.search_windows, self.balance_tolerance, self.final_windows,
        ):
            widget.setEnabled(not running)
        for edit in self.strategy_edits.values():
            edit.setEnabled(not running)

    def _mode_changed(self):
        observing = self.observe_only.isChecked()
        self.auto_falc.setEnabled(not observing and not self.controller.running)
        self.start_button.setText("开始观察" if observing else "开始自动锁频")
        self.start_button.setToolTip(
            "只判断00模、周期和居中误差，并给出人工调节建议；不写DLC pro"
            if observing else
            "允许算法自动写入Scan Offset和Scan Amplitude"
        )

    def _open_falc_window(self) -> None:
        if self.falc_window_opener is None:
            QMessageBox.information(
                self, "FALC pro设置", "请从DLC pro主控制台打开FALC pro设置。"
            )
            return
        self.falc_window_opener()

    def _render_status(self, data: dict):
        observation = data["observation"]
        state_names = {
            "idle": "未开始", "select": "自动选择00模",
            "wide_probe": "宽扫方向试探",
            "wide_probe_negative": "宽扫反向试探",
            "wide_jump": "宽扫完整理论跳转",
            "wide_correct": "宽扫理论残差修正",
            "wide_confirm": "宽扫缩幅确认",
            "final_shrink": "一步缩到最终幅度",
            "final_adjust": "最终定向调节",
            "final_reacquire": "最终粗步长重新捕获",
            "final_return": "恢复最终最佳Offset",
            "final_confirm": "自动FALC连续确认",
            "startup_offset_search": "启动Offset左右扩展寻峰",
            "track": "最终锁定完成",
            "observe": "仅观察（禁止写入）", "fault": "已停止/故障",
            "falc_enabled": "FALC pro已使能",
        }
        state = str(data.get("state", "idle"))
        self.state_label.setText(
            f"{state_names.get(state, state)} · {data.get('message', '')}"
        )
        self.values["offset"].setText(
            f"{data['offset']:.6f} / {float(data['start_offset'] or 0):.6f}"
        )
        self.values["amplitude"].setText(
            f"{data['amplitude']:.6f} / "
            f"{float(data.get('target_amplitude', 0.0)):.6f} / "
            f"{data['last_good_amplitude']:.6f} / "
            f"{float(data['start_amplitude'] or 0):.6f}"
        )
        frequency = float(data.get("scan_frequency", 0.0))
        device_period = 1.0 / frequency if frequency > 0 else 0.0
        self.values["period"].setText(
            f"{frequency:g} Hz / {device_period:.4f} s / "
            f"{observation.measured_period:.4f} s"
        )
        self.values["peaks"].setText(
            f"{observation.prominence:.1f} / {observation.second_prominence:.1f} / "
            f"{observation.dominance_ratio:.2f} / {observation.snr:.1f}（ADC码）"
        )
        self.values["spacing"].setText(
            f"{observation.delta_t1:.4f} s / {observation.delta_t2:.4f} s / "
            f"{observation.balance_error * 100:.2f} %"
        )
        self.values["step"].setText(
            f"{float(data.get('offset_step', 0.0)):.6f} · "
            f"{data.get('step_profile', '用户设定')}"
        )
        stage_target = data.get("stage_target_amplitude")
        shrink_text = (
            "不再缩幅" if stage_target is None
            else f"下一步→{float(stage_target):.6f} Vpp"
        )
        self.values["stage"].setText(
            f"{data.get('stage_name', '--')} / 门槛≤"
            f"{float(data.get('stage_tolerance', 0.0)) * 100:.2f}% / "
            f"{shrink_text} / 连续{int(data.get('stage_windows', 0))}个独立窗口"
        )
        advice = str(
            data.get("manual_advice") or data.get("message") or "--"
        )
        self.manual_advice_label.setText(
            advice + "\n点击此处查看完整建议与历史记录"
        )
        if advice != self._last_advice:
            self._last_advice = advice
            entry = f"{time.strftime('%H:%M:%S')}\n{advice}"
            self.advice_history.append(entry)
            self.advice_history = self.advice_history[-200:]
        if self.advice_dialog is not None:
            self.advice_dialog.update_contents(advice, self.advice_history)

    def _show_advice_history(self) -> None:
        if self.advice_dialog is None:
            self.advice_dialog = AdviceHistoryDialog(self)
        current = self._last_advice or self.manual_advice_label.text()
        self.advice_dialog.update_contents(current, self.advice_history)
        self.advice_dialog.show()
        self.advice_dialog.raise_()
        self.advice_dialog.activateWindow()

    def _restore_ui_settings(self):
        s = self.settings_store
        def migrated(new_key, old_key, default):
            if s.contains(new_key):
                return s.value(new_key)
            if old_key and s.contains(old_key):
                return s.value(old_key)
            return default
        pairs = (
            (self.channel, "peak_lock/channel", "A"),
            (self.polarity, "peak_lock/polarity", "auto"),
        )
        for combo, key, default in pairs:
            index = combo.findData(str(s.value(key, default)))
            if index >= 0:
                combo.setCurrentIndex(index)
        self.observe_only.setChecked(
            str(s.value("peak_lock/observe_only", "true")).lower()
            in ("1", "true", "yes")
        )
        self.auto_falc.setChecked(
            str(s.value("peak_lock/auto_falc", "false")).lower()
            in ("1", "true", "yes")
        )
        parameters_visible = (
            str(s.value("peak_lock/parameters_visible", "true")).lower()
            in ("1", "true", "yes")
        )
        self.algorithm_settings_button.setChecked(parameters_visible)
        self._toggle_algorithm_settings(parameters_visible)
        numeric = (
            (self.min_prominence, "peak_lock/min_prominence", 50),
            (self.noise_sigma, "peak_lock/noise_sigma", 6.0),
            (self.dominance, "peak_lock/main_family_ratio", 5.0, "peak_lock/dominance"),
            (self.period_tolerance, "peak_lock/period_tolerance", 10.0, None),
            (self.narrow_main_height_ratio, "peak_lock/narrow_main_height_ratio", 5.0, None),
            (self.invalid_retry_windows, "peak_lock/invalid_retry_windows", 3, None),
            (self.offset_step, "peak_lock/wide_probe_step", 0.05, "peak_lock/direction_probe_step"),
            (self.search_frequency, "peak_lock/search_frequency_hz", 10.0),
            (self.initial_search_amplitude, "peak_lock/initial_search_amplitude", 2.5),
            (self.initial_offset_search_step, "peak_lock/initial_offset_search_step", 1.0),
            (self.min_offset_step, "peak_lock/final_fine_step", 0.001, "peak_lock/min_offset_step"),
            (self.target_amplitude, "peak_lock/final_amplitude", 0.2, "peak_lock/target_amplitude"),
            (self.final_coarse_step, "peak_lock/final_coarse_step", 0.01, None),
            (self.final_max_offset_deviation, "peak_lock/final_max_offset_deviation", 0.09, None),
            (self.search_tolerance, "peak_lock/wide_shrink_tolerance", 8.0, "peak_lock/search_tolerance"),
            (self.model_corrections, "peak_lock/wide_model_corrections", 2, "peak_lock/model_corrections"),
            (self.search_windows, "peak_lock/wide_confirm_windows", 2, "peak_lock/search_windows"),
            (self.balance_tolerance, "peak_lock/final_balance_tolerance", 5.0, "peak_lock/final_tolerance"),
            (self.final_windows, "peak_lock/falc_confirm_windows", 3, "peak_lock/final_windows"),
        )
        for item in numeric:
            widget, key, default = item[:3]
            old_key = item[3] if len(item) > 3 else None
            widget.setValue(float(migrated(key, old_key, default)))

    def _save_ui_settings(self):
        s = self.settings_store
        s.setValue("peak_lock/channel", self.channel.currentData())
        s.setValue("peak_lock/polarity", self.polarity.currentData())
        s.setValue("peak_lock/observe_only", self.observe_only.isChecked())
        s.setValue("peak_lock/auto_falc", self.auto_falc.isChecked())
        s.setValue(
            "peak_lock/parameters_visible",
            self.algorithm_settings_button.isChecked(),
        )
        for widget, key in (
            (self.min_prominence, "peak_lock/min_prominence"),
            (self.noise_sigma, "peak_lock/noise_sigma"),
            (self.dominance, "peak_lock/main_family_ratio"),
            (self.period_tolerance, "peak_lock/period_tolerance"),
            (self.narrow_main_height_ratio, "peak_lock/narrow_main_height_ratio"),
            (self.invalid_retry_windows, "peak_lock/invalid_retry_windows"),
            (self.offset_step, "peak_lock/wide_probe_step"),
            (self.search_frequency, "peak_lock/search_frequency_hz"),
            (self.initial_search_amplitude, "peak_lock/initial_search_amplitude"),
            (self.initial_offset_search_step, "peak_lock/initial_offset_search_step"),
            (self.min_offset_step, "peak_lock/final_fine_step"),
            (self.target_amplitude, "peak_lock/final_amplitude"),
            (self.final_coarse_step, "peak_lock/final_coarse_step"),
            (self.final_max_offset_deviation, "peak_lock/final_max_offset_deviation"),
            (self.search_tolerance, "peak_lock/wide_shrink_tolerance"),
            (self.model_corrections, "peak_lock/wide_model_corrections"),
            (self.search_windows, "peak_lock/wide_confirm_windows"),
            (self.balance_tolerance, "peak_lock/final_balance_tolerance"),
            (self.final_windows, "peak_lock/falc_confirm_windows"),
        ):
            s.setValue(key, widget.value())
        s.sync()

    def closeEvent(self, event):
        self.prepare_for_workspace_close()
        event.accept()

    def prepare_for_workspace_close(self):
        if self.controller.running:
            self.controller.stop("自动锁频窗口关闭")
        self._save_ui_settings()
