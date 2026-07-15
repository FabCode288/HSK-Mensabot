#!/usr/bin/env python3

import math
import sys
import time
from collections import deque
from dataclasses import dataclass

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from nav2_msgs.msg import SpeedLimit
from sensor_msgs.msg import Imu
from std_msgs.msg import Bool, String
from action_msgs.msg import GoalStatusArray
from sick_safetyscanners2_interfaces.msg import OutputPaths

from PyQt6.QtCore import QObject, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QVBoxLayout, QWidget, QCheckBox, QPushButton, QComboBox,
)

import pyqtgraph as pg


# ============================================================
# GUI HELPERS
# ============================================================

GREEN = "#1f8f4e"
RED = "#c0392b"
ORANGE = "#d68910"
BLUE = "#2874a6"
DARK = "#20252b"
CARD = "#2b3138"
TEXT = "#f2f3f4"
MUTED = "#aeb6bf"


def yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class ValueCard(QFrame):
    def __init__(self, title, value="--", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.value = QLabel(value)
        self.value.setObjectName("cardValue")
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addWidget(self.value, 1)

    def set_value(self, text):
        self.value.setText(str(text))


class BoolCard(ValueCard):
    def __init__(self, title, true_text="AKTIV", false_text="INAKTIV", invert_good=False):
        super().__init__(title)
        self.true_text = true_text
        self.false_text = false_text
        self.invert_good = invert_good
        self.set_state(None)

    def set_state(self, state):
        if state is None:
            self.value.setText("--")
            self.setStyleSheet("QFrame#card { background: #566573; border-radius: 10px; }")
            return

        good = (not state) if self.invert_good else bool(state)
        color = GREEN if good else RED
        self.value.setText(self.true_text if state else self.false_text)
        self.setStyleSheet(
            f"QFrame#card {{ background: {color}; border-radius: 10px; }}"
            "QLabel { color: white; background: transparent; }"
        )


class StateCard(ValueCard):
    def set_state(self, text, color=BLUE):
        self.value.setText(text)
        self.setStyleSheet(
            f"QFrame#card {{ background: {color}; border-radius: 10px; }}"
            "QLabel { color: white; background: transparent; }"
        )


class RosWorker(QObject):
    data_changed = pyqtSignal(dict)
    ros_error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True
        self.node = None
        self.executor = None

    def run(self):
        try:
            rclpy.init(args=None)
            self.node = MonitorNode(self.data_changed)
            self.executor = SingleThreadedExecutor()
            self.executor.add_node(self.node)

            while self.running and rclpy.ok():
                self.executor.spin_once(timeout_sec=0.05)

        except Exception as exc:
            self.ros_error.emit(str(exc))
        finally:
            if self.executor and self.node:
                self.executor.remove_node(self.node)
            if self.node:
                self.node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
            self.finished.emit()

    def stop(self):
        self.running = False


class MonitorNode(Node):
    def __init__(self, signal):
        super().__init__("mensabot_gui_monitor")
        self.signal = signal
        self.last_seen = {}

        self.create_subscription(Odometry, "/odom", self.odom_cb, 10)
        self.create_subscription(Twist, "/cmd_vel_smoothed", lambda m: self.twist_cb("cmd_vel", m), 10)
        self.create_subscription(Twist, "/safety/cmd_vel", lambda m: self.twist_cb("safety_cmd", m), 10)
        self.create_subscription(
            TwistStamped,
            "/mensabot_base_controller/cmd_vel_out",
            lambda m: self.twist_cb("controller_cmd", m.twist),
            10,
        )

        self.create_subscription(Bool, "/safety/manual_override", lambda m: self.bool_cb("manual_override", m), 10)
        self.create_subscription(Bool, "/safety/estop", lambda m: self.bool_cb("estop", m), 10)
        self.create_subscription(Bool, "/hardware/connected", lambda m: self.bool_cb("hardware_connected", m), 10)
        self.create_subscription(String, "/safety/field_state", self.field_cb, 10)
        self.create_subscription(SpeedLimit, "/speed_limit", self.speed_limit_cb, 10)

        self.create_subscription(
            OutputPaths, "/lidars/front/output_paths",
            lambda m: self.scanner_cb("front", m), 10
        )
        self.create_subscription(
            OutputPaths, "/lidars/rear/output_paths",
            lambda m: self.scanner_cb("rear", m), 10
        )

        self.create_subscription(GoalStatusArray, "/navigate_to_pose/_action/status", self.goal_cb, 10)
        self.create_subscription(Imu, "/imu/data", self.imu_cb, 10)

        self.create_timer(0.25, self.watchdog_cb)

    def mark(self, topic_key):
        self.last_seen[topic_key] = time.monotonic()

    def emit(self, **kwargs):
        self.signal.emit(kwargs)

    def bool_cb(self, key, msg):
        self.mark(key)
        self.emit(**{key: bool(msg.data)})

    def twist_cb(self, key, msg):
        self.mark(key)
        self.emit(**{
            key: {
                "linear": float(msg.linear.x),
                "angular": float(msg.angular.z),
            }
        })

    def odom_cb(self, msg):
        self.mark("odom")
        q = msg.pose.pose.orientation
        self.emit(odom={
            "x": float(msg.pose.pose.position.x),
            "y": float(msg.pose.pose.position.y),
            "yaw": math.degrees(yaw_from_quaternion(q)),
            "linear": float(msg.twist.twist.linear.x),
            "angular": float(msg.twist.twist.angular.z),
        })

    def field_cb(self, msg):
        self.mark("field_state")
        self.emit(field_state=msg.data)

    def speed_limit_cb(self, msg):
        self.mark("speed_limit")
        self.emit(speed_limit=float(msg.speed_limit))

    def scanner_cb(self, side, msg):
        self.mark(f"{side}_scanner")
        protective_safe = len(msg.status) > 0 and bool(msg.status[0])
        warning_safe = len(msg.status) > 1 and bool(msg.status[1])
        self.emit(**{
            f"{side}_scanner": {
                "protective_safe": protective_safe,
                "warning_safe": warning_safe,
                "monitoring_case": int(msg.active_monitoring_case),
            }
        })

    def goal_cb(self, msg):
        self.mark("goal_status")
        if not msg.status_list:
            self.emit(goal_state=("IDLE","#566573")); return
        s=msg.status_list[-1].status
        m={1:("GOAL ACCEPTED","#5dade2"),2:("DRIVING TO GOAL","#2874a6"),3:("GOAL CANCELING","#d68910"),4:("GOAL SUCCEEDED","#1f8f4e"),5:("GOAL CANCELED","#d68910"),6:("GOAL ABORTED","#c0392b")}
        self.emit(goal_state=m.get(s,("UNKNOWN","#566573")))

    def imu_cb(self, msg):
        self.mark("imu")
        yaw = math.degrees(yaw_from_quaternion(msg.orientation))
        self.emit(imu={
            "yaw": yaw,
            "yaw_rate": float(msg.angular_velocity.z),
        })

    def watchdog_cb(self):
        now = time.monotonic()
        ages = {}
        keys = [
            "odom", "cmd_vel", "safety_cmd", "controller_cmd",
            "manual_override", "estop", "hardware_connected",
            "field_state", "speed_limit", "front_scanner",
            "rear_scanner", "imu"
        ]
        for key in keys:
            ages[key] = None if key not in self.last_seen else now - self.last_seen[key]
        self.emit(topic_ages=ages)


# ============================================================
# MAIN WINDOW
# ============================================================

class MensabotMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mensabot Monitor")
        self.resize(1500, 950)
        self.setMinimumSize(900, 650)

        self.data = {}
        self.start_time = time.monotonic()
        self.history_t = deque(maxlen=600)
        self.history_cmd = deque(maxlen=600)
        self.history_ctrl = deque(maxlen=600)
        self.history_odom = deque(maxlen=600)
        self.history_w_cmd = deque(maxlen=600)
        self.history_w_ctrl = deque(maxlen=600)
        self.history_w_odom = deque(maxlen=600)

        # Plotsteuerung
        self.auto_follow = True
        self.time_window = 20.0

        self.build_ui()
        self.apply_style()
        self.start_ros()

        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(100)

    def build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        root = QWidget()
        scroll.setWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("MENSABOT MONITOR")
        title.setObjectName("mainTitle")
        self.overall_state = StateCard("GESAMTZUSTAND")
        self.goal_state = StateCard("NAV2 GOAL")
        self.goal_state.set_state("IDLE", "#566573")
        self.hardware = BoolCard("MOTORANSTEUERUNG", "VERBUNDEN", "GETRENNT")
        header.addWidget(title, 2)
        header.addWidget(self.overall_state, 2)
        header.addWidget(self.goal_state, 2)
        header.addWidget(self.hardware, 1)
        main.addLayout(header)

        # Top information grid
        top = QGridLayout()
        top.setSpacing(10)

        self.pose = ValueCard("POSE", "x: -- m\ny: -- m\nyaw: -- °")
        self.motion = StateCard("FAHRZUSTAND")
        self.field = StateCard("AKTIVES SCHUTZFELD")
        self.field_match = BoolCard("FELD / BEWEGUNG", "PLAUSIBEL", "FEHLER")
        self.manual_override = BoolCard("MANUAL OVERRIDE", "AKTIV", "INAKTIV", invert_good=True)
        self.estop = BoolCard("E-STOP", "AKTIV", "INAKTIV", invert_good=True)
        self.speed_limit = ValueCard("SPEED LIMIT", "-- %")
        self.imu = ValueCard("IMU", "Yaw: -- °\nYaw Rate: -- rad/s")

        cards = [
            self.pose, self.motion, self.field, self.field_match,
            self.manual_override, self.estop, self.speed_limit, self.imu
        ]
        for i, card in enumerate(cards):
            top.addWidget(card, i // 4, i % 4)

        main.addLayout(top)

        # Velocity chain
        chain_group = QGroupBox("GESCHWINDIGKEITSKETTE")
        chain_layout = QGridLayout(chain_group)
        self.cmd_card = ValueCard("NAV2 MPPI_OUT: /cmd_vel_nav")
        self.safety_cmd_card = ValueCard("SAFETY OUTPUT: /safety/cmd_vel")
        self.controller_cmd_card = ValueCard("CONTROLLER OUT: /.../cmd_vel_out")
        self.odom_card = ValueCard("EKF Geschwindigkeit")
        for i, c in enumerate([
            self.cmd_card, self.safety_cmd_card,
            self.controller_cmd_card, self.odom_card
        ]):
            chain_layout.addWidget(c, 0, i)
        main.addWidget(chain_group)

        # Safety
        safety_group = QGroupBox("SICHERHEITSSYSTEM")
        safety = QGridLayout(safety_group)

        self.front_warning = BoolCard("FRONT WARNFELD", "FREI", "AUSGELÖST")
        self.front_protect = BoolCard("FRONT SCHUTZFELD", "FREI", "AUSGELÖST")
        self.front_data = BoolCard("FRONT DATEN", "OK", "TIMEOUT")

        self.rear_warning = BoolCard("HECK WARNFELD", "FREI", "AUSGELÖST")
        self.rear_protect = BoolCard("HECK SCHUTZFELD", "FREI", "AUSGELÖST")
        self.rear_data = BoolCard("HECK DATEN", "OK", "TIMEOUT")

        safety_cards = [
            self.front_warning, self.front_protect, self.front_data,
            self.rear_warning, self.rear_protect, self.rear_data
        ]
        for i, c in enumerate(safety_cards):
            safety.addWidget(c, i // 3, i % 3)
        main.addWidget(safety_group)

        # Plots
        plot_group = QGroupBox("LIVE-VERLÄUFE")
        plot_layout = QVBoxLayout(plot_group)

        # ---------------------------------------------------------
        # Werkzeugleiste für die Diagramme
        # ---------------------------------------------------------

        toolbar = QHBoxLayout()

        self.auto_follow_checkbox = QCheckBox("Auto Follow")
        self.auto_follow_checkbox.setChecked(True)
        self.auto_follow_checkbox.toggled.connect(self.toggle_auto_follow)

        toolbar.addWidget(self.auto_follow_checkbox)

        self.center_button = QPushButton("Zentrieren")
        self.center_button.clicked.connect(self.center_plots)

        toolbar.addWidget(self.center_button)

        toolbar.addSpacing(20)

        toolbar.addWidget(QLabel("Zeitfenster"))

        self.time_window_box = QComboBox()
        self.time_window_box.addItems(["10", "20", "30", "60", "120"])
        self.time_window_box.setCurrentText("20")
        self.time_window_box.currentTextChanged.connect(self.change_time_window)

        toolbar.addWidget(self.time_window_box)

        toolbar.addStretch()

        plot_layout.addLayout(toolbar)

        self.linear_plot = pg.PlotWidget(title="Lineargeschwindigkeit")
        self.linear_plot.setLabel("left", "v", units="m/s")
        self.linear_plot.setLabel("bottom", "Zeit", units="s")
        self.linear_plot.showGrid(x=True, y=True, alpha=0.25)
        self.linear_plot.addLegend(
            offset=(10, 10),
            brush=pg.mkBrush(40, 40, 40, 220)
        )
        self.lin_cmd_curve = self.linear_plot.plot(
            name="Nav2 /cmd_vel",
            pen=pg.mkPen("#3498db", width=3)
        )
        self.lin_ctrl_curve = self.linear_plot.plot(
            name="Controller Output",
            pen=pg.mkPen("#f39c12", width=3, style=Qt.PenStyle.DashLine)
        )
        self.lin_odom_curve = self.linear_plot.plot(
            name="EKF Geschwindigkeit",
            pen=pg.mkPen("#2ecc71", width=3, style=Qt.PenStyle.DotLine)
        )

        self.angular_plot = pg.PlotWidget(title="Winkelgeschwindigkeit")
        self.angular_plot.setLabel("left", "ω", units="rad/s")
        self.angular_plot.setLabel("bottom", "Zeit", units="s")
        self.angular_plot.showGrid(x=True, y=True, alpha=0.25)
        self.angular_plot.addLegend(
            offset=(10, 10),
            brush=pg.mkBrush(40, 40, 40, 220)
        )
        self.ang_cmd_curve = self.angular_plot.plot(
            name="Nav2 /cmd_vel",
            pen=pg.mkPen("#3498db", width=3)
        )
        self.ang_ctrl_curve = self.angular_plot.plot(
            name="Controller Output",
            pen=pg.mkPen("#f39c12", width=3, style=Qt.PenStyle.DashLine)
        )
        self.ang_odom_curve = self.angular_plot.plot(
            name="EKF Winkelgeschwindigkeit",
            pen=pg.mkPen("#2ecc71", width=3, style=Qt.PenStyle.DotLine)
        )
        
        # Benutzer hat den Plot verändert
        self.linear_plot.getViewBox().sigRangeChangedManually.connect(
            self.user_changed_plot
        )

        self.angular_plot.getViewBox().sigRangeChangedManually.connect(
            self.user_changed_plot
        )

        plot_layout.addWidget(self.linear_plot)
        plot_layout.addWidget(self.angular_plot)
        main.addWidget(plot_group, 2)

        # Watchdog
        watchdog_group = QGroupBox("TOPIC WATCHDOG")
        watchdog_layout = QGridLayout(watchdog_group)
        self.watchdog_labels = {}
        watchdog_names = {
            "odom": "/odom",
            "cmd_vel": "/cmd_vel",
            "safety_cmd": "/safety/cmd_vel",
            "controller_cmd": "/mensabot_base_controller/cmd_vel_out",
            "manual_override": "/safety/manual_override",
            "estop": "/safety/estop",
            "hardware_connected": "/hardware/connected",
            "field_state": "/safety/field_state",
            "speed_limit": "/speed_limit",
            "front_scanner": "/lidars/front/output_paths",
            "rear_scanner": "/lidars/rear/output_paths",
            "imu": "/imu/data",
        }
        for i, (key, name) in enumerate(watchdog_names.items()):
            label = QLabel(f"{name}: --")
            label.setObjectName("watchdog")
            self.watchdog_labels[key] = label
            watchdog_layout.addWidget(label, i // 3, i % 3)

        main.addWidget(watchdog_group)

    def apply_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {DARK};
                color: {TEXT};
                font-size: 14px;
            }}
            QScrollArea {{
                border: none;
            }}
            QLabel#mainTitle {{
                font-size: 28px;
                font-weight: 800;
                padding: 12px;
            }}
            QGroupBox {{
                font-size: 16px;
                font-weight: 700;
                border: 1px solid #4d5656;
                border-radius: 10px;
                margin-top: 14px;
                padding-top: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
            QFrame#card {{
                background: {CARD};
                border-radius: 10px;
                min-height: 78px;
            }}
            QLabel#cardTitle {{
                color: {TEXT};
                font-size: 12px;
                font-weight: 700;
                padding-top: 6px;
            }}
            QLabel#cardValue {{
                color: white;
                font-size: 19px;
                font-weight: 800;
                padding: 6px;
            }}
            QLabel#watchdog {{
                background: {CARD};
                border-radius: 6px;
                padding: 8px;
                font-family: monospace;
            }}
            QScrollBar:vertical {{
                background: #303841;
                width: 18px;
                margin: 0px;
                border-radius: 8px;
            }}

            QScrollBar::handle:vertical {{
                background: #4fa3ff;
                min-height: 40px;
                border-radius: 8px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: #6bb8ff;
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            QScrollBar:horizontal {{
                background: #303841;
                height: 18px;
                margin: 0px;
                border-radius: 8px;
            }}

            QScrollBar::handle:horizontal {{
                background: #4fa3ff;
                min-width: 40px;
                border-radius: 8px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background: #6bb8ff;
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
        """)

    def start_ros(self):
        self.ros_thread = QThread(self)
        self.ros_worker = RosWorker()
        self.ros_worker.moveToThread(self.ros_thread)
        self.ros_thread.started.connect(self.ros_worker.run)
        self.ros_worker.data_changed.connect(self.on_data)
        self.ros_worker.ros_error.connect(self.on_ros_error)
        self.ros_worker.finished.connect(self.ros_thread.quit)
        self.ros_thread.start()

    def on_ros_error(self, text):
        self.overall_state.set_state("ROS FEHLER", RED)
        self.statusBar().showMessage(text)

    def on_data(self, update):
        self.data.update(update)

        if "hardware_connected" in update:
            self.hardware.set_state(update["hardware_connected"])

        if "goal_state" in update:
            st,col=update["goal_state"]
            self.goal_state.set_state(st,col)

        if "manual_override" in update:
            self.manual_override.set_state(update["manual_override"])

        if "estop" in update:
            self.estop.set_state(update["estop"])

        if "speed_limit" in update:
            self.speed_limit.set_value(f'{update["speed_limit"]:.0f} %')

        if "field_state" in update:
            state = update["field_state"]
            color = ORANGE if state == "MANUAL_OVERRIDE" else BLUE
            self.field.set_state(state, color)

        if "odom" in update:
            o = update["odom"]
            self.pose.set_value(f'x: {o["x"]:.2f} m\ny: {o["y"]:.2f} m\nyaw: {o["yaw"]:.1f} °')
            self.odom_card.set_value(f'v: {o["linear"]:+.3f} m/s\nω: {o["angular"]:+.3f} rad/s')

        if "imu" in update:
            i = update["imu"]
            self.imu.set_value(f'Yaw: {i["yaw"]:.1f} °\nYaw Rate: {i["yaw_rate"]:+.3f} rad/s')

        if "cmd_vel" in update:
            self.set_twist_card(self.cmd_card, update["cmd_vel"])
        if "safety_cmd" in update:
            self.set_twist_card(self.safety_cmd_card, update["safety_cmd"])
        if "controller_cmd" in update:
            self.set_twist_card(self.controller_cmd_card, update["controller_cmd"])

        if "front_scanner" in update:
            s = update["front_scanner"]
            self.front_warning.set_state(s["warning_safe"])
            self.front_protect.set_state(s["protective_safe"])

        if "rear_scanner" in update:
            s = update["rear_scanner"]
            self.rear_warning.set_state(s["warning_safe"])
            self.rear_protect.set_state(s["protective_safe"])

        if "topic_ages" in update:
            self.update_watchdog(update["topic_ages"])

        self.update_motion_state()
        self.update_field_match()
        self.update_overall_state()

    def set_twist_card(self, card, value):
        card.set_value(f'v: {value["linear"]:+.3f} m/s\nω: {value["angular"]:+.3f} rad/s')

    def derive_motion(self):
        v = self.data.get("controller_cmd", {}).get("linear", 0.0)
        w = self.data.get("controller_cmd", {}).get("angular", 0.0)
        lin_th = 0.02
        ang_th = 0.05

        if abs(v) < lin_th and abs(w) < ang_th:
            return "STILLSTAND"
        if v > lin_th and abs(w) < ang_th:
            return "VORWÄRTS"
        if v < -lin_th and abs(w) < ang_th:
            return "RÜCKWÄRTS"
        if abs(v) < lin_th and w > ang_th:
            return "DREHUNG LINKS"
        if abs(v) < lin_th and w < -ang_th:
            return "DREHUNG RECHTS"
        return "KURVENFAHRT VORWÄRTS" if v > 0 else "KURVENFAHRT RÜCKWÄRTS"

    def update_motion_state(self):
        self.motion.set_state(self.derive_motion(), BLUE)

    def update_field_match(self):
        field = self.data.get("field_state")
        if field is None:
            self.field_match.set_state(None)
            return

        if self.data.get("manual_override", False):
            self.field_match.set_state(True)
            return

        motion = self.derive_motion()
        expected = {
            "STILLSTAND": "STOP",
            "VORWÄRTS": "FORWARD",
            "RÜCKWÄRTS": "BACKWARD",
            "DREHUNG LINKS": "ROTATE_LEFT",
            "DREHUNG RECHTS": "ROTATE_RIGHT",
            "KURVENFAHRT VORWÄRTS": "FORWARD",
            "KURVENFAHRT RÜCKWÄRTS": "BACKWARD",
        }.get(motion)

        self.field_match.set_state(field == expected)

    def update_overall_state(self):
        if self.data.get("estop", False):
            self.overall_state.set_state("E-STOP AKTIV", RED)
        elif self.data.get("hardware_connected") is False:
            self.overall_state.set_state("HARDWARE GETRENNT", RED)
        elif self.data.get("manual_override", False):
            self.overall_state.set_state("MANUAL OVERRIDE", ORANGE)
        elif self.any_protective_triggered():
            self.overall_state.set_state("SCHUTZFELD AKTIV", RED)
        elif self.any_warning_triggered():
            self.overall_state.set_state("WARNFELD AKTIV", ORANGE)
        else:
            self.overall_state.set_state("BETRIEBSBEREIT", GREEN)

    def any_protective_triggered(self):
        for side in ("front_scanner", "rear_scanner"):
            if side in self.data and not self.data[side]["protective_safe"]:
                return True
        return False

    def any_warning_triggered(self):
        for side in ("front_scanner", "rear_scanner"):
            if side in self.data and not self.data[side]["warning_safe"]:
                return True
        return False

    def update_watchdog(self, ages):
        for key, age in ages.items():
            if key not in self.watchdog_labels:
                continue

            label = self.watchdog_labels[key]
            if age is None:
                text = "NO DATA"
                color = RED
            elif age < 1.0:
                text = f"{age:.2f} s"
                color = GREEN
            elif age < 2.0:
                text = f"{age:.2f} s"
                color = ORANGE
            else:
                text = f"{age:.2f} s TIMEOUT"
                color = RED

            topic = label.text().split(":")[0]
            label.setText(f"{topic}: {text}")
            label.setStyleSheet(
                f"background: {color}; border-radius: 6px; padding: 8px; color: white;"
            )

        front_age = ages.get("front_scanner")
        rear_age = ages.get("rear_scanner")
        self.front_data.set_state(front_age is not None and front_age < 1.0)
        self.rear_data.set_state(rear_age is not None and rear_age < 1.0)

    def update_plots(self):
        t = time.monotonic() - self.start_time

        cmd = self.data.get("cmd_vel", {"linear": 0.0, "angular": 0.0})
        ctrl = self.data.get("controller_cmd", {"linear": 0.0, "angular": 0.0})
        odom = self.data.get("odom", {"linear": 0.0, "angular": 0.0})

        self.history_t.append(t)
        self.history_cmd.append(cmd["linear"])
        self.history_ctrl.append(ctrl["linear"])
        self.history_odom.append(odom["linear"])

        self.history_w_cmd.append(cmd["angular"])
        self.history_w_ctrl.append(ctrl["angular"])
        self.history_w_odom.append(odom["angular"])

        x = list(self.history_t)
        self.lin_cmd_curve.setData(x, list(self.history_cmd))
        self.lin_ctrl_curve.setData(x, list(self.history_ctrl))
        self.lin_odom_curve.setData(x, list(self.history_odom))

        self.ang_cmd_curve.setData(x, list(self.history_w_cmd))
        self.ang_ctrl_curve.setData(x, list(self.history_w_ctrl))
        self.ang_odom_curve.setData(x, list(self.history_w_odom))

        # ---------------------------------------------------------
        # Auto Follow
        # ---------------------------------------------------------

        if self.auto_follow and len(x) > 2:

            xmax = x[-1]
            xmin = max(0.0, xmax - self.time_window)

            self.linear_plot.setXRange(xmin, xmax, padding=0)
            self.angular_plot.setXRange(xmin, xmax, padding=0)

            # Nur Werte innerhalb des sichtbaren Fensters betrachten
            visible = [i for i, t in enumerate(x) if t >= xmin]

            if visible:

                lin_values = (
                    [self.history_cmd[i] for i in visible] +
                    [self.history_ctrl[i] for i in visible] +
                    [self.history_odom[i] for i in visible]
                )

                ang_values = (
                    [self.history_w_cmd[i] for i in visible] +
                    [self.history_w_ctrl[i] for i in visible] +
                    [self.history_w_odom[i] for i in visible]
                )

                if lin_values:
                    ymin = min(lin_values)
                    ymax = max(lin_values)

                    if abs(ymax - ymin) < 0.05:
                        ymin -= 0.05
                        ymax += 0.05

                    margin = (ymax - ymin) * 0.10

                    self.linear_plot.setYRange(
                        ymin - margin,
                        ymax + margin,
                        padding=0
                    )

                if ang_values:
                    ymin = min(ang_values)
                    ymax = max(ang_values)

                    if abs(ymax - ymin) < 0.05:
                        ymin -= 0.05
                        ymax += 0.05

                    margin = (ymax - ymin) * 0.10

                    self.angular_plot.setYRange(
                        ymin - margin,
                        ymax + margin,
                        padding=0
                    )

    def toggle_auto_follow(self, checked):
        self.auto_follow = checked

    def change_time_window(self, text):
        self.time_window = float(text)

    def center_plots(self):
        self.auto_follow = True
        self.auto_follow_checkbox.setChecked(True)

        self.linear_plot.enableAutoRange(axis="y")
        self.angular_plot.enableAutoRange(axis="y")
    
    def user_changed_plot(self):
        if self.auto_follow:
            self.auto_follow = False

            self.auto_follow_checkbox.blockSignals(True)
            self.auto_follow_checkbox.setChecked(False)
            self.auto_follow_checkbox.blockSignals(False)

    def closeEvent(self, event):
        self.plot_timer.stop()
        self.ros_worker.stop()
        self.ros_thread.quit()
        self.ros_thread.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("DejaVu Sans", 10))
    pg.setConfigOption("background", DARK)
    pg.setConfigOption("foreground", TEXT)

    window = MensabotMonitor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
