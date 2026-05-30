# main.py
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.switch import Switch
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics.texture import Texture
from kivy.uix.camera import Camera
import cv2
import numpy as np

Window.clearcolor = (0, 0, 0, 0)

class ESPBoxOverlay(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.boxes = []
        self.esp_enabled = False

    def update_boxes(self, boxes):
        self.boxes = boxes
        self.canvas.clear()
        if not self.esp_enabled:
            return
        with self.canvas:
            for (x, y, w, h, label, conf) in self.boxes:
                # Box fill
                Color(0, 1, 0.5, 0.08)
                Rectangle(pos=(x, y), size=(w, h))
                # Box border
                Color(0, 1, 0.5, 1)
                Line(rectangle=(x, y, w, h), width=2)
                # Corner accents TL
                Color(0, 1, 1, 1)
                Line(points=[x, y+h, x+20, y+h], width=3)
                Line(points=[x, y+h, x, y+h-20], width=3)
                # Corner TR
                Line(points=[x+w-20, y+h, x+w, y+h], width=3)
                Line(points=[x+w, y+h, x+w, y+h-20], width=3)
                # Corner BL
                Line(points=[x, y, x+20, y], width=3)
                Line(points=[x, y, x, y+20], width=3)
                # Corner BR
                Line(points=[x+w-20, y, x+w, y], width=3)
                Line(points=[x+w, y, x+w, y+20], width=3)

class AIDetector:
    def __init__(self):
        self.net = cv2.dnn.readNetFromCaffe(
            'deploy.prototxt',
            'mobilenet_iter_73000.caffemodel'
        )
        self.CLASSES = ["background","aeroplane","bicycle","bird",
                        "boat","bottle","bus","car","cat","chair",
                        "cow","diningtable","dog","horse","motorbike",
                        "person","pottedplant","sheep","sofa",
                        "train","tvmonitor"]

    def detect(self, frame):
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            0.007843, (300, 300), 127.5
        )
        self.net.setInput(blob)
        detections = self.net.forward()
        boxes = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (sx, sy, ex, ey) = box.astype("int")
                bw = ex - sx
                bh = ey - sy
                label = self.CLASSES[idx] if idx < len(self.CLASSES) else "Target"
                boxes.append((sx, sy, bw, bh, label, float(confidence)))
        return boxes

class ESPLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.detector = AIDetector()
        self.esp_active = False
        self.build_gui()
        self.overlay = ESPBoxOverlay(size=Window.size, pos=(0, 0))
        self.add_widget(self.overlay)
        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)

    def build_gui(self):
        # Floating GUI panel
        panel = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(220, 120),
            pos=(20, Window.height - 140),
            padding=16,
            spacing=8
        )
        with panel.canvas.before:
            Color(0.08, 0.08, 0.15, 0.92)
            self.panel_rect = Rectangle(
                pos=panel.pos,
                size=panel.size
            )

        title = Label(
            text='[b][color=00FFFF]ESP[/color][/b]',
            markup=True,
            font_size='20sp',
            size_hint_y=None,
            height=36
        )

        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        lbl = Label(
            text='[color=FFFFFF]Enable[/color]',
            markup=True,
            font_size='14sp'
        )
        self.toggle = Switch(active=False, size_hint_x=None, width=80)
        self.toggle.bind(active=self.on_toggle)

        row.add_widget(lbl)
        row.add_widget(self.toggle)
        panel.add_widget(title)
        panel.add_widget(row)
        self.add_widget(panel)

    def on_toggle(self, instance, value):
        self.esp_active = value
        self.overlay.esp_enabled = value
        if not value:
            self.overlay.update_boxes([])

    def update_frame(self, dt):
        if not self.esp_active:
            return
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return
        boxes = self.detector.detect(frame)
        self.overlay.update_boxes(boxes)

class ESPApp(App):
    def build(self):
        return ESPLayout()

if __name__ == '__main__':
    ESPApp().run()
