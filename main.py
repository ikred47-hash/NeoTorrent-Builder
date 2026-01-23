from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp
import requests  # <--- This matches your buildozer.spec
import threading
import os

# --- 1. THEME (Dark Matter) ---
COLOR_BG = (0.05, 0.05, 0.07, 1)
COLOR_CARD = (0.12, 0.14, 0.18, 1)
COLOR_ACCENT = (0, 0.85, 1, 1)
COLOR_TEXT_MAIN = (1, 1, 1, 1)
COLOR_TEXT_SUB = (0.7, 0.7, 0.8, 1)
COLOR_INPUT_BG = (0.2, 0.22, 0.25, 1)

# --- 2. COMPONENTS ---
class RoundedButton(Button):
    def __init__(self, btn_color=COLOR_ACCENT, text_color=(0,0,0,1), radius=[10], **kwargs):
        self.btn_color = btn_color
        self.radius = radius
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0,0,0,0)
        self.color = text_color
        self.bold = True
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=self.btn_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

class TabButton(ToggleButton):
    def __init__(self, text, mode, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.mode = mode
        self.app = app_ref
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0,0,0,0)
        self.group = 'tabs'
        self.bold = True
        self.color = COLOR_TEXT_SUB
        self.bind(state=self.on_state, pos=self.update_canvas, size=self.update_canvas)
        self.bind(on_press=self.set_filter)

    def on_state(self, instance, value):
        self.color = COLOR_ACCENT if value == 'down' else COLOR_TEXT_SUB
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(rgba=COLOR_ACCENT)
                RoundedRectangle(pos=(self.x, self.y), size=(self.width, dp(3)), radius=[1])
    
    def set_filter(self, instance):
        self.app.filter_mode = self.mode
        self.app.refresh_list_visibility()

class DownloadCard(BoxLayout):
    def __init__(self, url, filename, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.filename = filename
        self.app = app_ref
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(150)
        self.padding = dp(15)
        self.spacing = dp(5)
        self.is_finished = False 
        
        with self.canvas.before:
            Color(rgba=COLOR_CARD)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Title
        self.title_lbl = Label(text=filename, font_size='16sp', bold=True, 
                               color=COLOR_TEXT_MAIN, halign='left', size_hint_y=None, height=dp(25),
                               shorten=True, shorten_from='right')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        # Progress
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        self.add_widget(self.progress)

        # Stats
        stats = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(25))
        self.speed_lbl = Label(text="Downloading...", color=COLOR_ACCENT, font_size='13sp', bold=True, halign='left')
        self.speed_lbl.bind(size=self.speed_lbl.setter('text_size'))
        self.state_lbl = Label(text="0%", color=COLOR_TEXT_SUB, font_size='12sp', halign='right')
        self.state_lbl.bind(size=self.state_lbl.setter('text_size'))
        stats.add_widget(self.speed_lbl)
        stats.add_widget(self.state_lbl)
        self.add_widget(stats)

        # Controls
        controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        
        # Stream Toggle
        stream_box = BoxLayout(orientation='horizontal', spacing=dp(5))
        stream_lbl = Label(text="Stream:", color=COLOR_TEXT_SUB, font_size='12sp')
        self.stream_switch = Switch(active=False)
        stream_box.add_widget(stream_lbl)
        stream_box.add_widget(self.stream_switch)
        controls.add_widget(stream_box)

        # Delete Button
        del_btn = RoundedButton(text="DELETE", text_color=(1,1,1,1), btn_color=(0.8, 0.2, 0.2, 1), size_hint_x=0.4)
        del_btn.bind(on_press=self.delete_download)
        controls.add_widget(del_btn)
        self.add_widget(controls)
        
        # Start Download
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
                with open(path, 'wb') as f: f.write(response.content)
                self.finish_download()
            else:
                dl = 0
                total_length = int(total_length)
                with open(path, 'wb') as f:
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)
                        Clock.schedule_once(lambda dt, p=done: self.update_progress(p))
                self.finish_download()
        except:
            Clock.schedule_once(lambda dt: self.update_status("Error"))

    def update_progress(self, val):
        self.progress.value = val
        self.state_lbl.text = f"{val}%"

    def finish_download(self):
        self.is_finished = True
        Clock.schedule_once(lambda dt: self.update_status("Done"))
        Clock.schedule_once(lambda dt: self.app.refresh_list_visibility())

    def update_status(self, msg):
        self.speed_lbl.text = msg
        if msg == "Done":
            self.state_lbl.color = (0, 1, 0, 1)
            self.state_lbl.text = "Completed"

    def delete_download(self, instance):
        self.app.remove_card(self)

    def remove_card(self, card):
        if card in self.app.all_cards:
            self.app.all_cards.remove(card)
        self.app.refresh_list_visibility()

class EmptyState(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(20)
        self.size_hint_y = None
        self.height = dp(400)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.add_widget(Label(text="📦", font_size='80sp', size_hint_y=None, height=dp(100)))
        self.add_widget(Label(text="No downloads in this tab.", font_size='16sp', color=COLOR_TEXT_SUB, halign='center'))

class NeoSapphirePro(App):
    def build(self):
        self.filter_mode = 'all' # options: 'all', 'active', 'done'
        self.save_path = self.get_download_path()
        Window.clearcolor = COLOR_BG
        
        self.root = FloatLayout()
        
        # PADDING FIX
        main_box = BoxLayout(orientation='vertical', padding=[dp(0), dp(50), dp(0), dp(0)])
        
        # 1. HEADER
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(20), 0, dp(20), 0])
        title = Label(text="NeoPro", font_size='26sp', bold=True, color=COLOR_ACCENT, halign='left')
        title.bind(size=title.setter('text_size'))
        
        settings_btn = Button(text="⚙", font_size='24sp', size_hint=(None, None), size=(dp(40), dp(40)),
                              background_color=(0,0,0,0), color=COLOR_TEXT_SUB)
        settings_btn.bind(on_press=self.show_settings)
        
        header.add_widget(title)
        header.add_widget(settings_btn)
        main_box.add_widget(header)

        # 2. TABS
        tabs_box = BoxLayout(size_hint_y=None, height=dp(50), padding=[dp(10), 0])
        self.tab_all = TabButton(text="ALL", mode='all', app_ref=self, state='down')
        self.tab_dl = TabButton(text="ACTIVE", mode='active', app_ref=self)
        self.tab_done = TabButton(text="DONE", mode='done', app_ref=self)
        
        tabs_box.add_widget(self.tab_all)
        tabs_box.add_widget(self.tab_dl)
        tabs_box.add_widget(self.tab_done)
        main_box.add_widget(tabs_box)

        # 3. LIST
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15), padding=dp(15))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        
        self.empty_state = EmptyState()
        self.list_layout.add_widget(self.empty_state)
        self.all_cards = []
        
        self.scroll.add_widget(self.list_layout)
        main_box.add_widget(self.scroll)
        self.root.add_widget(main_box)

        # 4. FAB
        self.fab = RoundedButton(text="+", font_size='32sp', size_hint=(None, None), size=(dp(60), dp(60)), 
                                 pos_hint={'right': 0.95, 'y': 0.05}, btn_color=COLOR_ACCENT, radius=[dp(30)])
        self.fab.bind(on_press=self.show_add_popup)
        self.root.add_widget(self.fab)

        return self.root

    def get_download_path(self):
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                return os.path.join(primary_external_storage_path(), 'Download')
            except: return os.path.expanduser("~") 
        return os.path.join(os.path.expanduser("~"), "Downloads")

    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        self.link_input = TextInput(hint_text="Paste Link (MP4/Zip)...", multiline=False, size_hint_y=None, height=dp(50),
                                    background_normal='', background_color=COLOR_INPUT_BG, 
                                    foreground_color=COLOR_TEXT_MAIN, cursor_color=COLOR_ACCENT,
                                    hint_text_color=(0.5, 0.5, 0.5, 1))
        content.add_widget(self.link_input)
        add_btn = RoundedButton(text="DOWNLOAD", size_hint_y=None, height=dp(50), btn_color=(0, 0.8, 0, 1))
        add_btn.bind(on_press=self.add_download)
        content.add_widget(add_btn)
        self.popup = Popup(title="New Download", title_color=COLOR_ACCENT, content=content, 
                           size_hint=(0.9, 0.4), separator_color=COLOR_ACCENT, background_color=COLOR_CARD)
        self.popup.open()

    def show_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text="Wi-Fi Only", color=COLOR_TEXT_SUB))
        content.add_widget(Switch(active=True))
        content.add_widget(Label(text="Dark Mode", color=COLOR_TEXT_SUB))
        content.add_widget(Switch(active=True))
        
        btn = RoundedButton(text="CLOSE", size_hint_y=None, height=dp(50))
        popup = Popup(title="Settings", title_color=COLOR_ACCENT, content=content, 
                      size_hint=(0.8, 0.5), separator_color=COLOR_ACCENT, background_color=COLOR_CARD)
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def add_download(self, instance):
        link = self.link_input.text.strip()
        if link:
            filename = link.split('/')[-1]
            if len(filename) > 25: filename = filename[-25:]
            card = DownloadCard(link, filename, self)
            self.all_cards.append(card)
            self.refresh_list_visibility()
            self.popup.dismiss()

    def refresh_list_visibility(self):
        visible_count = 0
        self.list_layout.clear_widgets()
        for card in self.all_cards:
            should_show = False
            if self.filter_mode == 'all': should_show = True
            elif self.filter_mode == 'active' and not card.is_finished: should_show = True
            elif self.filter_mode == 'done' and card.is_finished: should_show = True
            if should_show:
                self.list_layout.add_widget(card)
                visible_count += 1
        if visible_count == 0:
            self.list_layout.add_widget(self.empty_state)

if __name__ == '__main__':
    NeoSapphirePro().run()
