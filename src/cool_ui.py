from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFloatingActionButton, MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.toolbar import MDTopAppBar
from src.theme import apply_theme

class ModernMainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = apply_theme('cyber_punk')
        self.build_ui()
    
    def build_ui(self):
        main = BoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(
            title="[b]DRIP[/b] Downloader",
            md_bg_color=self.theme['surface'],
            specific_text_color=self.theme['primary'],
            elevation=0,
            anchor_title='left',
            right_action_items=[
                ['theme-light-dark', lambda x: self.toggle_theme()],
                ['cog', lambda x: self.open_settings()],
            ]
        )
        main.add_widget(self.toolbar)
        content = FloatLayout()
        
        with content.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*self.hex_to_rgb(self.theme['surface']))
            self.bg_rect = Rectangle(size=content.size, pos=content.pos)
            content.bind(size=self.update_bg, pos=self.update_bg)
        
        self.main_card = GlassmorphismCard(
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            size_hint=(0.9, 0.7),
            radius=[dp(24), dp(24), dp(24), dp(24)],
        )
        
        self.url_field = CoolTextField(
            hint_text="Paste video URL...",
            icon_right="link-variant",
            pos_hint={'center_x': 0.5, 'top': 0.95},
            size_hint_x=0.85,
        )
        self.main_card.add_widget(self.url_field)
        
        self.download_btn = AnimatedDownloadButton(
            pos_hint={'center_x': 0.5, 'y': 0.05},
            size_hint=(0.6, None),
            height=dp(56),
        )
        self.main_card.add_widget(self.download_btn)
        content.add_widget(self.main_card)
        main.add_widget(content)
        self.add_widget(main)
    
    def update_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    
    def toggle_theme(self):
        pass
        
    def open_settings(self):
        pass

class GlassmorphismCard(MDCard, RoundedRectangularElevationBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0.15, 0.15, 0.15, 0.8]
        self.elevation = 8

class CoolTextField(MDTextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = "round"
        self.fill_color_normal = [0.2, 0.2, 0.2, 0.6]
        self.fill_color_focus = [0.25, 0.25, 0.25, 0.8]
        self.line_color_normal = [0.4, 0.4, 0.4, 0.3]
        self.line_color_focus = [1, 0, 0.33, 1]
        self.text_color_normal = [0.9, 0.9, 0.9, 1]
        self.text_color_focus = [1, 1, 1, 1]
        self.font_size = '16sp'

class AnimatedDownloadButton(MDFloatingActionButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 0, 0.33, 1]
        self.icon = 'download'
        self.elevation = 4
        Clock.schedule_interval(self.pulse, 2)
    
    def pulse(self, dt):
        anim = Animation(elevation=8, duration=0.3) + \
               Animation(elevation=4, duration=0.3)
        anim.start(self)
