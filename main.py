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
import libtorrent as lt
import threading
import os

# --- 1. THEME (Dark Matter) ---
COLOR_BG = (0.05, 0.05, 0.07, 1)
COLOR_CARD = (0.12, 0.14, 0.18, 1)
COLOR_ACCENT = (0, 0.85, 1, 1)        # Neon Cyan
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

class TorrentCard(BoxLayout):
    def __init__(self, handle, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.handle = handle
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

        self.title_lbl = Label(text="Fetching...", font_size='16sp', bold=True, 
                               color=COLOR_TEXT_MAIN, halign='left', size_hint_y=None, height=dp(25),
                               shorten=True, shorten_from='right')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        self.add_widget(self.progress)

        stats = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(25))
        self.speed_lbl = Label(text="0 KB/s", color=COLOR_ACCENT, font_size='13sp', bold=True, halign='left')
        self.speed_lbl.bind(size=self.speed_lbl.setter('text_size'))
        self.state_lbl = Label(text="Starting...", color=COLOR_TEXT_SUB, font_size='12sp', halign='right')
        self.state_lbl.bind(size=self.state_lbl.setter('text_size'))
        stats.add_widget(self.speed_lbl)
        stats.add_widget(self.state_lbl)
        self.add_widget(stats)

        controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        
        stream_box = BoxLayout(orientation='horizontal', spacing=dp(5))
        stream_lbl = Label(text="Stream:", color=COLOR_TEXT_SUB, font_size='12sp')
        self.stream_switch = Switch(active=False)
        self.stream_switch.bind(active=self.toggle_sequential)
        stream_box.add_widget(stream_lbl)
        stream_box.add_widget(self.stream_switch)
        controls.add_widget(stream_box)

        del_btn = RoundedButton(text="DELETE", text_color=(1,1,1,1), btn_color=(0.8, 0.2, 0.2, 1), size_hint_x=0.4)
        del_btn.bind(on_press=self.delete_torrent)
        controls.add_widget(del_btn)
        self.add_widget(controls)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def toggle_sequential(self, instance, value):
        if self.handle.is_valid():
            self.handle.set_sequential_download(value)
            if value: self.handle.set_deadline(0, 1000) 

    def delete_torrent(self, instance):
        self.app.remove_torrent(self.handle, self)

class EmptyState(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(20)
        self.size_hint_y = None
        self.height = dp(400)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.add_widget(Label(text="[ NO TORRENTS ]", font_size='24sp', bold=True, color=COLOR_TEXT_SUB, size_hint_y=None, height=dp(50)))
        self.add_widget(Label(text="Tap + to add a magnet link", font_size='16sp', color=COLOR_TEXT_SUB, halign='center'))

class NeoOnyx(App):
    def build(self):
        self.cards = {}
        self.filter_mode = 'all'
        self.save_path = self.get_download_path()
        Window.clearcolor = COLOR_BG
        
        # --- ENGINE STARTUP ---
        self.ses = lt.session()
        self.ses.listen_on(6881, 6891)
        self.ses.apply_settings({'active_downloads': 10, 'enable_dht': True})

        if platform == 'android':
            Window.keep_screen_on = True
            from android.activity import bind as android_bind
            android_bind(on_new_intent=self.on_new_intent)

        self.root = FloatLayout()
        main_box = BoxLayout(orientation='vertical', padding=[dp(0), dp(50), dp(0), dp(0)])
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(20), 0, dp(20), 0])
        title = Label(text="NeoOnyx", font_size='26sp', bold=True, color=COLOR_ACCENT, halign='left')
        title.bind(size=title.setter('text_size'))
        
        settings_btn = Button(text="⚙", font_size='24sp', size_hint=(None, None), size=(dp(40), dp(40)),
                              background_color=(0,0,0,0), color=COLOR_TEXT_SUB)
        settings_btn.bind(on_press=self.show_settings)
        header.add_widget(title)
        header.add_widget(settings_btn)
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
        
        self.scroll.add_widget(self.list_layout)
        main_box.add_widget(self.scroll)
        self.root.add_widget(main_box)

        # FAB
        self.fab = RoundedButton(text="+", font_size='32sp', size_hint=(None, None), size=(dp(60), dp(60)), 
                                 pos_hint={'right': 0.95, 'y': 0.05}, btn_color=COLOR_ACCENT, radius=[dp(30)])
        self.fab.bind(on_press=self.show_add_popup)
        self.root.add_widget(self.fab)

        Clock.schedule_interval(self.update_loop, 1.0)
        return self.root

    def on_new_intent(self, intent):
        data = intent.getDataString()
        if data and "magnet:" in data: self.add_magnet(data)

    def get_download_path(self):
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                path = os.path.join(primary_external_storage_path(), 'Download')
                if not os.path.exists(path): os.makedirs(path)
                return path
            except: return self.user_data_dir 
        return os.path.join(os.path.expanduser("~"), "Downloads")

    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        self.link_input = TextInput(hint_text="Paste Magnet...", multiline=False, size_hint_y=None, height=dp(50),
                                    background_normal='', background_color=COLOR_INPUT_BG, 
                                    foreground_color=COLOR_TEXT_MAIN, cursor_color=COLOR_ACCENT)
        content.add_widget(self.link_input)
        add_btn = RoundedButton(text="ADD TORRENT", size_hint_y=None, height=dp(50), btn_color=(0, 0.8, 0, 1))
        add_btn.bind(on_press=lambda x: self.add_magnet(self.link_input.text))
        content.add_widget(add_btn)
        self.popup = Popup(title="New Torrent", title_color=COLOR_ACCENT, content=content, 
                           size_hint=(0.9, 0.4), separator_color=COLOR_ACCENT, background_color=COLOR_CARD)
        self.popup.open()

    def show_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text="Wi-Fi Only (Coming Soon)", color=COLOR_TEXT_SUB))
        content.add_widget(Switch(active=True, disabled=True))
        content.add_widget(Label(text="Dark Mode (Enabled)", color=COLOR_TEXT_SUB))
        content.add_widget(Switch(active=True, disabled=True))
        btn = RoundedButton(text="CLOSE", size_hint_y=None, height=dp(50))
        popup = Popup(title="Settings", title_color=COLOR_ACCENT, content=content, 
                      size_hint=(0.8, 0.5), separator_color=COLOR_ACCENT, background_color=COLOR_CARD)
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def add_magnet(self, link):
        link = link.strip().replace('"', '')
        if "magnet:" in link:
            try:
                if self.empty_state in self.list_layout.children:
                    self.list_layout.remove_widget(self.empty_state)
                params = {'save_path': self.save_path}
                handle = lt.add_magnet_uri(self.ses, link, params)
                card = TorrentCard(handle, self)
                self.list_layout.add_widget(card)
                self.cards[handle] = card
                if hasattr(self, 'popup'): self.popup.dismiss()
                self.refresh_list_visibility()
            except: pass

    def remove_torrent(self, handle, card):
        try: self.ses.remove_torrent(handle)
        except: pass
        self.list_layout.remove_widget(card)
        if handle in self.cards: del self.cards[handle]
        self.refresh_list_visibility()

    def refresh_list_visibility(self):
        visible_count = 0
        for handle, card in self.cards.items():
            should_show = False
            if self.filter_mode == 'all': should_show = True
            elif self.filter_mode == 'active' and not card.is_finished: should_show = True
            elif self.filter_mode == 'done' and card.is_finished: should_show = True
            
            if should_show:
                if card not in self.list_layout.children: self.list_layout.add_widget(card)
                visible_count += 1
            else:
                if card in self.list_layout.children: self.list_layout.remove_widget(card)
        
        if visible_count == 0:
            if self.empty_state not in self.list_layout.children: self.list_layout.add_widget(self.empty_state)
        else:
            if self.empty_state in self.list_layout.children: self.list_layout.remove_widget(self.empty_state)

    def update_loop(self, dt):
        for handle, card in list(self.cards.items()):
            try:
                if not handle.is_valid(): continue
                s = handle.status()
                if handle.has_metadata(): card.title_lbl.text = handle.get_torrent_info().name()
                card.progress.value = s.progress * 100
                is_done = (s.state == lt.torrent_status.seeding or s.progress >= 1.0)
                card.is_finished = is_done
                state_str = "Downloading"
                if is_done: state_str = "Done"
                elif s.state == lt.torrent_status.checking_files: state_str = "Checking"
                card.speed_lbl.text = f"{s.download_rate / 1000:.0f} KB/s"
                card.state_lbl.text = f"{state_str} | P: {s.num_peers}"
                if is_done: card.state_lbl.color = (0, 1, 0, 1)
            except: pass
        self.refresh_list_visibility()

if __name__ == '__main__':
    NeoOnyx().run()
