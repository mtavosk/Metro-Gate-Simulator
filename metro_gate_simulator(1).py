#!/usr/bin/env python3
"""
شبیه‌ساز گیت مترو - Metro Gate Simulator
کلاس‌ها: Passenger, Card, Sensor, Motor, Gate, GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
from datetime import datetime
from enum import Enum, auto


# ──────────────────────────── Enumerations ────────────────────────────

class GateState(Enum):
    CLOSED = auto()
    OPENING = auto()
    OPEN = auto()
    CLOSING = auto()
    BLOCKED = auto()


class SensorType(Enum):
    ENTRY = auto()
    EXIT = auto()


class SensorStatus(Enum):
    CLEAR = auto()
    DETECTED = auto()


class CardType(Enum):
    SINGLE_RIDE = auto()
    CREDIT = auto()
    STUDENT = auto()
    ELDERLY = auto()


# ──────────────────────────── Card Class ────────────────────────────

class Card:
    """کلاس کارت مترو - مدیریت موجودی و اعتبار کارت"""

    _card_counter = 100000

    def __init__(self, card_type=CardType.CREDIT, balance=0):
        Card._card_counter += 1
        self.card_number = Card._card_counter
        self.card_type = card_type
        self.balance = balance
        self.is_active = True
        self.issue_date = datetime.now()
        self.last_used = None
        self.ride_count = 0

    def charge(self, amount):
        """شارژ کارت"""
        if amount <= 0:
            return False, "مبلغ شارژ باید مثبت باشد"
        self.balance += amount
        return True, f"شارژ موفق: {amount:,} تومان"

    def deduct(self, amount):
        """کسر هزینه سفر"""
        if not self.is_active:
            return False, "کارت غیرفعال است"
        if self.balance < amount:
            return False, "موجودی ناکافی"
        self.balance -= amount
        self.ride_count += 1
        self.last_used = datetime.now()
        return True, "هزینه کسر شد"

    def get_fare(self):
        """محاسبه هزینه سفر بر اساس نوع کارت"""
        base_fare = 5000  # 5000 تومان پایه
        if self.card_type == CardType.STUDENT:
            return int(base_fare * 0.5)
        elif self.card_type == CardType.ELDERLY:
            return int(base_fare * 0.3)
        elif self.card_type == CardType.SINGLE_RIDE:
            return base_fare
        return base_fare

    def __str__(self):
        type_names = {
            CardType.SINGLE_RIDE: "تک‌سفره",
            CardType.CREDIT: "اعتباری",
            CardType.STUDENT: "دانشجویی",
            CardType.ELDERLY: "سالمندی",
        }
        return f"کارت #{self.card_number} | نوع: {type_names[self.card_type]} | موجودی: {self.balance:,} تومان"


# ──────────────────────────── Passenger Class ────────────────────────────

class Passenger:
    """کلاس مسافر - مدیریت اطلاعات و کارت مسافر"""

    _passenger_counter = 0

    def __init__(self, name=None, card=None):
        Passenger._passenger_counter += 1
        self.id = Passenger._passenger_counter
        self.name = name or f"مسافر {self.id}"
        self.card = card
        self.entry_station = None
        self.exit_station = None
        self.entry_time = None

    def assign_card(self, card):
        """تخصیص کارت به مسافر"""
        self.card = card

    def has_valid_card(self):
        """بررسی اعتبار کارت مسافر"""
        if self.card is None:
            return False
        if not self.card.is_active:
            return False
        if self.card.balance < self.card.get_fare():
            return False
        return True

    def __str__(self):
        return f"{self.name} (شناسه: {self.id})"


# ──────────────────────────── Sensor Class ────────────────────────────

class Sensor:
    """کلاس سنسور - تشخیص حضور مسافر"""

    def __init__(self, sensor_type=SensorType.ENTRY, sensor_id=None):
        self.sensor_id = sensor_id or f"SEN-{random.randint(100, 999)}"
        self.sensor_type = sensor_type
        self.status = SensorStatus.CLEAR
        self.detection_count = 0

    def detect(self):
        """تشخیص حضور مسافر"""
        self.status = SensorStatus.DETECTED
        self.detection_count += 1
        return True

    def clear(self):
        """پاک کردن وضعیت تشخیص"""
        self.status = SensorStatus.CLEAR
        return True

    def __str__(self):
        type_name = "ورود" if self.sensor_type == SensorType.ENTRY else "خروج"
        status_name = "تشخیص" if self.status == SensorStatus.DETECTED else "پاک"
        return f"سنسور {self.sensor_id} | نوع: {type_name} | وضعیت: {status_name}"


# ──────────────────────────── Motor Class ────────────────────────────

class Motor:
    """کلاس موتور - کنترل باز و بسته شدن گیت"""

    def __init__(self, motor_id=None):
        self.motor_id = motor_id or f"MTR-{random.randint(100, 999)}"
        self.is_running = False
        self.angle = 0  # زاویه باز شدن (0 = بسته, 90 = کاملاً باز)
        self.max_angle = 90
        self.speed = 5  # درجه در هر مرحله
        self.status = "بسته"

    def open(self):
        """باز کردن گیت"""
        self.is_running = True
        self.status = "در حال باز شدن"
        return True

    def close(self):
        """بسته کردن گیت"""
        self.is_running = True
        self.status = "در حال بسته شدن"
        return True

    def stop(self):
        """توقف موتور"""
        self.is_running = False
        if self.angle >= 80:
            self.status = "باز"
        elif self.angle <= 10:
            self.status = "بسته"
        else:
            self.status = "متوقف"
        return True

    def is_fully_open(self):
        return self.angle >= self.max_angle

    def is_fully_closed(self):
        return self.angle <= 0

    def __str__(self):
        return f"موتور {self.motor_id} | زاویه: {self.angle}° | وضعیت: {self.status}"


# ──────────────────────────── Gate Class ────────────────────────────

class Gate:
    """کلاس گیت - هماهنگ‌کننده تمام بخش‌ها"""

    def __init__(self, gate_id=None):
        self.gate_id = gate_id or f"GATE-{random.randint(1, 99)}"
        self.state = GateState.CLOSED
        self.motor = Motor(motor_id=f"MTR-{self.gate_id}")
        self.entry_sensor = Sensor(SensorType.ENTRY, f"SEN-{self.gate_id}-IN")
        self.exit_sensor = Sensor(SensorType.EXIT, f"SEN-{self.gate_id}-OUT")
        self.current_passenger = None
        self.passage_count = 0
        self.rejected_count = 0
        self.is_processing = False
        self.message = "آماده"

    def process_entry(self, passenger):
        """پردازش ورود مسافر"""
        if self.is_processing:
            self.message = "لطفاً صبر کنید..."
            return False, "گیت در حال پردازش مسافر قبلی است"

        self.is_processing = True
        self.current_passenger = passenger

        if not passenger.has_valid_card():
            self.state = GateState.BLOCKED
            self.rejected_count += 1
            self.message = "دسترسی رد شد - کارت نامعتبر"
            self.is_processing = False
            self.current_passenger = None
            return False, "کارت نامعتبر یا موجودی ناکافی"

        # کسر هزینه
        fare = passenger.card.get_fare()
        success, msg = passenger.card.deduct(fare)
        if not success:
            self.state = GateState.BLOCKED
            self.rejected_count += 1
            self.message = f"دسترسی رد شد - {msg}"
            self.is_processing = False
            self.current_passenger = None
            return False, msg

        # باز کردن گیت
        self.entry_sensor.detect()
        self.message = f"{passenger.name} - گیت باز شد"
        self.state = GateState.OPENING
        self.passage_count += 1

        passenger.entry_time = datetime.now()
        return True, f"ورود مجاز - هزینه: {fare:,} تومان"

    def process_exit(self, passenger=None):
        """پردازش خروج مسافر از گیت"""
        self.exit_sensor.detect()
        self.state = GateState.CLOSING
        self.message = "گیت در حال بسته شدن..."
        return True, "خروج با موفقیت"

    def complete_passage(self):
        """تکمیل عبور مسافر"""
        self.entry_sensor.clear()
        self.exit_sensor.clear()
        self.state = GateState.CLOSED
        self.current_passenger = None
        self.is_processing = False
        self.message = "آماده"

    def emergency_stop(self):
        """توقف اضطراری"""
        self.motor.stop()
        self.state = GateState.BLOCKED
        self.message = "⚠ توقف اضطراری"

    def reset(self):
        """بازنشانی گیت"""
        self.motor.angle = 0
        self.motor.status = "بسته"
        self.motor.is_running = False
        self.entry_sensor.clear()
        self.exit_sensor.clear()
        self.state = GateState.CLOSED
        self.current_passenger = None
        self.is_processing = False
        self.message = "آماده"

    def __str__(self):
        state_names = {
            GateState.CLOSED: "بسته",
            GateState.OPENING: "در حال باز شدن",
            GateState.OPEN: "باز",
            GateState.CLOSING: "در حال بسته شدن",
            GateState.BLOCKED: "قفل شده",
        }
        return f"گیت {self.gate_id} | وضعیت: {state_names[self.state]} | عبور: {self.passage_count}"


# ──────────────────────────── GUI Class ────────────────────────────

class MetroGateGUI:
    """رابط گرافیکی شبیه‌ساز گیت مترو"""

    # رنگ‌بندی
    BG_COLOR = "#1a1a2e"
    PANEL_COLOR = "#16213e"
    ACCENT_COLOR = "#0f3460"
    HIGHLIGHT_COLOR = "#e94560"
    SUCCESS_COLOR = "#00b894"
    WARNING_COLOR = "#fdcb6e"
    TEXT_COLOR = "#dfe6e9"
    GATE_COLOR = "#636e72"
    GATE_OPEN_COLOR = "#00b894"
    GATE_BLOCKED_COLOR = "#e94560"
    METRO_YELLOW = "#f9ca24"
    SENSOR_GREEN = "#00b894"
    SENSOR_RED = "#e94560"

    def __init__(self, root):
        self.root = root
        self.root.title("شبیه‌ساز گیت مترو | Metro Gate Simulator")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)
        self.root.configure(bg=self.BG_COLOR)

        self.gate = Gate(gate_id="GATE-01")
        self.animation_running = False
        self.animation_id = None
        self.passengers_log = []

        self._setup_styles()
        self._build_ui()
        self._create_sample_passengers()
        self._draw_gate()
        self._update_info()

    def _setup_styles(self):
        """تنظیم استایل ویجت‌ها"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=self.BG_COLOR)
        style.configure("Panel.TFrame", background=self.PANEL_COLOR)
        style.configure("Dark.TLabel", background=self.PANEL_COLOR, foreground=self.TEXT_COLOR, font=("Vazirmatn", 11))
        style.configure("Title.TLabel", background=self.PANEL_COLOR, foreground=self.METRO_YELLOW, font=("Vazirmatn", 14, "bold"))
        style.configure("Status.TLabel", background=self.BG_COLOR, foreground=self.TEXT_COLOR, font=("Vazirmatn", 12, "bold"))
        style.configure("Success.TLabel", background=self.PANEL_COLOR, foreground=self.SUCCESS_COLOR, font=("Vazirmatn", 11))
        style.configure("Warning.TLabel", background=self.PANEL_COLOR, foreground=self.WARNING_COLOR, font=("Vazirmatn", 11))
        style.configure("Error.TLabel", background=self.PANEL_COLOR, foreground=self.HIGHLIGHT_COLOR, font=("Vazirmatn", 11, "bold"))
        style.configure("Accent.TButton", font=("Vazirmatn", 11, "bold"), padding=8)
        style.configure("Dark.TCombobox", font=("Vazirmatn", 10))

    def _build_ui(self):
        """ساخت رابط گرافیکی اصلی"""
        # هدر
        header_frame = tk.Frame(self.root, bg=self.ACCENT_COLOR, height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame, text="🚇  شبیه‌ساز گیت مترو  🚇",
            bg=self.ACCENT_COLOR, fg=self.METRO_YELLOW,
            font=("Vazirmatn", 18, "bold")
        ).pack(expand=True)

        # محتوای اصلی
        main_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # سمت چپ - نمایش گیت
        left_frame = tk.Frame(main_frame, bg=self.PANEL_COLOR, bd=2, relief=tk.RIDGE)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        tk.Label(left_frame, text="نمایش گیت", bg=self.PANEL_COLOR,
                 fg=self.METRO_YELLOW, font=("Vazirmatn", 14, "bold")).pack(pady=(10, 5))

        self.canvas = tk.Canvas(left_frame, width=480, height=420, bg=self.BG_COLOR,
                                highlightthickness=1, highlightbackground=self.ACCENT_COLOR)
        self.canvas.pack(padx=10, pady=5)

        # پیام وضعیت
        self.status_label = tk.Label(left_frame, text="✅ آماده برای عبور مسافر",
                                      bg=self.BG_COLOR, fg=self.SUCCESS_COLOR,
                                      font=("Vazirmatn", 13, "bold"))
        self.status_label.pack(fill=tk.X, padx=10, pady=(5, 10))

        # سمت راست - پنل کنترل
        right_frame = tk.Frame(main_frame, bg=self.BG_COLOR, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_frame.pack_propagate(False)

        self._build_control_panel(right_frame)
        self._build_info_panel(right_frame)
        self._build_log_panel(right_frame)

    def _build_control_panel(self, parent):
        """ساخت پنل کنترل"""
        panel = tk.LabelFrame(parent, text=" ⚙ کنترل گیت ", bg=self.PANEL_COLOR,
                               fg=self.METRO_YELLOW, font=("Vazirmatn", 12, "bold"),
                               bd=2, relief=tk.GROOVE)
        panel.pack(fill=tk.X, pady=(0, 8))

        # انتخاب مسافر
        tk.Label(panel, text="انتخاب مسافر:", bg=self.PANEL_COLOR,
                 fg=self.TEXT_COLOR, font=("Vazirmatn", 11)).pack(anchor=tk.E, padx=10, pady=(10, 2))

        self.passenger_var = tk.StringVar()
        self.passenger_combo = ttk.Combobox(panel, textvariable=self.passenger_var,
                                             state="readonly", font=("Vazirmatn", 10), width=30)
        self.passenger_combo.pack(padx=10, pady=(0, 10))

        # مبلغ شارژ
        tk.Label(panel, text="مبلغ شارژ (تومان):", bg=self.PANEL_COLOR,
                 fg=self.TEXT_COLOR, font=("Vazirmatn", 11)).pack(anchor=tk.E, padx=10, pady=(5, 2))

        self.charge_var = tk.StringVar(value="20000")
        charge_entry = tk.Entry(panel, textvariable=self.charge_var, font=("Vazirmatn", 11),
                                width=32, bg="#2d3436", fg=self.TEXT_COLOR, insertbackground=self.TEXT_COLOR)
        charge_entry.pack(padx=10, pady=(0, 10))

        # دکمه‌ها
        btn_frame = tk.Frame(panel, bg=self.PANEL_COLOR)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.btn_enter = tk.Button(btn_frame, text="🚶 عبور مسافر", font=("Vazirmatn", 11, "bold"),
                                    bg=self.SUCCESS_COLOR, fg="white", activebackground="#00a884",
                                    relief=tk.FLAT, cursor="hand2", command=self._on_pass_enter)
        self.btn_enter.pack(fill=tk.X, pady=2, ipady=4)

        self.btn_charge = tk.Button(btn_frame, text="💳 شارژ کارت", font=("Vazirmatn", 11, "bold"),
                                     bg=self.WARNING_COLOR, fg="#2d3436", activebackground="#f0b830",
                                     relief=tk.FLAT, cursor="hand2", command=self._on_charge_card)
        self.btn_charge.pack(fill=tk.X, pady=2, ipady=4)

        self.btn_reset = tk.Button(btn_frame, text="🔄 بازنشانی گیت", font=("Vazirmatn", 11, "bold"),
                                    bg=self.ACCENT_COLOR, fg="white", activebackground="#0d2d52",
                                    relief=tk.FLAT, cursor="hand2", command=self._on_reset_gate)
        self.btn_reset.pack(fill=tk.X, pady=2, ipady=4)

        # دکمه‌های سریع
        quick_frame = tk.Frame(panel, bg=self.PANEL_COLOR)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(quick_frame, text="+ مسافر جدید", font=("Vazirmatn", 10),
                  bg="#636e72", fg="white", relief=tk.FLAT, cursor="hand2",
                  command=self._on_add_passenger).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3), ipady=3)

        tk.Button(quick_frame, text="⚡ عبور تصادفی", font=("Vazirmatn", 10),
                  bg="#6c5ce7", fg="white", relief=tk.FLAT, cursor="hand2",
                  command=self._on_random_passage).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(3, 0), ipady=3)

    def _build_info_panel(self, parent):
        """ساخت پنل اطلاعات"""
        panel = tk.LabelFrame(parent, text=" 📊 اطلاعات سیستم ", bg=self.PANEL_COLOR,
                               fg=self.METRO_YELLOW, font=("Vazirmatn", 12, "bold"),
                               bd=2, relief=tk.GROOVE)
        panel.pack(fill=tk.X, pady=(0, 8))

        self.info_labels = {}
        info_items = [
            ("gate_state", "وضعیت گیت:"),
            ("motor_status", "وضعیت موتور:"),
            ("motor_angle", "زاویه موتور:"),
            ("entry_sensor", "سنسور ورود:"),
            ("exit_sensor", "سنسور خروج:"),
            ("passage_count", "تعداد عبور:"),
            ("rejected_count", "رد شده:"),
        ]

        for key, label_text in info_items:
            row = tk.Frame(panel, bg=self.PANEL_COLOR)
            row.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(row, text=label_text, bg=self.PANEL_COLOR,
                     fg="#b2bec3", font=("Vazirmatn", 10), anchor=tk.E, width=16).pack(side=tk.RIGHT)
            lbl = tk.Label(row, text="---", bg=self.PANEL_COLOR,
                          fg=self.TEXT_COLOR, font=("Vazirmatn", 10, "bold"), anchor=tk.W)
            lbl.pack(side=tk.RIGHT, padx=(5, 0))
            self.info_labels[key] = lbl

        # اطلاعات کارت
        tk.Frame(panel, bg=self.METRO_YELLOW, height=2).pack(fill=tk.X, padx=10, pady=(8, 5))

        tk.Label(panel, text="اطلاعات کارت مسافر انتخاب‌شده:", bg=self.PANEL_COLOR,
                 fg=self.METRO_YELLOW, font=("Vazirmatn", 11, "bold")).pack(anchor=tk.E, padx=10)

        self.card_info_label = tk.Label(panel, text="مسافری انتخاب نشده",
                                         bg=self.PANEL_COLOR, fg="#b2bec3",
                                         font=("Vazirmatn", 10), justify=tk.RIGHT, wraplength=300)
        self.card_info_label.pack(anchor=tk.E, padx=10, pady=(2, 10))

        # اتصال رویداد انتخاب مسافر
        self.passenger_combo.bind("<<ComboboxSelected>>", self._on_passenger_selected)

    def _build_log_panel(self, parent):
        """ساخت پنل گزارش"""
        panel = tk.LabelFrame(parent, text=" 📋 گزارش رویدادها ", bg=self.PANEL_COLOR,
                               fg=self.METRO_YELLOW, font=("Vazirmatn", 12, "bold"),
                               bd=2, relief=tk.GROOVE)
        panel.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

        self.log_text = tk.Text(panel, bg="#0d1117", fg=self.TEXT_COLOR,
                                 font=("Vazirmatn", 9), height=8, width=35,
                                 state=tk.DISABLED, wrap=tk.WORD, bd=0)
        scrollbar = tk.Scrollbar(panel, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5), pady=5)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        # تگ‌های رنگی برای گزارش
        self.log_text.tag_configure("success", foreground=self.SUCCESS_COLOR)
        self.log_text.tag_configure("error", foreground=self.HIGHLIGHT_COLOR)
        self.log_text.tag_configure("warning", foreground=self.WARNING_COLOR)
        self.log_text.tag_configure("info", foreground="#74b9ff")
        self.log_text.tag_configure("time", foreground="#636e72")

    # ──────────────── Drawing Methods ────────────────

    def _draw_gate(self):
        """رسم گیت مترو روی کنواس"""
        self.canvas.delete("all")
        w, h = 480, 420

        # زمین
        self.canvas.create_rectangle(0, h - 60, w, h, fill="#2d3436", outline="")
        self.canvas.create_line(0, h - 60, w, h - 60, fill="#636e72", width=2)

        # خطوط مترو (راهنما)
        for i in range(0, w, 40):
            self.canvas.create_line(i, h - 55, i + 20, h - 55, fill="#636e72", width=1, dash=(4, 4))

        # ستون‌های گیت
        self._draw_gate_pillars()

        # بال‌های گیت
        self._draw_gate_flaps()

        # سنسورها
        self._draw_sensors()

        # مسافر
        self._draw_passenger()

        # مسیر حرکت
        self._draw_path_indicators()

    def _draw_gate_pillars(self):
        """رسم ستون‌های گیت"""
        # ستون چپ
        self.canvas.create_rectangle(100, 100, 130, 360, fill="#636e72", outline="#b2bec3", width=2)
        self.canvas.create_rectangle(105, 105, 125, 355, fill="#4a5568", outline="")

        # ستون راست
        self.canvas.create_rectangle(350, 100, 380, 360, fill="#636e72", outline="#b2bec3", width=2)
        self.canvas.create_rectangle(355, 105, 375, 355, fill="#4a5568", outline="")

        # نوار بالایی
        self.canvas.create_rectangle(100, 90, 380, 110, fill=self.ACCENT_COLOR, outline="#1a5276", width=2)
        self.canvas.create_text(240, 100, text="METRO GATE", fill=self.METRO_YELLOW,
                                font=("Arial", 10, "bold"))

        # چراغ وضعیت
        self._draw_status_light(240, 125)

    def _draw_status_light(self, x, y):
        """رسم چراغ وضعیت گیت"""
        color = "#00b894"
        if self.gate.state == GateState.BLOCKED:
            color = "#e94560"
        elif self.gate.state in (GateState.OPENING, GateState.OPEN):
            color = "#00b894"
        elif self.gate.state == GateState.CLOSING:
            color = "#fdcb6e"

        # هاله نور
        self.canvas.create_oval(x - 18, y - 18, x + 18, y + 18, fill="", outline=color, width=2)
        # چراغ
        self.canvas.create_oval(x - 12, y - 12, x + 12, y + 12, fill=color, outline="white", width=2)

    def _draw_gate_flaps(self):
        """رسم بال‌های گیت با توجه به زاویه موتور"""
        angle = self.gate.motor.angle
        open_factor = angle / 90.0  # 0 = بسته, 1 = باز

        # بال چپ
        left_base_x = 130
        left_base_y = 200
        left_length = 110
        left_angle_rad = (90 - angle * 0.7) * (3.14159 / 180)

        left_end_x = left_base_x + left_length * abs(open_factor - 0.3)
        left_end_y = left_base_y + 30 * (1 - open_factor)

        flap_color = self.GATE_OPEN_COLOR if open_factor > 0.5 else (self.GATE_BLOCKED_COLOR if self.gate.state == GateState.BLOCKED else self.GATE_COLOR)

        if open_factor > 0.3:
            self.canvas.create_line(left_base_x, left_base_y, left_end_x, left_end_y,
                                     fill=flap_color, width=6, capstyle=tk.ROUND)
        else:
            self.canvas.create_line(left_base_x, left_base_y, left_base_x + 80, left_base_y + 15,
                                     fill=flap_color, width=6, capstyle=tk.ROUND)

        # بال راست
        right_base_x = 350
        right_base_y = 200
        right_end_x = right_base_x - 110 * abs(open_factor - 0.3)
        right_end_y = right_base_y + 30 * (1 - open_factor)

        if open_factor > 0.3:
            self.canvas.create_line(right_base_x, right_base_y, right_end_x, right_end_y,
                                     fill=flap_color, width=6, capstyle=tk.ROUND)
        else:
            self.canvas.create_line(right_base_x, right_base_y, right_base_x - 80, right_base_y + 15,
                                     fill=flap_color, width=6, capstyle=tk.ROUND)

        # بال پایین چپ
        self.canvas.create_line(130, 300, 130 + 80 * (1 - open_factor * 0.8), 300 + 10,
                                 fill=flap_color, width=5, capstyle=tk.ROUND)

        # بال پایین راست
        self.canvas.create_line(350, 300, 350 - 80 * (1 - open_factor * 0.8), 300 + 10,
                                 fill=flap_color, width=5, capstyle=tk.ROUND)

    def _draw_sensors(self):
        """رسم سنسورهای ورود و خروج"""
        # سنسور ورود
        entry_color = self.SENSOR_GREEN if self.gate.entry_sensor.status == SensorStatus.DETECTED else self.SENSOR_RED
        self.canvas.create_oval(55, 195, 85, 225, fill=entry_color, outline="white", width=2)
        self.canvas.create_text(70, 240, text="سنسور\nورود", fill=self.TEXT_COLOR,
                                font=("Vazirmatn", 8), justify=tk.CENTER)

        # سنسور خروج
        exit_color = self.SENSOR_GREEN if self.gate.exit_sensor.status == SensorStatus.DETECTED else self.SENSOR_RED
        self.canvas.create_oval(395, 195, 425, 225, fill=exit_color, outline="white", width=2)
        self.canvas.create_text(410, 240, text="سنسور\nخروج", fill=self.TEXT_COLOR,
                                font=("Vazirmatn", 8), justify=tk.CENTER)

        # اشعه مادون قرمز (نمادین)
        if self.gate.entry_sensor.status == SensorStatus.DETECTED:
            self.canvas.create_line(85, 210, 100, 210, fill="#ff6b6b", width=2, dash=(3, 2))
        else:
            self.canvas.create_line(85, 210, 100, 210, fill="#00b894", width=1, dash=(5, 3))

        if self.gate.exit_sensor.status == SensorStatus.DETECTED:
            self.canvas.create_line(380, 210, 395, 210, fill="#ff6b6b", width=2, dash=(3, 2))
        else:
            self.canvas.create_line(380, 210, 395, 210, fill="#00b894", width=1, dash=(5, 3))

    def _draw_passenger(self):
        """رسم مسافر"""
        if self.gate.current_passenger is None and self.gate.state == GateState.CLOSED:
            # مسافر منتظر
            self._draw_person(50, 310, "#b2bec3", "مسافر\nبعدی")
        elif self.gate.state in (GateState.OPENING, GateState.OPEN):
            # مسافر در حال عبور
            progress = self.gate.motor.angle / 90.0
            px = 150 + progress * 180
            self._draw_person(px, 320, "#74b9ff", self.gate.current_passenger.name if self.gate.current_passenger else "")

    def _draw_person(self, x, y, color, name=""):
        """رسم شکلک مسافر"""
        # سر
        self.canvas.create_oval(x - 12, y - 45, x + 12, y - 20, fill=color, outline="white", width=2)
        # بدن
        self.canvas.create_line(x, y - 20, x, y + 15, fill=color, width=3)
        # دست‌ها
        self.canvas.create_line(x - 15, y - 5, x + 15, y - 5, fill=color, width=2)
        # پاها
        self.canvas.create_line(x, y + 15, x - 10, y + 35, fill=color, width=2)
        self.canvas.create_line(x, y + 15, x + 10, y + 35, fill=color, width=2)
        # نام
        if name:
            self.canvas.create_text(x, y + 50, text=name, fill=self.TEXT_COLOR,
                                     font=("Vazirmatn", 8), justify=tk.CENTER)

    def _draw_path_indicators(self):
        """رسم مسیر حرکت مسافر"""
        # فلش ورود
        self.canvas.create_text(50, 170, text="➡ ورود", fill="#636e72", font=("Vazirmatn", 9))
        # فلش خروج
        self.canvas.create_text(430, 170, text="خروج ➡", fill="#636e72", font=("Vazirmatn", 9))
        # نمایش زاویه
        self.canvas.create_text(240, 390, text=f"زاویه باز شدن: {self.gate.motor.angle}°",
                                fill=self.TEXT_COLOR, font=("Vazirmatn", 10))

    # ──────────────── Animation ────────────────

    def _animate_gate_opening(self):
        """انیمیشن باز شدن گیت"""
        if self.gate.motor.angle < 90:
            self.gate.motor.angle += self.gate.motor.speed
            if self.gate.motor.angle >= 90:
                self.gate.motor.angle = 90
                self.gate.motor.status = "باز"
                self.gate.state = GateState.OPEN

            self._draw_gate()
            self._update_info()
            self.animation_id = self.root.after(40, self._animate_gate_opening)
        else:
            self.animation_running = False
            # شروع انیمیشن خروج مسافر
            self.root.after(1200, self._start_closing)

    def _start_closing(self):
        """شروع بسته شدن گیت بعد از عبور"""
        if self.gate.state == GateState.OPEN:
            self.gate.process_exit()
            self._set_status("⚠ گیت در حال بسته شدن...", self.WARNING_COLOR)
            self._animate_gate_closing()

    def _animate_gate_closing(self):
        """انیمیشن بسته شدن گیت"""
        if self.gate.motor.angle > 0:
            self.gate.motor.angle -= self.gate.motor.speed
            if self.gate.motor.angle <= 0:
                self.gate.motor.angle = 0
                self.gate.motor.status = "بسته"

            self._draw_gate()
            self._update_info()
            self.animation_id = self.root.after(40, self._animate_gate_closing)
        else:
            self.animation_running = False
            self.gate.complete_passage()
            self._draw_gate()
            self._update_info()
            self._set_status("✅ آماده برای عبور مسافر بعدی", self.SUCCESS_COLOR)
            self.btn_enter.config(state=tk.NORMAL)

    def _animate_blocked(self):
        """انیمیشن وقتی گیت قفل می‌شود"""
        # فلش زدن چراغ قرمز
        self._draw_gate()
        self._update_info()
        # ۳ بار چشمک زدن
        self._blink_count = 0
        self._blink_blocked()

    def _blink_blocked(self):
        """چشمک زدن قرمز هنگام رد شدن"""
        if self._blink_count < 6:
            self._blink_count += 1
            if self._blink_count % 2 == 1:
                self.canvas.create_rectangle(95, 85, 385, 370,
                                              outline=self.HIGHLIGHT_COLOR, width=4)
            else:
                self._draw_gate()
            self.root.after(200, self._blink_blocked)
        else:
            self._draw_gate()
            self.btn_enter.config(state=tk.NORMAL)

    # ──────────────── Info Update ────────────────

    def _update_info(self):
        """بروزرسانی اطلاعات نمایشی"""
        state_names = {
            GateState.CLOSED: "🔒 بسته",
            GateState.OPENING: "🔓 در حال باز شدن",
            GateState.OPEN: "🔓 باز",
            GateState.CLOSING: "🔒 در حال بسته شدن",
            GateState.BLOCKED: "🚫 قفل شده",
        }
        sensor_status = {SensorStatus.CLEAR: "🟢 پاک", SensorStatus.DETECTED: "🔴 تشخیص"}

        self.info_labels["gate_state"].config(text=state_names.get(self.gate.state, "---"))
        self.info_labels["motor_status"].config(text=self.gate.motor.status)
        self.info_labels["motor_angle"].config(text=f"{self.gate.motor.angle}°")
        self.info_labels["entry_sensor"].config(text=sensor_status[self.gate.entry_sensor.status])
        self.info_labels["exit_sensor"].config(text=sensor_status[self.gate.exit_sensor.status])
        self.info_labels["passage_count"].config(text=str(self.gate.passage_count),
                                                  fg=self.SUCCESS_COLOR if self.gate.passage_count > 0 else self.TEXT_COLOR)
        self.info_labels["rejected_count"].config(text=str(self.gate.rejected_count),
                                                   fg=self.HIGHLIGHT_COLOR if self.gate.rejected_count > 0 else self.TEXT_COLOR)

    def _set_status(self, text, color):
        """تنظیم پیام وضعیت"""
        self.status_label.config(text=text, fg=color)

    def _update_card_info(self, passenger):
        """بروزرسانی نمایش اطلاعات کارت"""
        if passenger is None or passenger.card is None:
            self.card_info_label.config(text="مسافری انتخاب نشده", fg="#b2bec3")
            return

        card = passenger.card
        type_names = {
            CardType.SINGLE_RIDE: "تک‌سفره",
            CardType.CREDIT: "اعتباری",
            CardType.STUDENT: "دانشجویی",
            CardType.ELDERLY: "سالمندی",
        }
        fare = card.get_fare()
        balance_color = self.SUCCESS_COLOR if card.balance >= fare else self.HIGHLIGHT_COLOR

        info = (
            f"شماره کارت: {card.card_number}\n"
            f"نوع: {type_names[card.card_type]}\n"
            f"موجودی: {card.balance:,} تومان\n"
            f"هزینه سفر: {fare:,} تومان\n"
            f"تعداد سفر: {card.ride_count}"
        )
        self.card_info_label.config(text=info, fg=balance_color)

    # ──────────────── Logging ────────────────

    def _log(self, message, tag="info"):
        """ثبت رویداد در گزارش"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] ", "time")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    # ──────────────── Sample Data ────────────────

    def _create_sample_passengers(self):
        """ایجاد مسافران نمونه"""
        self.sample_passengers = []

        # مسافر ۱ - کارت اعتباری با موجودی
        p1 = Passenger("علی احمدی", Card(CardType.CREDIT, 50000))
        self.sample_passengers.append(p1)

        # مسافر ۲ - کارت دانشجویی
        p2 = Passenger("سارا محمدی", Card(CardType.STUDENT, 15000))
        self.sample_passengers.append(p2)

        # مسافر ۳ - کارت سالمندی
        p3 = Passenger("حاج رضا", Card(CardType.ELDERLY, 10000))
        self.sample_passengers.append(p3)

        # مسافر ۴ - کارت بدون موجودی
        p4 = Passenger("مریم حسینی", Card(CardType.CREDIT, 2000))
        self.sample_passengers.append(p4)

        # مسافر ۵ - بدون کارت
        p5 = Passenger("رضا کریمی", None)
        self.sample_passengers.append(p5)

        # مسافر ۶ - کارت تک‌سفره
        p6 = Passenger("فاطمه نوری", Card(CardType.SINGLE_RIDE, 5000))
        self.sample_passengers.append(p6)

        self._refresh_passenger_list()
        self._log("سیستم شبیه‌ساز گیت مترو راه‌اندازی شد", "success")
        self._log(f"{len(self.sample_passengers)} مسافر نمونه ایجاد شد", "info")

    def _refresh_passenger_list(self):
        """بروزرسانی لیست مسافران"""
        names = [f"{p.name} | موجودی: {p.card.balance:,} ت" if p.card else f"{p.name} | بدون کارت"
                 for p in self.sample_passengers]
        self.passenger_combo['values'] = names
        if names:
            self.passenger_combo.current(0)
            self._on_passenger_selected(None)

    def _find_selected_passenger(self):
        """یافتن مسافر انتخاب‌شده"""
        idx = self.passenger_combo.current()
        if 0 <= idx < len(self.sample_passengers):
            return self.sample_passengers[idx]
        return None

    # ──────────────── Event Handlers ────────────────

    def _on_passenger_selected(self, event):
        """رویداد انتخاب مسافر"""
        passenger = self._find_selected_passenger()
        self._update_card_info(passenger)

    def _on_pass_enter(self):
        """رویداد عبور مسافر"""
        if self.animation_running or self.gate.is_processing:
            self._set_status("⏳ لطفاً صبر کنید...", self.WARNING_COLOR)
            return

        passenger = self._find_selected_passenger()
        if passenger is None:
            messagebox.showwarning("هشدار", "لطفاً یک مسافر انتخاب کنید!")
            return

        self._log(f"درخواست عبور: {passenger.name}", "info")
        success, msg = self.gate.process_entry(passenger)

        if success:
            self._log(f"✅ {msg}", "success")
            self._set_status(f"✅ {passenger.name} - گیت باز شد", self.SUCCESS_COLOR)
            self.btn_enter.config(state=tk.DISABLED)
            self.animation_running = True
            self.gate.motor.open()
            self._animate_gate_opening()
        else:
            self._log(f"❌ {msg}", "error")
            self._set_status(f"❌ {msg}", self.HIGHLIGHT_COLOR)
            self._animate_blocked()

        self._update_card_info(passenger)
        self._refresh_passenger_list()

    def _on_charge_card(self):
        """رویداد شارژ کارت"""
        passenger = self._find_selected_passenger()
        if passenger is None:
            messagebox.showwarning("هشدار", "لطفاً یک مسافر انتخاب کنید!")
            return
        if passenger.card is None:
            messagebox.showwarning("هشدار", f"{passenger.name} کارت ندارد!")
            return

        try:
            amount = int(self.charge_var.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "مبلغ شارژ نامعتبر است!")
            return

        success, msg = passenger.card.charge(amount)
        if success:
            self._log(f"💳 شارژ کارت {passenger.name}: {amount:,} تومان", "success")
            messagebox.showinfo("موفق", f"کارت {passenger.name} با مبلغ {amount:,} تومان شارژ شد.")
        else:
            self._log(f"❌ خطا در شارژ: {msg}", "error")

        self._update_card_info(passenger)
        self._refresh_passenger_list()

    def _on_reset_gate(self):
        """رویداد بازنشانی گیت"""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        self.animation_running = False

        self.gate.reset()
        self._draw_gate()
        self._update_info()
        self._set_status("✅ گیت بازنشانی شد - آماده برای عبور", self.SUCCESS_COLOR)
        self.btn_enter.config(state=tk.NORMAL)
        self._log("🔄 گیت بازنشانی شد", "warning")

    def _on_add_passenger(self):
        """رویداد افزودن مسافر جدید"""
        names = ["امیر", "نازنین", "حسین", "زهرا", "مهدی", "الهام", "پویا", "شیما",
                 "کامران", "مینا", "بهروز", "ندا", "داریوش", "پریسا"]
        name = random.choice(names) + " " + random.choice(["رضایی", "موسوی", "جعفری", "عباسی", "قاسمی", "طاهری"])

        card_types = [CardType.CREDIT, CardType.STUDENT, CardType.ELDERLY, CardType.SINGLE_RIDE]
        card_type = random.choice(card_types)
        balance = random.choice([0, 1000, 3000, 5000, 10000, 20000, 50000, 100000])

        passenger = Passenger(name, Card(card_type, balance))
        self.sample_passengers.append(passenger)
        self._refresh_passenger_list()
        self._log(f"➕ مسافر جدید: {name} ({passenger.card.card_number})", "info")

    def _on_random_passage(self):
        """رویداد عبور تصادفی"""
        if self.animation_running or self.gate.is_processing:
            return

        # ایجاد مسافر تصادفی
        names = ["مسافر", "مسافر", "مسافر"]
        name = random.choice(names) + f" #{random.randint(100, 999)}"
        card_types = [CardType.CREDIT, CardType.CREDIT, CardType.STUDENT, CardType.ELDERLY]
        card_type = random.choice(card_types)

        # ۸۰٪ شانس موجودی کافی
        if random.random() < 0.8:
            balance = random.choice([5000, 10000, 20000, 50000])
        else:
            balance = random.choice([0, 500, 1000, 2000])

        passenger = Passenger(name, Card(card_type, balance))
        self.sample_passengers.append(passenger)
        self._refresh_passenger_list()

        # انتخاب مسافر جدید و عبور
        self.passenger_combo.current(len(self.sample_passengers) - 1)
        self._on_passenger_selected(None)
        self.root.after(300, self._on_pass_enter)


# ──────────────────────────── Main ────────────────────────────

def main():
    root = tk.Tk()

    # تلاش برای تنظیم فونت فارسی
    try:
        root.tk.call("font", "create", "Vazirmatn", "-family", "Vazirmatn",
                      "-size", 11, "-weight", "normal")
    except Exception:
        try:
            root.tk.call("font", "create", "Vazirmatn", "-family", "Arial",
                          "-size", 11, "-weight", "normal")
        except Exception:
            pass

    app = MetroGateGUI(root)

    # مرکز کردن پنجره
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()