from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivy.clock import Clock

class AnimatedWidget:
    def fade_in(self, duration=0.3):
        anim = Animation(opacity=1, duration=duration)
        anim.start(self)
        return anim
    
    def fade_out(self, duration=0.2):
        anim = Animation(opacity=0, duration=duration)
        anim.start(self)
        return anim
    
    def slide_up(self, y_offset=50, duration=0.4):
        anim = Animation(y=self.y + y_offset, duration=duration)
        anim += Animation(y=self.y, duration=0.2)
        anim.start(self)
        return anim
    
    def scale_pulse(self):
        anim = Animation(scale=1.1, duration=0.15) + \
               Animation(scale=1.0, duration=0.15)
        anim.start(self)
        return anim

class ParticleBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        Clock.schedule_interval(self.update_particles, 1/60)
        Clock.schedule_interval(self.spawn_particle, 0.5)
    
    def spawn_particle(self, dt):
        pass
    
    def update_particles(self, dt):
        pass
