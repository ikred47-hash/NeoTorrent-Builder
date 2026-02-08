import os
import libtorrent as lt
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager

if platform == 'android':
    from jnius import autoclass
    from android.activity import bind as android_bind

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

        TextInput:
            id: search_input
            hint_text: "Paste Magnet Link..."
            multiline: False
            size_hint_y: None
            height: dp(50)
            padding: [dp(15), dp(15)]
            background_color: 0.15, 0.15, 0.15, 1
            foreground_color: 1, 1, 1, 1
            on_text_validate: app.add_torrent(self.text); self.text = ""

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
    def build(self):
        self.ses = lt.session()
        self.ses.listen_on(6881, 6891)
        settings = self.ses.get_settings()
        settings['disk_io_write_mode'] = 2 
        self.ses.apply_settings(settings)

        self.handles = []
        Builder.load_string(KV)
        sm = ScreenManager()
        self.main_screen = MainScreen(name='main')
        sm.add_widget(self.main_screen)
        
        Clock.schedule_interval(self.update_status, 1)
        return sm

    def on_start(self):
        if platform == 'android':
            android_bind(on_new_intent=self.process_intent)
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.process_intent(PythonActivity.mActivity.getIntent())

    def process_intent(self, intent):
        if intent and intent.getData():
            link = intent.getData().toString()
            if link.startswith("magnet:"):
                self.add_torrent(link)

    def add_torrent(self, link):
        save_path = "/storage/emulated/0/Download"
        if not os.path.exists(save_path):
            save_path = "."
        params = {'save_path': save_path}
        handle = lt.add_magnet_uri(self.ses, link, params)
        handle.set_sequential_download(True)
        self.handles.append(handle)

    def update_status(self, dt):
        self.main_screen.ids.rv.data = [{
            'title': h.status().name if h.status().name else "Connecting...",
            'progress': h.status().progress * 100,
            'speed': f"{h.status().download_rate / 1000000:.2f}"
        } for h in self.handles]

if __name__ == '__main__':
    NeoOnyxApp().run()
