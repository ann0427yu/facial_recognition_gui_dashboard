import socket
import requests
import subprocess
import csv
import datetime
import os
import pyttsx3
import threading
import tkinter as tk
import cv2
from deepface import DeepFace
from PIL import Image, ImageTk
import util
from sympy import public
from tensorflow.python.lib.io.file_io import file_exists
from torch.backends.quantized import engine
from urllib3.filepost import writer

class App:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.geometry("1200x520+350+100")
        self.main_window.title("TalentCorp Malaysia Berhad- Attendance System")
        self.bg_image_path = "background14.png"
        bg_img = Image.open(self.bg_image_path)
        bg_img = bg_img.resize((1200,520))
        self.bg_tk = ImageTk.PhotoImage(bg_img)

        self.bg_label = tk.Label(self.main_window, image= self.bg_tk)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.login_button_main_window = util.get_button(self.main_window, 'Login','#aac1b1', self.login, fg='white')
        self.login_button_main_window.place(x=800, y=220)

        self.register_new_user_button_main_window = util.get_button(self.main_window, 'Register New User', '#8e93b2',
                                                                    self.register_new_user, fg='white')
        self.register_new_user_button_main_window.place(x=800, y=350)

        self.webcam_label = util.get_img_label(self.main_window)
        self.webcam_label.place(x=20, y=20, width=650, height=450)

        self.add_webcam(self.webcam_label)

        self.db_dir = './Documents'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

        self.engine = pyttsx3.init("sapi5")
        self.engine.setProperty('rate', 180)
        self.engine.setProperty('volume', 1.0)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id)

    def get_ip_address(self):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            response = requests.get('http://ipinfo.io/json/')
            geo_info = response.json()
            public_ip = geo_info.get('ip', 'Uknown')
            location = geo_info.get('city', 'Unknown') + "," + geo_info.get('region', 'Unknown')
            return local_ip, public_ip, location
        except Exception as e:
            print(f"Error IP or location:{e}")
            return "Unknown", "Unknown", "Unknown"

    def speak_text(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def add_webcam(self, label):
        if 'cap' not in self.__dict__:
            self.cap = cv2.VideoCapture(0)

        self._label = label
        self.process_webcam()

    def process_webcam(self):
        ret, frame = self.cap.read()
        self.most_recent_capture_arr = frame
        img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB)
        self.most_recent_capture_pil = Image.fromarray(img_)
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)

        self._label.after(20, self.process_webcam)


    def login(self):
        local_ip,public_ip,location = self.get_ip_address()
        unknown_img_path = './.tmp.jpg'
        cv2.imwrite(unknown_img_path, self.most_recent_capture_arr)

        best_match = None
        lowest_distance = float('inf')
        threshold = 0.45
        csv_file = "attendance_records.csv"

        for img_name in os.listdir(self.db_dir):
            db_img_path = os.path.join(self.db_dir, img_name)

            try:
                result = DeepFace.verify(unknown_img_path, db_img_path, model_name='ArcFace', distance_metric='cosine')

                print(f"Comparing with {img_name}: Distance = {result['distance']} (Threshold = {threshold})")

                if result["distance"] < lowest_distance:
                    lowest_distance = result["distance"]
                    best_match = img_name

            except Exception as e:
                print(f"Error processing {img_name}: {e}")

        os.remove(unknown_img_path)

        if best_match and lowest_distance < threshold:
            username = best_match.split('.')[0]
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Determine work mode based on location
            work_mode = "Work From Home (WFH)"
            if local_ip == "192.168.18.27" or local_ip == "211.25.11.23":
                work_mode = "Work From Office (WFO)"

            file_exists = os.path.exists(csv_file)
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Date", "Name", "Time", "Work Mode", "Location","Local IP"])
                writer.writerow(
                    [current_time.split()[0], username, current_time.split()[1], work_mode,location,local_ip])

            util.msg_box("Login Successful", f"Welcome {username}")
            print(f"Login successful! Matched with {best_match} at {location}")

            t = threading.Thread(target=self.speak_text, args=("Attendance taken, have a nice day!",))
            t.start()

        else:
            util.msg_box("Login Failed", "No match found!")
            print("Login failed! No match found.")

    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x520+370+120")

        self.accept_button_main_window = util.get_button(self.register_new_user_window, 'Accept', '#aac1b1', self.accept_register_new_user)
        self.accept_button_main_window.place(x=765, y=300)

        self.try_again_button_main_window = util.get_button(self.register_new_user_window, 'Try Again', '#8e93b2',
                                                         self.try_again_register_new_user)
        self.try_again_button_main_window.place(x=765, y=400)

        self.capture_label = util.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)

        self.add_img_to_label(self.capture_label)

        self.entry_text_register_new_user = util.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user.place(x=750, y=150)

        self.text_label_register_new_user = util.get_text_label(self.register_new_user_window, "Welcome to TalentCorp!\nPlease input your username:")
        self.text_label_register_new_user.place(x=750, y=70)

    def try_again_register_new_user(self):
        self.register_new_user_window.destroy()

    def add_img_to_label(self, label):
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        self.register_new_user_capture = self.most_recent_capture_arr.copy()


    def start(self):
        self.main_window.mainloop()

    def accept_register_new_user(self):
        name = self.entry_text_register_new_user.get(1.0, "end-1c").strip()

        if hasattr(self, "register_new_user_capture"):
            filename = os.path.join(self.db_dir, '{}.jpg'.format(name))
            cv2.imwrite(filename, self.register_new_user_capture)
            print(f"Image saved as {filename}")
        else:
            print("Error: No image captured!")

        util.msg_box("Success!","User register successfully!")

        self.register_new_user_window.destroy()


if __name__ == "__main__":
    app = App()
    app.start()
