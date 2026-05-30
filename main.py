# main.py
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
import threading

# ─── Android Imports ───────────────────────────────────────────
try:
    from android.permissions import request_permissions, Permission
    from android import mActivity
    from jnius import autoclass, cast

    # Android classes
    Intent          = autoclass('android.content.Intent')
    MediaProjectionManager = autoclass('android.media.projection.MediaProjectionManager')
    Context         = autoclass('android.content.Context')
    WindowManager   = autoclass('android.view.WindowManager')
    LayoutParams    = autoclass('android.view.WindowManager$LayoutParams')
    PixelFormat     = autoclass('android.graphics.PixelFormat')
    Gravity         = autoclass('android.view.Gravity')
    View            = autoclass('android.view.View')
    Build           = autoclass('android.os.Build')
    Settings        = autoclass('android.provider.Settings')
    Uri             = autoclass('android.net.Uri')
    ANDROID         = True
except Exception:
    ANDROID = False

import cv2
import numpy as np

# ─── Colors ────────────────────────────────────────────────────
BG_DARK      = get_color_from_hex('#12111A')
BG_PANEL     = get_color_from_hex('#1A1828')
BG_CARD      = get_color_from_hex('#21203099')
PURPLE       = get_color_from_hex('#6C5CE7')
PURPLE_GLOW  = get_color_from_hex('#8B7FFF')
GREEN        = get_color_from_hex('#00D26A')
WHITE        = get_color_from_hex('#FFFFFF')
GREY         = get_color_from_hex('#888888')

# ─── ESP Overlay ───────────────────────────────────────────────
class ESPOverlay(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.boxes   = []
        self.enabled = False

    def update_boxes(self, boxes):
        self.boxes = boxes
        self.canvas.clear()
        if not self.enabled:
            return
        with self.canvas:
            for (x, y, w, h, label, conf) in self.boxes:
                # Fill
                Color(0.42, 0.36, 0.9, 0.08)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[6])
                # Border
                Color(0.42, 0.36, 0.9, 1)
                Line(rounded_rectangle=(x, y, w, h, 6), width=2)
                # Corner TL
                Color(0, 0.82, 0.42, 1)
                Line(points=[x, y+h, x+18, y+h], width=3)
                Line(points=[x, y+h, x, y+h-18], width=3)
                # Corner TR
                Line(points=[x+w-18, y+h, x+w, y+h], width=3)
                Line(points=[x+w, y+h, x+w, y+h-18], width=3)
                # Corner BL
                Line(points=[x, y, x+18, y], width=3)
                Line(points=[x, y, x, y+20], width=3)
                # Corner BR
                Line(points=[x+w-18, y, x+w, y], width=3)
                Line(points=[x+w, y, x+w, y+20], width=3)

# ─── Draggable GUI Panel ────────────────────────────────────────
class DraggablePanel(FloatLayout):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref    = app_ref
        self._drag      = False
        self._drag_off  = (0, 0)
        self.hidden     = False
        self.size_hint  = (None, None)
        self.size       = (dp(320), dp(420))
        self.pos        = (dp(20), Window.height - dp(440))
        self._build()

    def _build(self):
        with self.canvas.before:
            # Glow border
            Color(*PURPLE_GLOW, 0.4)
            self.glow_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(18)]
            )
            # Main background
            Color(*BG_PANEL)
            self.bg_rect = RoundedRectangle(
                pos=(self.pos[0]+2, self.pos[1]+2),
                size=(self.size[0]-4, self.size[1]-4),
                radius=[dp(16)]
            )

        self.bind(pos=self._update_bg, size=self._update_bg)

        # ── Sidebar ──────────────────────────────────────────
        sidebar = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=dp(90),
            padding=dp(12),
            spacing=dp(8),
            pos_hint={'x': 0, 'y': 0}
        )

        # Logo area
        logo_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=dp(4)
        )
        logo_label = Label(
            text='[b][color=8B7FFF]ESP[/color][/b]',
            markup=True,
            font_size=dp(18),
            size_hint_y=None,
            height=dp(30)
        )
        version_label = Label(
            text='[color=666666]v1.0.0[/color]',
            markup=True,
            font_size=dp(10),
            size_hint_y=None,
            height=dp(20)
        )
        logo_box.add_widget(logo_label)
        logo_box.add_widget(version_label)
        sidebar.add_widget(logo_box)

        # Home button
        home_btn = Button(
            text='  Home',
            background_color=(*PURPLE, 1),
            background_normal='',
            color=WHITE,
            font_size=dp(12),
            size_hint_y=None,
            height=dp(44),
            halign='left'
        )
        sidebar.add_widget(home_btn)
        sidebar.add_widget(Widget())

        # Status box
        status_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            padding=dp(8)
        )
        with status_box.canvas.before:
            Color(*BG_CARD)
            RoundedRectangle(
                pos=status_box.pos,
                size=status_box.size,
                radius=[dp(10)]
            )
        status_label = Label(
            text='[color=888888]Status[/color]',
            markup=True,
            font_size=dp(10)
        )
        online_label = Label(
            text='[color=00D26A]● Online[/color]',
            markup=True,
            font_size=dp(11)
        )
        status_box.add_widget(status_label)
        status_box.add_widget(online_label)
        sidebar.add_widget(status_box)

        # ── Main content ──────────────────────────────────────
        content = BoxLayout(
            orientation='vertical',
            padding=dp(16),
            spacing=dp(12),
            pos_hint={'x': dp(90)/self.width, 'y': 0},
            size_hint=(None, 1),
            width=self.width - dp(90)
        )

        # Header row with hide button
        header_row = BoxLayout(
            size_hint_y=None,
            height=dp(36),
            spacing=dp(8)
        )
        home_title = Label(
            text='[b]Home[/b]',
            markup=True,
            font_size=dp(20),
            color=WHITE,
            halign='left'
        )
        hide_btn = Button(
            text='−',
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            background_color=(*BG_CARD[:3], 1),
            background_normal='',
            color=WHITE,
            font_size=dp(16)
        )
        close_btn = Button(
            text='×',
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            background_color=(0.8, 0.2, 0.2, 1),
            background_normal='',
            color=WHITE,
            font_size=dp(16)
        )
        hide_btn.bind(on_press=self.toggle_hide)
        close_btn.bind(on_press=self.close_panel)
        header_row.add_widget(home_title)
        header_row.add_widget(Widget())
        header_row.add_widget(hide_btn)
        header_row.add_widget(close_btn)

        welcome = Label(
            text='[color=888888]Welcome to ESP[/color]',
            markup=True,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(20),
            halign='left'
        )

        # ESP toggle card
        esp_card = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            padding=dp(12),
            spacing=dp(12)
        )
        with esp_card.canvas.before:
            Color(0.13, 0.12, 0.20, 1)
            self.card_rect = RoundedRectangle(
                pos=esp_card.pos,
                size=esp_card.size,
                radius=[dp(12)]
            )
        esp_card.bind(
            pos=lambda i, v: setattr(self.card_rect, 'pos', v),
            size=lambda i, v: setattr(self.card_rect, 'size', v)
        )

        icon_box = BoxLayout(
            size_hint=(None, None),
            size=(dp(40), dp(40))
        )
        with icon_box.canvas.before:
            Color(*PURPLE, 0.3)
            RoundedRectangle(
                pos=icon_box.pos,
                size=icon_box.size,
                radius=[dp(10)]
            )
        eye_label = Label(
            text='👁',
            font_size=dp(20)
        )
        icon_box.add_widget(eye_label)

        esp_text = BoxLayout(orientation='vertical', spacing=dp(2))
        esp_title = Label(
            text='[b]ESP[/b]',
            markup=True,
            font_size=dp(14),
            color=WHITE,
            halign='left'
        )
        esp_sub = Label(
            text='[color=888888]Extra sensory perception[/color]',
            markup=True,
            font_size=dp(10),
            halign='left'
        )
        esp_text.add_widget(esp_title)
        esp_text.add_widget(esp_sub)

        self.esp_toggle = Switch(
            active=False,
            size_hint=(None, None),
            size=(dp(60), dp(30))
        )
        self.esp_toggle.bind(active=self.on_esp_toggle)

        esp_card.add_widget(icon_box)
        esp_card.add_widget(esp_text)
        esp_card.add_widget(Widget())
        esp_card.add_widget(self.esp_toggle)

        content.add_widget(header_row)
        content.add_widget(welcome)
        content.add_widget(esp_card)
        content.add_widget(Widget())

        main_row = BoxLayout(orientation='horizontal')
        main_row.add_widget(sidebar)
        main_row.add_widget(content)

        self.add_widget(main_row)

    def _update_bg(self, *args):
        self.glow_rect.pos  = self.pos
        self.glow_rect.size = self.size
        self.bg_rect.pos    = (self.pos[0]+2, self.pos[1]+2)
        self.bg_rect.size   = (self.size[0]-4, self.size[1]-4)

    def on_esp_toggle(self, instance, value):
        self.app_ref.esp_enabled = value
        self.app_ref.overlay.enabled = value
        if not value:
            self.app_ref.overlay.update_boxes([])

    def toggle_hide(self, *args):
        self.hidden = not self.hidden
        if self.hidden:
            anim = Animation(opacity=0, duration=0.2)
            anim.start(self)
        else:
            anim = Animation(opacity=1, duration=0.2)
            anim.start(self)

    def close_panel(self, *args):
        self.app_ref.stop()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._drag = True
            self._drag_off = (touch.x - self.x, touch.y - self.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._drag:
            self.x = touch.x - self._drag_off[0]
            self.y = touch.y - self._drag_off[1]
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        self._drag = False
        return super().on_touch_up(touch)

# ─── Start Screen ───────────────────────────────────────────────
class StartScreen(FloatLayout):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(*BG_DARK)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda i,v: setattr(self.bg,'pos',v),
            size=lambda i,v: setattr(self.bg,'size',v)
        )

        title = Label(
            text='[b]FLICK CRASHER[/b]',
            markup=True,
            font_size=dp(28),
            color=WHITE,
            pos_hint={'center_x': 0.5, 'top': 0.92}
        )

        status = Label(
            text='[color=00D26A]● Ready[/color]',
            markup=True,
            font_size=dp(13),
            pos_hint={'center_x': 0.5, 'top': 0.84}
        )

        start_btn = Button(
            text='▶  START',
            font_size=dp(18),
            bold=True,
            size_hint=(None, None),
            size=(dp(160), dp(160)),
            pos_hint={'center_x': 0.5, 'center_y': 0.45},
            background_normal='',
            background_color=(0.23, 0.63, 1, 1),
            color=WHITE,
            border=(80, 80, 80, 80)
        )
        start_btn.bind(on_press=self.on_start)

        telegram_btn = Button(
            text='✈  Telegram Channel',
            font_size=dp(14),
            size_hint=(1, None),
            height=dp(52),
            pos_hint={'x': 0, 'y': 0},
            background_normal='',
            background_color=(0.12, 0.12, 0.18, 1),
            color=WHITE
        )

        self.add_widget(title)
        self.add_widget(status)
        self.add_widget(start_btn)
        self.add_widget(telegram_btn)

    def on_start(self, *args):
        self.app_ref.launch_esp()

# ─── Main App ───────────────────────────────────────────────────
class ESPApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.esp_enabled    = False
        self.overlay        = None
        self.panel          = None
        self.capture_thread = None
        self.running        = False

    def build(self):
        Window.clearcolor = (*BG_DARK, 1)
        self.root_layout = FloatLayout()
        self.start_screen = StartScreen(self)
        self.root_layout.add_widget(self.start_screen)
        return self.root_layout

    def launch_esp(self):
        if ANDROID:
            request_permissions([
                Permission.CAMERA,
                Permission.FOREGROUND_SERVICE,
                Permission.SYSTEM_ALERT_WINDOW
            ], self._on_permissions)
        else:
            self._start_esp()

    def _on_permissions(self, permissions, grants):
        self._start_esp()

    def _start_esp(self):
        # Remove start screen
        self.root_layout.remove_widget(self.start_screen)

        # Add ESP overlay
        self.overlay = ESPOverlay(
            size=Window.size,
            pos=(0, 0)
        )
        self.root_layout.add_widget(self.overlay)

        # Add draggable panel
        self.panel = DraggablePanel(self)
        self.root_layout.add_widget(self.panel)

        # Start detection loop
        self.running = True
        self.capture_thread = threading.Thread(
            target=self._detection_loop,
            daemon=True
        )
        self.capture_thread.start()
        Clock.schedule_interval(self._refresh_overlay, 1.0/30.0)

    def _detection_loop(self):
        net = cv2.dnn.readNetFromCaffe(
            'deploy.prototxt',
            'mobilenet_iter_73000.caffemodel'
        )
        CLASSES = ["background","aeroplane","bicycle","bird","boat",
                   "bottle","bus","car","cat","chair","cow",
                   "diningtable","dog","horse","motorbike","person",
                   "pottedplant","sheep","sofa","train","tvmonitor"]

        cap = cv2.VideoCapture(0)
        self._boxes = []

        while self.running:
            if not self.esp_enabled:
                self._boxes = []
                continue
            ret, frame = cap.read()
            if not ret:
                continue
            h, w = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)),
                0.007843, (300, 300), 127.5
            )
            net.setInput(blob)
            detections = net.forward()
            boxes = []
            for i in range(detections.shape[2]):
                conf = detections[0, 0, i, 2]
                if conf > 0.5:
                    idx = int(detections[0, 0, i, 1])
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    sx, sy, ex, ey = box.astype('int')
                    label = CLASSES[idx] if idx < len(CLASSES) else 'Target'
                    boxes.append((sx, sy, ex-sx, ey-sy, label, float(conf)))
            self._boxes = boxes
        cap.release()

    def _refresh_overlay(self, dt):
        if self.overlay and hasattr(self, '_boxes'):
            self.overlay.update_boxes(self._boxes)

    def on_stop(self):
        self.running = False

if __name__ == '__main__':
    ESPApp().run()
