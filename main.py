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
from kivy.metrics import dp
import threading
import requests
import os

# --- 1. THEME COLORS (Cyberpunk / High Contrast) ---
COLOR_BG = (0.05, 0.05, 0.07, 1)      # Deep Black/Navy Background
COLOR_CARD = (0.12, 0.14, 0.18, 1)    # Dark Grey Card Background
COLOR_ACCENT = (0, 0.85, 1, 1)        # Neon Cyan Accent
COLOR_TEXT_MAIN = (1, 1, 1, 1)        # Pure White Text
COLOR_TEXT_SUB = (0.7, 0.7, 0.8, 1)   # Light Grey Subtext
COLOR_INPUT_BG = (0.2, 0.22, 0.25, 1) # Dark Input Box

# --- 2. CUSTOM UI COMPONENTS ---
class RoundedButton(Button):
    def __init__(self, btn_color=COLOR_ACCENT, text_color=(0,0,0,1), radius=[15], **kwargs):
        self.btn_color = btn_color
        self.radius = radius
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0,0,0,0)
        self.color = text_color
        self.bold = True
        self.font_size = '16sp'
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
        self.height = dp(120)  # Fixed height for each card
        self.padding = dp(15)
        self.spacing = dp(8)
        
        # Draw the Card Background
        with self.canvas.before:
            Color(rgba=COLOR_CARD)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)

        # 1. Filename Title
        self.title_lbl = Label(text=filename, font_size='16sp', bold=True, 
                               color=COLOR_TEXT_MAIN, halign='left', valign='middle',
                               size_hint_y=None, height=dp(25),
                               shorten=True, shorten_from='right')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        # 2. Progress Bar
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        self.add_widget(self.progress)

        # 3. Status Text (e.g., "Downloading: 45%")
        self.status_lbl = Label(text="Starting...", color=COLOR_ACCENT, font_size='12sp', 
                                halign='left', size_hint_y=None, height=dp(20))
        self.status_lbl.bind(size=self.status_lbl.setter('text_size'))
        self.add_widget(self.status_lbl)

        # Start the download automatically
        threading.Thread(target=self.start_download, daemon=True).start()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def start_download(self):
        try:
            path = os.path.join(self.app.save_path, self.filename)
            response = requests.get(self.url, stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None:
                with open(path, 'wb') as f:
                    f.write(response.content)
                self.update_status(100, "Done (Unknown Size)")
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
            Clock.schedule_once(lambda dt: self.update_status(0, "Error: Check Link"))

    def update_progress(self, val):
        self.progress.value = val
        self.status_lbl.text = f"Downloading: {val}%"

    def update_status(self, val, msg):
        self.progress.value = val
        self.status_lbl.text = msg
        if val == 100:
            self.status_lbl.color = (0, 1, 0, 1) # Turn text green when done

# --- 3. MAIN APP STRUCTURE ---
class NeoSapphire(App):
    def build(self):
        self.request_android_permissions()
        self.save_path = self.get_download_path()
        
        # Set the main background color for the whole screen
        Window.clearcolor = COLOR_BG 
        
        self.root = FloatLayout()

        # --- THE MAIN LAYOUT ---
        # Padding explanation: [Left, Top, Right, Bottom]
        # Top = dp(60) pushes content down so it doesn't hide behind the camera notch
        main_box = BoxLayout(orientation='vertical', padding=[dp(20), dp(60), dp(20), dp(20)], spacing=dp(20))
        
        # 1. HEADER SECTION
        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70))
        
        title = Label(text="NeoSapphire", font_size='32sp', bold=True, 
                      color=COLOR_ACCENT, halign='left', valign='bottom')
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        
        subtitle = Label(text="Direct Stream Accelerator", font_size='14sp', 
                         color=COLOR_TEXT_SUB, halign='left', valign='top')
        subtitle.bind(size=subtitle.setter('text_size'))
        header.add_widget(subtitle)
        
        main_box.add_widget(header)

        # 2. SCROLLABLE LIST (Where downloads appear)
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        main_box.add_widget(self.scroll)
        
        self.root.add_widget(main_box)

        # 3. FLOATING ACTION BUTTON (The "+" Button)
        self.fab = RoundedButton(text="+", font_size='32sp', text_color=(1,1,1,1),
                                 size_hint=(None, None), size=(dp(65), dp(65)), 
                                 pos_hint={'right': 0.95, 'y': 0.05}, 
                                 btn_color=COLOR_ACCENT, radius=[dp(32)])
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
        # A clean, styled popup for adding links
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # STYLED INPUT BOX (Fixed the white-on-white issue)
        self.link_input = TextInput(
            hint_text="Paste Link (MP4, Zip, etc)...", 
            multiline=False, 
            size_hint_y=None, 
            height=dp(50),
            background_normal='', # Removes the default ugly border
            background_color=COLOR_INPUT_BG,
            foreground_color=COLOR_TEXT_MAIN, # White text when typing
            cursor_color=COLOR_ACCENT,
            hint_text_color=(0.5, 0.5, 0.5, 1),
            padding_y=dp(15), # Centers text vertically
            padding_x=dp(15)
        )
        content.add_widget(self.link_input)
        
        # STYLED CONFIRM BUTTON
        add_btn = RoundedButton(text="START DOWNLOAD", text_color=(1,1,1,1),
                                size_hint_y=None, height=dp(50), 
                                btn_color=(0, 0.8, 0, 1), # Green button
                                radius=[10])
        add_btn.bind(on_press=self.add_download)
        content.add_widget(add_btn)
        
        self.popup = Popup(title="New Download", 
                           title_color=COLOR_ACCENT,
                           content=content, 
                           size_hint=(0.9, 0.4),
                           separator_color=COLOR_ACCENT,
                           background_color=COLOR_CARD) # Dark popup background
        self.popup.open()

    def add_download(self, instance):
        link = self.link_input.text.strip()
        if link:
            filename = link.split('/')[-1]
            if len(filename) > 25: filename = filename[-25:]
            card = DownloadCard(link, filename, self)
            self.list_layout.add_widget(card)
            self.popup.dismiss()

if __name__ == '__main__':
    NeoSapphire().run()
