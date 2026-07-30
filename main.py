from kivymd.app import MDApp
from src.cool_ui import ModernMainScreen

class DRIPApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        return ModernMainScreen()

if __name__ == '__main__':
    DRIPApp().run()
