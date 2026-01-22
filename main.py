from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.switch import Switch
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import platform
from kivy.core.window import Window
import libtorrent as lt
import webbrowser
import os

# --- UI COMPONENTS ---
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

class SelectableLabel(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty("")
    selected = BooleanProperty(True)
    index = None
    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.text = data['text']
        self.selected = data['selected']
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.selected = not self.selected
            self.parent.parent.data[self.index]['selected'] = self.selected
            return True
        return super(SelectableLabel, self).on_touch_down(touch)

class FileSelectorPopup(Popup):
    data = ListProperty([])
    def __init__(self, handle, card_callback, **kwargs):
        super().__init__(**kwargs)
        self.handle = handle
        self.callback = card_callback
        self.title = "Select Files"
        self.size_hint = (0.9, 0.8)
        self.separator_color = (0, 0.8, 1, 1)
        container = BoxLayout(orientation='vertical', padding=10, spacing=10)
        name_text = "Getting File List..."
        if self.handle.is_valid() and self.handle.has_metadata():
            name_text = self.handle.get_torrent_info().name()
        container.add_widget(Label(text=f"{name_text[:40]}...", size_hint_y=None, height=30, color=(0.7,0.7,0.7,1)))
        self.rv = RecycleView(viewclass=SelectableLabel)
        self.rv.data = self.data
        layout = RecycleBoxLayout(default_size=(None, 40), default_size_hint=(1, None), size_hint_y=None, orientation='vertical')
        layout.bind(minimum_height=layout.setter('height'))
        self.rv.add_widget(layout)
        container.add_widget(self.rv)
        confirm_btn = RoundedButton(text="CONFIRM SELECTION", btn_color=(0, 0.8, 0.2, 1), size_hint_y=None, height=50)
        confirm_btn.bind(on_press=self.apply_selection)
        container.add_widget(confirm_btn)
        self.content = container
        self.populate_files()
    def populate_files(self):
        if not self.handle.is_valid() or not self.handle.has_metadata(): return
        info = self.handle.get_torrent_info()
        files = info.files()
        new_data = []
        priorities = self.handle.file_priorities()
        for i in range(files.num_files()):
            f_name = os.path.basename(files.file_path(i))
            f_size = files.file_size(i) / (1024*1024)
            is_active = True if not priorities or priorities[i] > 0 else False
            new_data.append({'text': f"[{'x' if is_active else ' '}] {f_name} ({f_size:.1f} MB)", 'selected': is_active})
        self.rv.data = new_data
    def apply_selection(self, instance):
        new_priorities = [1 if item['selected'] else 0 for item in self.rv.data]
        self.handle.prioritize_files(new_priorities)
        self.callback()
        self.dismiss()

class TorrentCard(BoxLayout):
    def __init__(self, handle, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.handle = handle
        self.app = app_ref
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 190
        self.padding = 15
        self.spacing = 8
        with self.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.title_lbl = Label(text="Fetching Metadata...", font_size='15sp', bold=True, halign='left', valign='middle', size_hint_y=None, height=30, shorten=True, shorten_from='right')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=6)
        self.add_widget(self.progress)
        stats = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        self.speed_lbl = Label(text="0 KB/s", color=(0, 0.9, 1, 1), font_size='13sp', bold=True)
        self.meta_lbl = Label(text="Waiting...", color=(0.6, 0.6, 0.6, 1), font_size='13sp')
        stats.add_widget(self.speed_lbl)
        stats.add_widget(self.meta_lbl)
        self.add_widget(stats)
        ctrl_row = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        stream_box = BoxLayout(orientation='horizontal', spacing=5)
        stream_box.add_widget(Label(text="Stream:", font_size='12sp', size_hint_x=0.4))
        self.stream_switch = Switch(active=False, size_hint_x=0.6)
        self.stream_switch.bind(active=self.toggle_sequential)
        stream_box.add_widget(self.stream_switch)
        ctrl_row.add_widget(stream_box)
        self.files_btn = RoundedButton(text="FILES", size_hint_x=0.4, btn_color=(0.3, 0.3, 0.3, 1))
        self.files_btn.bind(on_press=self.open_file_selector)
        self.files_btn.disabled = True
        ctrl_row.add_widget(self.files_btn)
        self.add_widget(ctrl_row)
        actions = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        self.pause_btn = RoundedButton(text="PAUSE", btn_color=(1, 0.7, 0, 1))
        self.pause_btn.bind(on_press=self.toggle_pause)
        actions.add_widget(self.pause_btn)
        self.del_btn = RoundedButton(text="DELETE", btn_color=(0.8, 0.2, 0.2, 1))
        self.del_btn.bind(on_press=self.request_delete)
        actions.add_widget(self.del_btn)
        self.add_widget(actions)
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    def toggle_sequential(self, instance, value):
        if not self.handle.is_valid(): return
        self.handle.set_sequential_download(value)
        if value: self.handle.set_deadline(0, 1000)
    def open_file_selector(self, instance):
        if self.handle.is_valid() and self.handle.has_metadata():
            self.handle.pause()
            popup = FileSelectorPopup(self.handle, self.resume_download)
            popup.open()
    def resume_download(self):
        if self.handle.is_valid(): self.handle.resume()
    def toggle_pause(self, instance):
        if not self.handle.is_valid(): return
        if self.handle.status().paused:
            self.handle.resume()
            self.pause_btn.text = "PAUSE"
            self.pause_btn.btn_color = (1, 0.7, 0, 1)
        else:
            self.handle.pause()
            self.pause_btn.text = "RESUME"
            self.pause_btn.btn_color = (0.2, 0.8, 0.3, 1)
        self.pause_btn.update_canvas()
    def request_delete(self, instance):
        self.app.delete_torrent(self.handle, self)

class NeoTorrentDiamond(App):
    def build(self):
        self.request_android_permissions()
        self.save_path = self.get_download_path()
        self.cards = {} 
        if platform == 'android': Window.keep_screen_on = True
        self.ses = lt.session()
        self.ses.listen_on(6881, 6891)
        self.ses.apply_settings({'active_downloads': 10, 'active_seeds': 5, 'connections_limit': 200})
        self.root = FloatLayout()
        with self.root.canvas.before:
            Color(0, 0, 0, 1)
            RoundedRectangle(pos=(0,0), size=(3000, 3000))
        main_box = BoxLayout(orientation='vertical')
        header = BoxLayout(size_hint_y=None, height=130, orientation='vertical', padding=15, spacing=5)
        top_bar = BoxLayout(size_hint_y=None, height=40)
        top_bar.add_widget(Label(text="NeoTorrent", font_size='24sp', bold=True, color=(0, 0.8, 1, 1), halign='left', size_hint_x=0.4))
        self.total_speed = Label(text="DL: 0.0 MB/s", font_size='16sp', color=(1,1,1,1), halign='right', size_hint_x=0.6)
        top_bar.add_widget(self.total_speed)
        header.add_widget(top_bar)
        tools_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.search_input = TextInput(hint_text="Search...", multiline=False, size_hint_x=0.5, background_color=(0.2,0.2,0.2,1), foreground_color=(1,1,1,1))
        tools_bar.add_widget(self.search_input)
        search_btn = RoundedButton(text="GO", size_hint_x=0.2, btn_color=(0.2, 0.2, 0.2, 1))
        search_btn.bind(on_press=self.perform_search)
        tools_bar.add_widget(search_btn)
        wifi_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        wifi_box.add_widget(Label(text="Wi-Fi Only", font_size='10sp'))
        self.wifi_switch = Switch(active=False)
        wifi_box.add_widget(self.wifi_switch)
        tools_bar.add_widget(wifi_box)
        header.add_widget(tools_bar)
        main_box.add_widget(header)
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=10)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        main_box.add_widget(self.scroll)
        self.fab = RoundedButton(text="+", font_size='35sp', size_hint=(None, None), size=(70, 70), pos_hint={'right': 0.95, 'y': 0.04}, btn_color=(0, 0.7, 1, 1), radius=[35])
        self.fab.bind(on_press=self.show_add_popup)
        self.root.add_widget(self.fab)
        Clock.schedule_interval(self.update_loop, 1.0)
        return self.root
    def on_pause(self): return True
    def on_resume(self): return True
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
    def perform_search(self, instance):
        if self.search_input.text: webbrowser.open(f"https://www.google.com/search?q={self.search_input.text}+magnet+torrent")
    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.link_input = TextInput(hint_text="Paste Magnet Link...", multiline=False, size_hint_y=None, height=50)
        content.add_widget(self.link_input)
        add_btn = RoundedButton(text="ADD DOWNLOAD", size_hint_y=None, height=50, btn_color=(0, 0.8, 0, 1))
        add_btn.bind(on_press=self.add_torrent)
        content.add_widget(add_btn)
        self.popup = Popup(title="Add Torrent", content=content, size_hint=(0.9, 0.35))
        self.popup.open()
    def add_torrent(self, instance):
        link = self.link_input.text.strip().replace('"', '')
        if "magnet:" in link:
            try:
                params = {'save_path': self.save_path}
                handle = lt.add_magnet_uri(self.ses, link, params)
                card = TorrentCard(handle, self)
                self.list_layout.add_widget(card)
                self.cards[handle] = card
                self.popup.dismiss()
            except: self.link_input.text = "Error: Bad Link"
        else: self.link_input.text = "Error: Not a magnet link"
    def delete_torrent(self, handle, card):
        try:
            if handle.is_valid(): self.ses.remove_torrent(handle)
        except: pass
        self.list_layout.remove_widget(card)
        if handle in self.cards: del self.cards[handle]
    def update_loop(self, dt):
        try:
            status = self.ses.status()
            self.total_speed.text = f"DL: {status.download_rate / 1000000:.1f} MB/s"
            for handle, card in list(self.cards.items()):
                if not handle.is_valid(): continue
                s = handle.status()
                if handle.has_metadata():
                    card.title_lbl.text = handle.get_torrent_info().name()
                    card.files_btn.disabled = False
                    card.files_btn.btn_color = (0.2, 0.2, 0.2, 1)
                card.progress.value = s.progress * 100
                card.speed_lbl.text = f"{s.download_rate / 1000:.0f} KB/s"
                card.meta_lbl.text = f"Peers: {s.num_peers} | {s.state}"
        except: pass

if __name__ == '__main__':
    NeoTorrentDiamond().run()
