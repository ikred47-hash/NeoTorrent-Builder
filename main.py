from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import platform
from kivy.core.window import Window
import threading
import requests
import os

# --- UI COMPONENTS (DIAMOND STYLE) ---
class RoundedButton(Button):
    def __init__(self, btn_color=(0.1, 0.6, 1, 1), radius=[10], **kwargs):
        self.btn_color = btn_color
        self.radius = radius
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0,0,0,0)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=self.btn_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

class DownloadCard(BoxLayout):
    def __init__(self, url, filename, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.filename = filename
        self.app = app_ref
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 120
        self.padding = 15
        self.spacing = 8
        
        with self.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.title_lbl = Label(text=filename, font_size='15sp', bold=True, 
                               halign='left', size_hint_y=None, height=30,
                               shorten=True, shorten_from='right')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=6)
        self.add_widget(self.progress)

        stats = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        self.status_lbl = Label(text="Starting...", color=(0, 0.9, 1, 1), font_size='13sp', bold=True)
        stats.add_widget(self.status_lbl)
        self.add_widget(stats)

        # Start Download Thread
        threading.Thread(target=self.start_download, daemon=True).start()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def start_download(self):
        try:
            path = os.path.join(self.app.save_path, self.filename)
            response = requests.get(self.url, stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None: # No content length header
                with open(path, 'wb') as f:
                    f.write(response.content)
                self.update_status(100, "Done (No Size Data)")
            else:
                dl = 0
                total_length = int(total_length)
                with open(path, 'wb') as f:
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)
                        Clock.schedule_once(lambda dt, p=done: self.update_progress(p))
                Clock.schedule_once(lambda dt: self.update_status(100, "Download Complete"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(0, "Error"))

    def update_progress(self, val):
        self.progress.value = val
        self.status_lbl.text = f"Downloading: {val}%"

    def update_status(self, val, msg):
        self.progress.value = val
        self.status_lbl.text = msg
        if val == 100:
            self.status_lbl.color = (0, 1, 0, 1)

class NeoSapphire(App):
    def build(self):
        self.request_android_permissions()
        self.save_path = self.get_download_path()
        
        self.root = FloatLayout()
        with self.root.canvas.before:
            Color(0, 0, 0, 1)
            RoundedRectangle(pos=(0,0), size=(3000, 3000))

        main_box = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(size_hint_y=None, height=100, orientation='vertical', padding=20)
        title = Label(text="NeoSapphire", font_size='26sp', bold=True, color=(0, 0.8, 1, 1), halign='left')
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        sub = Label(text="Direct Stream Accelerator", font_size='14sp', color=(0.6, 0.6, 0.6, 1), halign='left')
        sub.bind(size=sub.setter('text_size'))
        header.add_widget(sub)
        main_box.add_widget(header)

        # List Area
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=10)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        main_box.add_widget(self.scroll)
        self.root.add_widget(main_box)

        # FAB
        self.fab = RoundedButton(text="+", font_size='35sp', size_hint=(None, None), size=(70, 70), 
                                 pos_hint={'right': 0.95, 'y': 0.04}, btn_color=(0, 0.7, 1, 1), radius=[35])
        self.fab.bind(on_press=self.show_add_popup)
        self.root.add_widget(self.fab)

        return self.root

    def request_android_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    def get_download_path(self):
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                return os.path.join(primary_external_storage_path(), 'Download')
            except: return os.path.expanduser("~") 
        return os.path.join(os.path.expanduser("~"), "Downloads")

    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.link_input = TextInput(hint_text="Paste Direct Link (MP4/Zip)...", multiline=False, size_hint_y=None, height=50)
        content.add_widget(self.link_input)
        add_btn = RoundedButton(text="START DOWNLOAD", size_hint_y=None, height=50, btn_color=(0, 0.8, 0, 1))
        add_btn.bind(on_press=self.add_download)
        content.add_widget(add_btn)
        self.popup = Popup(title="Add Link", content=content, size_hint=(0.9, 0.35))
        self.popup.open()

    def add_download(self, instance):
        link = self.link_input.text.strip()
        if link:
            filename = link.split('/')[-1]
            if len(filename) > 20: filename = filename[-20:]
            card = DownloadCard(link, filename, self)
            self.list_layout.add_widget(card)
            self.popup.dismiss()

if __name__ == '__main__':
    NeoSapphire().run()
