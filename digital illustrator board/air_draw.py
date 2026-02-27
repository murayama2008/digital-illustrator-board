import cv2
import mediapipe as mp
import math
import customtkinter as ctk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk
import numpy as np


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AirDrawApp:

    def __init__(self, root):
        self.root = root
        self.root.title("digital illustrator board by joekenn.mp4")
        self.root.geometry("1100x700")

        self.cap = cv2.VideoCapture(0)

        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        self.prev_x = None
        self.prev_y = None
        self.drawing = False
        self.brush_size = 5
        self.draw_color = (0, 0, 255)

        #layout
        self.main_frame = ctk.CTkFrame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self.main_frame, width=250)
        self.sidebar.pack(side="left", fill="y")

        self.video_frame = ctk.CTkFrame(self.main_frame)
        self.video_frame.pack(side="right", fill="both", expand=True)

        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        self.video_label.pack(expand=True)

        #UI
        ctk.CTkLabel(self.sidebar, text="digital illustrator board by joekenn.mp4", font=("Arial", 22)).pack(pady=20)

        self.clear_btn = ctk.CTkButton(self.sidebar, text="Clear Canvas", command=self.clear)
        self.clear_btn.pack(pady=10, fill="x", padx=20)

        self.save_btn = ctk.CTkButton(self.sidebar, text="Save Image", command=self.save)
        self.save_btn.pack(pady=10, fill="x", padx=20)

        self.color_btn = ctk.CTkButton(self.sidebar, text="Pick Color", command=self.pick_color)
        self.color_btn.pack(pady=10, fill="x", padx=20)

        ctk.CTkLabel(self.sidebar, text="Brush Size").pack(pady=(30, 5))
        self.size_slider = ctk.CTkSlider(self.sidebar, from_=1, to=20,
                                         command=self.change_brush)
        self.size_slider.set(5)
        self.size_slider.pack(padx=20, fill="x")

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Idle")
        self.status_label.pack(side="bottom", pady=20)

        self.draw_layer = None
        self.current_frame = None

        self.update()

    def clear(self):
        if self.draw_layer is not None:
            self.draw_layer[:] = 0

    def save(self):
        file = filedialog.asksaveasfilename(defaultextension=".png")
        if file and self.current_frame is not None:
            cv2.imwrite(file, self.current_frame)

    def pick_color(self):
        color = colorchooser.askcolor()[0]
        if color:
            self.draw_color = (int(color[2]), int(color[1]), int(color[0]))

    def change_brush(self, value):
        self.brush_size = int(value)

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        if self.draw_layer is None:
            self.draw_layer = np.zeros_like(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            self.mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS
            )

            index_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]

            x = int(index_tip.x * w)
            y = int(index_tip.y * h)
            thumb_x = int(thumb_tip.x * w)
            thumb_y = int(thumb_tip.y * h)

            cv2.circle(frame, (x, y), 6, (0, 255, 255), -1)

            distance = math.hypot(x - thumb_x, y - thumb_y)

            if distance < 40:
                self.drawing = True
                self.status_label.configure(text="Status: Drawing")
            else:
                self.drawing = False
                self.prev_x, self.prev_y = None, None
                self.status_label.configure(text="Status: Idle")

            if self.drawing:
                if self.prev_x is not None:
                    cv2.line(
                        self.draw_layer,
                        (self.prev_x, self.prev_y),
                        (x, y),
                        self.draw_color,
                        self.brush_size
                    )
                self.prev_x, self.prev_y = x, y

        combined = cv2.add(frame, self.draw_layer)
        self.current_frame = combined.copy()

        img = Image.fromarray(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)

        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        self.root.after(10, self.update)


root = ctk.CTk()
app = AirDrawApp(root)
root.mainloop()