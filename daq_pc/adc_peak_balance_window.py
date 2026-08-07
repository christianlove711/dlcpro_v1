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
    "透射峰通道": (
        "选择自动锁频算法分析的当前逻辑ADC通道；它与通道A/B示波器显示一致。\n\n"
        "这里使用的是PL执行‘交换A/B’之后的通道：未勾选交换时，信号显示在哪个"
        "示波器就选哪个通道；勾选交换并重新启动采集后，A/B会随显示一起交换。\n\n"
        "可选值：通道 A、通道 B。默认：通道 A。"
    ),
    "峰极性": (
        "指定透射峰是向上、向下，或由算法自动判断。\n\n"
        "可选值：自动判断、正峰、负峰。默认：自动判断。"
    ),
    "最小峰高（ADC码）": (
        "峰相对局部基线至少要达到的原始ADC码突出度；低于该值的候选会被忽略。\n\n"
        "软件允许范围：0～32767 ADC码。默认：50 ADC码。"
    ),
    "噪声阈值倍数": (
        "动态峰门限中的噪声倍数。算法使用MAD估计背景噪声，并与最小峰高取较大值。\n\n"
        "软件允许范围：1.0～30.0。默认：6.0。"
    ),
    "00模/次峰最小强度比": (
        "00模峰族突出度与第二强峰族突出度的最小比值，用于防止误锁边带。\n\n"
        "软件允许范围：1.01～20.00。默认：2.00。"
    ),
    "方向试探步长": (
        "找到峰以后，它用于一次正向试探，以判断Offset增大后峰间隔是否改善；"
        "启动窗口完全没有透射峰时，也作为左右扩大Offset搜索的基础步长。\n\n"
        "软件允许范围：0.000001～1000000。默认：0.050000 V。\n"
        "实际可用范围仍受当前DLC pro配置限制。"
    ),
    "快速扫频频率": (
        "自动控制模式启动时写入的三角扫描频率。提高到10 Hz可显著缩短每个独立窗口的等待时间；"
        "观察模式不会自动写入。恢复启动参数时会恢复原频率。\n\n"
        "软件允许范围：0.01～1000 Hz。默认：10 Hz。"
    ),
    "初始化扫频范围": (
        "自动控制开始时首先写入的Scan Amplitude。若当前值不同，会先写入并校验读回，"
        "然后才开始寻找透射峰。默认：2.500000 Vpp。"
    ),
    "初始化无峰Offset步长": (
        "在初始化扫频范围内没有透射峰时，围绕初始化Offset按"
        "+步长、-步长、+2倍步长、-2倍步长依次搜索。默认：1.000000 V。"
    ),
    "Offset最小步长": (
        "Offset接近居中时允许算法使用的最小调节步长；反向或减半试探不会低于此值。\n\n"
        "使用PC Voltage扫描时单位为V。软件允许范围：0.000001～1000000，"
        "且不能大于方向试探步长。默认：0.001000 V。"
    ),
    "启动Offset最大偏移": (
        "自动运行期间Scan Offset相对启动值允许偏离的最大绝对量。\n\n"
        "软件允许范围：0.000001～1000000。默认：0.500000 V。\n"
        "实际可用范围仍受当前DLC pro配置限制。"
    ),
    "最终扫频范围目标": (
        "自动流程逐级缩小Scan Amplitude时的最终目标。算法不会缩到该值以下；"
        "达到目标并连续满足峰间隔标准后，才允许自动使能FALC pro。\n\n"
        "本功能强制要求Scan Output为PC Voltage，因此单位为Vpp。"
        "软件允许范围：0.000001～1000000。默认：0.200000 Vpp；"
        "目标不能大于启动Amplitude；快速寻峰通过后会直接写入该值。"
    ),
    "重捕获最大扩幅倍数": (
        "仅用于锁定后丢峰或窄扫失败时的恢复流程，限制恢复Amplitude的最大值。"
        "启动窗口没有透射峰时不会增大Amplitude，而是保持当前幅度并围绕启动Offset左右扩大搜索。\n\n"
        "软件允许范围：1.0～10.0倍。默认：2.0倍。"
    ),
    "最终允许不均匀度": (
        "上、下扫描两次穿越的间隔不均匀度目标；越小表示00模越接近扫描中心。\n\n"
        "软件允许范围：0.1%～25%。默认：5%。"
    ),
    "快速寻峰允许不均匀度": (
        "大扫理论预测后的粗居中门槛。达到后不再进行多级缩幅，而是直接进入0.200 Vpp。\n\n"
        "软件允许范围：0.1%～25%。默认：8%。"
    ),
    "理论预测增益": (
        "理论移动量为 prediction_gain × 0.5 × Amplitude × 不均匀度。\n\n"
        "软件允许范围：0.01～1.00。默认：0.80。"
    ),
    "模型最大修正次数": (
        "第一次理论跳转后允许继续按剩余误差直接修正的最多次数。正常流程不做无限迭代。\n\n"
        "软件允许范围：0～10。默认：2。"
    ),
    "最终邻域最大距离": (
        "0.200 Vpp最终阶段围绕当前Offset进行第一轮离散比较的最大距离。\n\n"
        "默认：0.009 V，即测试O±0.001…O±0.009；仍未达标时自动进入"
        "第二轮O±0.01…O±0.09 V搜索，Amplitude保持0.200 Vpp。"
    ),
    "快速确认窗口": (
        "大扫阶段达到8%门槛后，需要连续多少个独立窗口确认。默认：2。"
    ),
    "最终验收窗口": (
        "最终幅度达到5%门槛后，需要连续多少个独立窗口确认后才允许FALC接管。默认：3。"
    ),
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


class AdcPeakBalanceWindow(QMainWindow):
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
            self.resize(1180, 820)
            self.setMinimumSize(980, 700)
        self.setStyleSheet(PEAK_LOCK_STYLE)

        scroll = QScrollArea()
        scroll.setObjectName("peakLockScroll")
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded if embedded else Qt.ScrollBarAlwaysOff
        )
        self.setCentralWidget(scroll)

        root = QWidget()
        root.setObjectName("peakLockRoot")
        root.setMinimumHeight(1450)
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
        self.observe_only = VisibleCheckBox("仅观察算法判断（绝不写入DLC pro）")
        self.observe_only.setObjectName("observeOnly")
        self.observe_only.setChecked(True)
        self.observe_only.setToolTip(
            "勾选后只分析原始ADC码并显示判断结果，不修改Scan Offset或Scan Amplitude"
        )
        page.addWidget(title)
        page.addWidget(note)
        page.addWidget(self.observe_only)

        config = QFrame()
        config.setObjectName("card")
        grid = QGridLayout(config)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(18)
        left = QFormLayout()
        right = QFormLayout()
        left.setHorizontalSpacing(14)
        right.setHorizontalSpacing(14)
        left.setVerticalSpacing(10)
        right.setVerticalSpacing(10)
        self.parameter_info_buttons = {}
        self.channel = QComboBox()
        self.channel.addItem("通道 A（与A示波器一致）", "A")
        self.channel.addItem("通道 B（与B示波器一致）", "B")
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
        self.dominance.setValue(2.0)
        self.dominance.setDecimals(2)
        self._add_parameter_row(left, "透射峰通道", self.channel)
        self._add_parameter_row(left, "峰极性", self.polarity)
        self._add_parameter_row(left, "最小峰高（ADC码）", self.min_prominence)
        self._add_parameter_row(left, "噪声阈值倍数", self.noise_sigma)
        self._add_parameter_row(left, "00模/次峰最小强度比", self.dominance)

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
        self.offset_range = ParameterDoubleSpinBox()
        self.offset_range.setRange(0.000001, 1_000_000.0)
        self.offset_range.setDecimals(6)
        self.offset_range.setValue(0.5)
        self.target_amplitude = ParameterDoubleSpinBox()
        self.target_amplitude.setRange(0.000001, 1_000_000.0)
        self.target_amplitude.setDecimals(6)
        self.target_amplitude.setValue(0.2)
        self.max_search_factor = ParameterDoubleSpinBox()
        self.max_search_factor.setRange(1.0, 10.0)
        self.max_search_factor.setDecimals(2)
        self.max_search_factor.setValue(2.0)
        self.search_tolerance = ParameterDoubleSpinBox()
        self.search_tolerance.setRange(0.1, 25.0)
        self.search_tolerance.setValue(8.0)
        self.search_tolerance.setSuffix(" %")
        self.prediction_gain = ParameterDoubleSpinBox()
        self.prediction_gain.setRange(0.01, 1.0)
        self.prediction_gain.setDecimals(2)
        self.prediction_gain.setValue(0.8)
        self.model_corrections = ParameterSpinBox()
        self.model_corrections.setRange(0, 10)
        self.model_corrections.setValue(2)
        self.final_local_distance = ParameterDoubleSpinBox()
        self.final_local_distance.setRange(0.001, 1_000_000.0)
        self.final_local_distance.setDecimals(6)
        self.final_local_distance.setValue(0.009)
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
        self._add_parameter_row(left, "方向试探步长", self.offset_step)
        self._add_parameter_row(left, "快速扫频频率", self.search_frequency)
        self._add_parameter_row(left, "初始化扫频范围", self.initial_search_amplitude)
        self._add_parameter_row(left, "初始化无峰Offset步长", self.initial_offset_search_step)
        self._add_parameter_row(left, "快速寻峰允许不均匀度", self.search_tolerance)
        self._add_parameter_row(left, "理论预测增益", self.prediction_gain)
        self._add_parameter_row(left, "快速确认窗口", self.search_windows)
        self._add_parameter_row(right, "Offset最小步长", self.min_offset_step)
        self._add_parameter_row(right, "启动Offset最大偏移", self.offset_range)
        self._add_parameter_row(right, "最终扫频范围目标", self.target_amplitude)
        self._add_parameter_row(right, "重捕获最大扩幅倍数", self.max_search_factor)
        self._add_parameter_row(right, "模型最大修正次数", self.model_corrections)
        self._add_parameter_row(right, "最终邻域最大距离", self.final_local_distance)
        self._add_parameter_row(right, "最终允许不均匀度", self.balance_tolerance)
        self._add_parameter_row(right, "最终验收窗口", self.final_windows)
        grid.addLayout(left, 0, 0)
        grid.addLayout(right, 0, 1)
        config.setMinimumHeight(500)
        page.addWidget(config)

        strategy = QFrame()
        strategy.setObjectName("card")
        strategy_box = QVBoxLayout(strategy)
        strategy_box.setContentsMargins(16, 14, 16, 14)
        strategy_title = QLabel("两级自动居中策略（PC Voltage）")
        strategy_title.setStyleSheet("font-weight:700; font-size:15px;")
        strategy_box.addWidget(strategy_title)
        strategy_note = QLabel(
            "自动模式先写入初始化Amplitude；无峰时以初始化步长左右搜索Offset。"
            "找到峰后使用三角波峰间隔计算理论中心，只做一次方向试探；"
            "通过后一步缩到最终幅度，先以0.001 V离散邻域精调；"
            "按±0.001至±0.009 V搜索；仍无效时保持最终幅度，"
            "再按±0.01至±0.09 V搜索。"
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
            ("最终锁定", "0.200 Vpp", "5%", "±0.001…0.009 → ±0.01…0.09 V", "3"),
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
            self.final_local_distance, self.search_windows,
            self.final_windows,
        ):
            control.valueChanged.connect(self._update_strategy_summary)
        self._update_strategy_summary()
        strategy_box.addLayout(stage_grid)
        page.addWidget(strategy)

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
            ("peaks", "00模/次峰/强度比/SNR"),
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
        self.save_button = QPushButton("保存参数")
        self.save_button.setObjectName("save")
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
        controls.addWidget(self.save_button)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.restore_button)
        controls.addStretch(1)
        controls.addWidget(self.falc_button)
        page.addLayout(controls)
        falc_options = QHBoxLayout()
        falc_options.addWidget(self.auto_falc)
        falc_options.addStretch(1)
        page.addLayout(falc_options)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(130)
        page.addWidget(self.log, 1)

        self.save_button.clicked.connect(self._save_parameters)
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
            f"±{self.min_offset_step.value():.3f} V网格，"
            f"范围±{self.final_local_distance.value():.3f} V；"
            "无效后±0.010…0.090 V"
        )
        labels[(2, 4)].setText(str(self.final_windows.value()))

    def _add_parameter_row(self, form: QFormLayout, title: str,
                           control: QWidget) -> None:
        field = QWidget()
        field.setObjectName("parameterField")
        field.setAttribute(Qt.WA_StyledBackground, True)
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
        QMessageBox.information(
            self, f"参数说明：{title}", PARAMETER_HELP[title]
        )

    def _numeric_parameter_widgets(self):
        return (
            self.min_prominence, self.noise_sigma, self.dominance,
            self.offset_step, self.search_frequency,
            self.initial_search_amplitude, self.initial_offset_search_step,
            self.min_offset_step, self.offset_range,
            self.target_amplitude, self.max_search_factor,
            self.search_tolerance, self.prediction_gain,
            self.model_corrections, self.final_local_distance,
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
            carrier_dominance_ratio=float(self.dominance.value()),
            offset_step=float(self.offset_step.value()),
            min_offset_step=float(self.min_offset_step.value()),
            max_offset_deviation=float(self.offset_range.value()),
            target_amplitude=float(self.target_amplitude.value()),
            max_search_amplitude_factor=float(self.max_search_factor.value()),
            balance_tolerance=float(self.balance_tolerance.value()) / 100.0,
            stable_windows=int(self.final_windows.value()),
            search_tolerance=float(self.search_tolerance.value()) / 100.0,
            search_windows=int(self.search_windows.value()),
            prediction_gain=float(self.prediction_gain.value()),
            max_model_corrections=int(self.model_corrections.value()),
            final_local_max_distance=float(self.final_local_distance.value()),
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
            self.search_frequency,
            self.initial_search_amplitude, self.initial_offset_search_step,
            self.min_offset_step, self.offset_range,
            self.target_amplitude, self.max_search_factor,
            self.search_tolerance, self.prediction_gain,
            self.model_corrections, self.final_local_distance,
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
            "probe": "试探Offset方向", "center": "居中Offset",
            "search_direction_probe": "快速寻峰·方向试探",
            "search_verify": "快速寻峰·理论跳转验证",
            "search_model_correct": "快速寻峰·模型残差修正",
            "search_accept": "快速寻峰·粗居中确认",
            "final_shrink": "一步缩到最终幅度",
            "final_verify": "最终幅度初次验证",
            "final_local_search": "0.001 V邻域搜索",
            "final_local_return": "恢复邻域最佳Offset",
            "startup_offset_search": "启动Offset左右扩展寻峰",
            "final_accept": "最终连续窗口验收",
            "legacy_restore": "恢复大扫幅并进入旧搜索",
            "verify_shrink": "验证缩幅", "local_recover": "小范围左右找峰",
            "restore_amplitude": "恢复扫频范围", "refine": "二分最小可靠幅度",
            "track": "均衡保持与漂移跟踪", "ambiguous": "00模候选不唯一",
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
        shrink = data.get("stage_shrink")
        shrink_text = "不再缩幅" if shrink is None else f"×{float(shrink):.2f}"
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
            self.log.append(f"建议：{advice}")
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
        numeric = (
            (self.min_prominence, "peak_lock/min_prominence", 50),
            (self.noise_sigma, "peak_lock/noise_sigma", 6.0),
            (self.dominance, "peak_lock/dominance", 2.0),
            (self.offset_step, "peak_lock/direction_probe_step", 0.05),
            (self.search_frequency, "peak_lock/search_frequency_hz", 10.0),
            (self.initial_search_amplitude, "peak_lock/initial_search_amplitude", 2.5),
            (self.initial_offset_search_step, "peak_lock/initial_offset_search_step", 1.0),
            (self.min_offset_step, "peak_lock/min_offset_step", 0.001),
            (self.offset_range, "peak_lock/max_start_offset_deviation", 0.5),
            (self.target_amplitude, "peak_lock/target_amplitude", 0.2),
            (self.max_search_factor, "peak_lock/max_search_factor", 2.0),
            (self.search_tolerance, "peak_lock/search_tolerance", 8.0),
            (self.prediction_gain, "peak_lock/prediction_gain", 0.8),
            (self.model_corrections, "peak_lock/model_corrections", 2),
            # v2 deliberately ignores the former ±0.005 V persisted default;
            # the current algorithm always starts with ±0.001..±0.009 V.
            (self.final_local_distance, "peak_lock/final_local_distance_v2", 0.009),
            (self.search_windows, "peak_lock/search_windows", 2),
            (self.balance_tolerance, "peak_lock/final_tolerance", 5.0),
            (self.final_windows, "peak_lock/final_windows", 3),
        )
        for widget, key, default in numeric:
            widget.setValue(float(s.value(key, default)))

    def _save_ui_settings(self):
        s = self.settings_store
        s.setValue("peak_lock/channel", self.channel.currentData())
        s.setValue("peak_lock/polarity", self.polarity.currentData())
        s.setValue("peak_lock/observe_only", self.observe_only.isChecked())
        s.setValue("peak_lock/auto_falc", self.auto_falc.isChecked())
        for widget, key in (
            (self.min_prominence, "peak_lock/min_prominence"),
            (self.noise_sigma, "peak_lock/noise_sigma"),
            (self.dominance, "peak_lock/dominance"),
            (self.offset_step, "peak_lock/direction_probe_step"),
            (self.search_frequency, "peak_lock/search_frequency_hz"),
            (self.initial_search_amplitude, "peak_lock/initial_search_amplitude"),
            (self.initial_offset_search_step, "peak_lock/initial_offset_search_step"),
            (self.min_offset_step, "peak_lock/min_offset_step"),
            (self.offset_range, "peak_lock/max_start_offset_deviation"),
            (self.target_amplitude, "peak_lock/target_amplitude"),
            (self.max_search_factor, "peak_lock/max_search_factor"),
            (self.search_tolerance, "peak_lock/search_tolerance"),
            (self.prediction_gain, "peak_lock/prediction_gain"),
            (self.model_corrections, "peak_lock/model_corrections"),
            (self.final_local_distance, "peak_lock/final_local_distance_v2"),
            (self.search_windows, "peak_lock/search_windows"),
            (self.balance_tolerance, "peak_lock/final_tolerance"),
            (self.final_windows, "peak_lock/final_windows"),
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
