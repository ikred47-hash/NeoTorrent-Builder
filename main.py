import os
import time
import libtorrent as lt
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty
from kivy.uix.screenmanager import Screen, ScreenManager

# Register Android-specific intents if on mobile
if platform == 'android':
    from jnius import autoclass
    from android.activity import bind as android_bind

# --- UI DESIGN (Minimalist 2026) ---
KV = '''
<TorrentCard@BoxLayout>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(8)
    size_hint_y: None
    height: dp(140)
    canvas.before:
        Color:
            rgba: (0.15, 0.15, 0.15, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16),]

    Label:
        text: root.title
        font_size: '18sp'
        bold: True
        shorten: True
        shorten_from: 'right'
        text_size: self.width, None

    ProgressBar:
        max: 100
        value: root.progress
        size_hint_y: None
        height: dp(4)

    BoxLayout:
        size_hint_y: None
        height: dp(30)
        Label:
            text: str(int(root.progress)) + "%"
            font_size: '13sp'
            color: 0.7, 0.7, 0.7, 1
        Label:
            text: root.speed + " MB/s"
            halign: 'right'
            color: 0.3, 0.8, 0.3, 1

<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.08, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "NeoOnyx Fusion"
            font_size: '24sp'
            bold: True
            size_hint_y: None
            height: dp(40)
            halign: 'left'
            text_size: self.size

        # Search Bar
        TextInput:
            id: search_input
            hint_text: "Search or Paste Magnet Link..."
            multiline: False
            size_hint_y: None
            height: dp(50)
            padding: [dp(15), dp(15)]
            background_color: 0.15, 0.15, 0.15, 1
            foreground_color: 1, 1, 1, 1

        RecycleView:
            id: rv
            viewclass: 'TorrentCard'
            RecycleBoxLayout:
                default_size: None, dp(150)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                spacing: dp(15)

'''

class MainScreen(Screen):
    pass

class NeoOnyxApp(App):
    torrents_data = ListProperty([])

    def build(self):
        # 1. Initialize libtorrent session
        self.ses = lt.session()
        self.ses.listen_on(6881, 6891)
        
        # 2. Battery/Disk Optimization for Android 16
        settings = self.ses.get_settings()
        settings['download_rate_limit'] = 0
        settings['disk_io_write_mode'] = 2 # Disable OS cache to prevent system drain
        self.ses.apply_settings(settings)

        self.handles = []
        Builder.load_string(KV)
        sm = ScreenManager()
        self.main_screen = MainScreen(name='main')
        sm.add_widget(self.main_screen)
        
        # Update UI every second
        Clock.schedule_interval(self.update_status, 1)
        return sm

    def on_start(self):
        if platform == 'android':
            android_bind(on_new_intent=self.process_intent)
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = PythonActivity.mActivity.getIntent()
            self.process_intent(intent)

    def process_intent(self, intent):
        data = intent.getData()
        if data:
            link = data.toString()
            if link.startswith("magnet:"):
                self.add_torrent(link)

    def add_torrent(self, link):
        save_path = "/storage/emulated/0/Download"
        params = {'save_path': save_path}
        handle = lt.add_magnet_uri(self.ses, link, params)
        handle.set_sequential_download(True) # THE "ELITE" FEATURE
        self.handles.append(handle)

    def update_status(self, dt):
        ui_list = []
        for h in self.handles:
            s = h.status()
            ui_list.append({
                'title': s.name if s.name else "Fetching Metadata...",
                'progress': s.progress * 100,
                'speed': f"{s.download_rate / 1000000:.2f}"
            })
        self.main_screen.ids.rv.data = ui_list

if __name__ == '__main__':
    NeoOnyxApp().run()
