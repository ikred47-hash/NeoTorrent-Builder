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
import threading
import os
import traceback # To catch errors

# NOTE: We do NOT import requests here. We import it later.

# --- THEME ---
COLOR_BG = (0.05, 0.05, 0.07, 1)
COLOR_CARD = (0.12, 0.14, 0.18, 1)
COLOR_ACCENT = (0, 0.85, 1, 1)
COLOR_TEXT_MAIN = (1, 1, 1, 1)
COLOR_TEXT_SUB = (0.7, 0.7, 0.8, 1)
COLOR_INPUT_BG = (0.2, 0.22, 0.25, 1)

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

        self.title_lbl = Label(text=filename, font_size='16sp', bold=True, 
                               color=COLOR_TEXT_MAIN, halign='left', size_hint_y=None, height=dp(25),
                               shorten=True, shorten_from='right')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        self.add_widget(self.progress)

        stats = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(25))
        self.speed_lbl = Label(text="Initializing...", color=COLOR_ACCENT, font_size='13sp', bold=True, halign='left')
        self.speed_lbl.bind(size=self.speed_lbl.setter('text_size'))
        self.state_lbl = Label(text="0%", color=COLOR_TEXT_SUB, font_size='12sp', halign='right')
        self.state_lbl.bind(size=self.state_lbl.setter('text_size'))
        stats.add_widget(self.speed_lbl)
        stats.add_widget(self.state_lbl)
        self.add_widget(stats)

        controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        del_btn = RoundedButton(text="DELETE", text_color=(1,1,1,1), btn_color=(0.8, 0.2, 0.2, 1), size_hint_x=0.4)
        del_btn.bind(on_press=self.delete_download)
        controls.add_widget(del_btn)
        self.add_widget(controls)
        
        # Start Thread
        threading.Thread(target=self.start_download, daemon=True).start()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def start_download(self):
        try:
            # LAZY IMPORT: We import requests here so the app doesn't crash on launch if it's missing
            import requests
            
            path = os.path.join(self.app.save_path, self.filename)
            response = requests.get(self.url, stream=True, verify=False) # verify=False avoids SSL crashes
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
        except Exception as e:
            # PRINT ERROR TO SCREEN
            err_msg = str(traceback.format_exc())
            Clock.schedule_once(lambda dt: self.update_status("Error: " + str(e)))
            print(err_msg)

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

class EmptyState(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(20)
        self.size_hint_y = None
        self.height = dp(400)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        # FIXED: Removed Emoji, using text instead to prevent Font Crash
        self.add_widget(Label(text="[ NO FILES ]", font_size='24sp', bold=True, color=COLOR_TEXT_SUB, size_hint_y=None, height=dp(50)))
        self.add_widget(Label(text="Tap + to add a download", font_size='16sp', color=COLOR_TEXT_SUB, halign='center'))

class NeoSapphirePro(App):
    def build(self):
        self.filter_mode = 'all'
        self.save_path = self.get_download_path()
        Window.clearcolor = COLOR_BG
        
        self.root = FloatLayout()
        main_box = BoxLayout(orientation='vertical', padding=[dp(0), dp(50), dp(0), dp(0)])
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(20), 0, dp(20), 0])
        title = Label(text="NeoPro", font_size='26sp', bold=True, color=COLOR_ACCENT, halign='left')
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        main_box.add_widget(header)

        # Tabs
        tabs_box = BoxLayout(size_hint_y=None, height=dp(50), padding=[dp(10), 0])
        self.tab_all = TabButton(text="ALL", mode='all', app_ref=self, state='down')
        self.tab_dl = TabButton(text="ACTIVE", mode='active', app_ref=self)
        self.tab_done = TabButton(text="DONE", mode='done', app_ref=self)
        tabs_box.add_widget(self.tab_all)
        tabs_box.add_widget(self.tab_dl)
        tabs_box.add_widget(self.tab_done)
        main_box.add_widget(tabs_box)

        # List
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15), padding=dp(15))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        
        self.empty_state = EmptyState()
        self.list_layout.add_widget(self.empty_state)
        self.all_cards = []
        
        self.scroll.add_widget(self.list_layout)
        main_box.add_widget(self.scroll)
        self.root.add_widget(main_box)

        # FAB
        self.fab = RoundedButton(text="+", font_size='32sp', size_hint=(None, None), size=(dp(60), dp(60)), 
                                 pos_hint={'right': 0.95, 'y': 0.05}, btn_color=COLOR_ACCENT, radius=[dp(30)])
        self.fab.bind(on_press=self.show_add_popup)
        self.root.add_widget(self.fab)

        return self.root

    def get_download_path(self):
        # Fallback to internal storage if external fails permissions
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                path = os.path.join(primary_external_storage_path(), 'Download')
                if not os.path.exists(path): os.makedirs(path)
                return path
            except: 
                return self.user_data_dir # Safer fallback
        return os.path.join(os.path.expanduser("~"), "Downloads")

    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        self.link_input = TextInput(hint_text="Paste Link...", multiline=False, size_hint_y=None, height=dp(50),
                                    background_normal='', background_color=COLOR_INPUT_BG, 
                                    foreground_color=COLOR_TEXT_MAIN, cursor_color=COLOR_ACCENT)
        content.add_widget(self.link_input)
        add_btn = RoundedButton(text="DOWNLOAD", size_hint_y=None, height=dp(50), btn_color=(0, 0.8, 0, 1))
        add_btn.bind(on_press=self.add_download)
        content.add_widget(add_btn)
        self.popup = Popup(title="New Download", title_color=COLOR_ACCENT, content=content, 
                           size_hint=(0.9, 0.4), separator_color=COLOR_ACCENT, background_color=COLOR_CARD)
        self.popup.open()

    def add_download(self, instance):
        link = self.link_input.text.strip()
        if link:
            filename = link.split('/')[-1]
            if len(filename) > 25: filename = filename[-25:]
            card = DownloadCard(link, filename, self)
            self.all_cards.append(card)
            self.refresh_list_visibility()
            self.popup.dismiss()

    def remove_card(self, card):
        if card in self.all_cards: self.all_cards.remove(card)
        self.refresh_list_visibility()

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
