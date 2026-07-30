from kivy.core.window import Window
from kivymd.theming import ThemableBehavior
from kivymd.color_definitions import colors
from kivymd.uix.button import MDRaisedButton

THEMES = {
    'dark_purple': {
        'primary': '#D0BCFF',
        'on_primary': '#381E72',
        'primary_container': '#4F378B',
        'on_primary_container': '#EADDFF',
        'secondary': '#CCC2DC',
        'surface': '#1C1B1F',
        'surface_variant': '#49454F',
        'on_surface': '#E6E1E5',
        'outline': '#938F99',
    },
    'ocean_blue': {
        'primary': '#4FD8EB',
        'on_primary': '#00363D',
        'primary_container': '#004F58',
        'surface': '#191C1D',
        'surface_variant': '#3F484A',
    },
    'cyber_punk': {
        'primary': '#FF0055',
        'on_primary': '#000000',
        'primary_container': '#330011',
        'surface': '#0D0D0D',
        'surface_variant': '#1F1F1F',
    }
}

def apply_theme(theme_name='dark_purple'):
    theme = THEMES.get(theme_name, THEMES['dark_purple'])
    colors['Light']['Primary'] = theme['primary']
    colors['Dark']['Primary'] = theme['primary']
    colors['Dark']['Background'] = theme['surface']
    return theme
