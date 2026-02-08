import os
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
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp
import random
import requests

# --- SAFE IMPORT: Torrent Engine ---
try:
    import libtorrent as lt
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

# --- THEME (Cyber-Onyx) ---
COLOR_BG = (0.05, 0.05, 0.07, 1)
COLOR_CARD = (0.12, 0.14, 0.18, 1)
COLOR_ACCENT_BLUE = (0, 0.85, 1, 1)     # Network
COLOR_ACCENT_PURPLE = (0.7, 0, 1, 1)    # Neural
COLOR_TEXT_MAIN = (1, 1, 1, 1)
COLOR_TEXT_SUB = (0.7, 0.7, 0.8, 1)

class RoundedButton(Button):
    def __init__(self, btn_color=COLOR_ACCENT_BLUE, radius=[10], **kwargs):
        self.btn_color = btn_color
        self.radius = radius
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0,0,0,0)
        self.bold = True
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        if not self.canvas: return
        if self.pos[1] < 1: return
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=self.btn_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

class NavButton(ToggleButton):
    def __init__(self, text, icon, app_ref, mode, **kwargs):
        self.app = app_ref
        self.mode = mode
        super().__init__(**kwargs)
        self.text = f"{icon}  {text}"
        self.group = 'nav'
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0,0,0,0)
        self.allow_no_selection = False
        self.bind(state=self.on_state, pos=self.update_canvas, size=self.update_canvas)
        if self.state == 'down':
            self.on_state(self, 'down')

    def on_state(self, instance, value):
        if value == 'down':
            self.app.switch_tab(self.mode)
            self.color = COLOR_ACCENT_BLUE if self.mode == 'network' else COLOR_ACCENT_PURPLE
        else:
            self.color = COLOR_TEXT_SUB
        self.update_canvas()

    def update_canvas(self, *args):
        if not self.canvas: return
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(rgba=self.color)
                RoundedRectangle(pos=(self.x + dp(20), self.y), size=(self.width - dp(40), dp(2)), radius=[1])

class TorrentCard(BoxLayout):
    def __init__(self, handle, **kwargs):
        super().__init__(**kwargs)
        self.handle = handle
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(110)
        self.padding = dp(15)
        with self.canvas.before:
            Color(rgba=COLOR_CARD)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.title_lbl = Label(text="Initializing...", bold=True, halign='left', size_hint_y=None, height=dp(25))
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        self.add_widget(self.progress)

        self.stats_lbl = Label(text="0 KB/s", color=COLOR_ACCENT_BLUE, font_size='12sp', halign='left')
        self.stats_lbl.bind(size=self.stats_lbl.setter('text_size'))
        self.add_widget(self.stats_lbl)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class NeuralPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(15)
        
        self.image_display = AsyncImage(source='', allow_stretch=True, keep_ratio=True)
        self.image_display.bind(on_load=self.on_image_loaded)
        self.add_widget(self.image_display)

        self.status_lbl = Label(text="[ NPU STANDBY ]", color=COLOR_TEXT_SUB, size_hint_y=None, height=dp(40))
        self.add_widget(self.status_lbl)

        self.prompt_in = TextInput(hint_text="Describe your dream...", multiline=False, size_hint_y=None, height=dp(50),
                                   background_color=(0.18, 0.18, 0.2, 1), foreground_color=(1,1,1,1))
        self.add_widget(self.prompt_in)

        self.gen_btn = RoundedButton(text="DREAM (Snapdragon 8s Gen 4)", btn_color=COLOR_ACCENT_PURPLE, size_hint_y=None, height=dp(60))
        self.gen_btn.bind(on_press=self.generate_ai)
        self.add_widget(self.gen_btn)

    def generate_ai(self, instance):
        if not self.prompt_in.text: return
        instance.disabled = True
        self.status_lbl.text = "⚡ TRANSMITTING PROMPT ⚡"
        seed = random.randint(1, 99999)
        safe_prompt = requests.utils.quote(self.prompt_in.text)
        self.image_display.source = f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&seed={seed}"

    def on_image_loaded(self, instance):
        self.gen_btn.disabled = False
        self.status_lbl.text = "[ DREAM REALIZED ]"

class NeoOnyx(App):
    def build(self):
        Window.clearcolor = COLOR_BG
        Window.softinput_mode = 'pan'
        self.root = FloatLayout()
        
        self.content_area = BoxLayout(padding=[0, 0, 0, dp(60)])
        self.root.add_widget(self.content_area)

        nav_bar = BoxLayout(size_hint_y=None, height=dp(60), pos_hint={'y': 0})
        with nav_bar.canvas.before:
            Color(rgba=COLOR_CARD)
            self.nav_bg_rect = Rectangle(pos=nav_bar.pos, size=nav_bar.size)
        nav_bar.bind(pos=self.update_nav_bg, size=self.update_nav_bg)
        
        self.screen_network = BoxLayout(orientation='vertical')
        self.init_network_ui()
        self.screen_neural = NeuralPanel()

        self.btn_net = NavButton("NETWORK", "⬇", self, 'network', state='down')
        self.btn_neu = NavButton("NEURAL", "🧠", self, 'neural')
        nav_bar.add_widget(self.btn_net)
        nav_bar.add_widget(self.btn_neu)
        self.root.add_widget(nav_bar)

        self.cards = {}
        if ENGINE_AVAILABLE:
            self.ses = lt.session()
            self.ses.listen_on(6881, 6891)
            Clock.schedule_interval(self.update_loop, 1.0)

        return self.root

    def update_nav_bg(self, i, v):
        self.nav_bg_rect.pos = i.pos
        self.nav_bg_rect.size = i.size

    def init_network_ui(self):
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(15))
        header.add_widget(Label(text="NeoOnyx Engine", font_size='22sp', bold=True, color=COLOR_ACCENT_BLUE))
        add_btn = RoundedButton(text="+", size_hint=(None, None), size=(dp(45), dp(45)))
        add_btn.bind(on_press=self.show_add_popup)
        header.add_widget(add_btn)
        self.screen_network.add_widget(header)
        
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(10))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        self.screen_network.add_widget(self.scroll)

    def switch_tab(self, mode):
        self.content_area.clear_widgets()
        self.content_area.add_widget(self.screen_network if mode == 'network' else self.screen_neural)

    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        link_in = TextInput(hint_text="Magnet Link...", multiline=False, size_hint_y=None, height=dp(50))
        content.add_widget(link_in)
        go_btn = RoundedButton(text="START DOWNLOAD")
        go_btn.bind(on_press=lambda x: self.add_magnet(link_in.text))
        content.add_widget(go_btn)
        self.popup = Popup(title="Add Torrent", content=content, size_hint=(0.9, 0.4))
        self.popup.open()

    def add_magnet(self, link):
        if ENGINE_AVAILABLE and "magnet:" in link:
            params = {'save_path': '/storage/emulated/0/Download'}
            handle = lt.add_magnet_uri(self.ses, link, params)
            card = TorrentCard(handle)
            self.list_layout.add_widget(card)
            self.cards[handle] = card
            self.popup.dismiss()

    def update_loop(self, dt):
        for handle, card in list(self.cards.items()):
            s = handle.status()
            if handle.has_metadata(): card.title_lbl.text = handle.get_torrent_info().name()
            card.progress.value = s.progress * 100
            card.stats_lbl.text = f"{s.download_rate / 1000:.1f} KB/s | Seeds: {s.num_seeds}"

if __name__ == '__main__':
    NeoOnyx().run()
