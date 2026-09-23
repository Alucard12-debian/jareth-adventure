# language: Python 3.13+, file: Game.py
# Jareth Adventure — Flappy Bird
# intro + START + VER VIDEO · pausa · video a los 10 puntos · optimizado A15

import os
import sys
import random
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty
from kivy.utils import platform

try:
    from kivy.uix.video import Video
    VIDEO_OK = True
except Exception:
    VIDEO_OK = False

try:
    from video_android import play_video_android
except Exception:
    def play_video_android(path, on_finish=None):
        return False


# ── rutas: script y .exe ──
if getattr(sys, 'frozen', False):
    _external = os.path.join(os.path.dirname(sys.executable), 'assets')
    if os.path.isdir(_external):
        BASE = os.path.dirname(sys.executable)
    else:
        BASE = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

ASSETS = os.path.join(BASE, 'assets')
BIRD_IMG = os.path.join(ASSETS, 'bird.png')
PIPE_IMG = os.path.join(ASSETS, 'pipe.png')
VIDEO_PATH = os.path.join(ASSETS, 'Jareth.mp4')


# ── ajustes para Samsung A15 (1080x2340, 6.5", densidad 3x) ──
GRAVITY = -0.6
JUMP = 9.0
PIPE_GAP = 200
PIPE_SPEED = -4
PIPE_SPACING = 380          # ← antes 260: tubos más separados
PIPE_WIDTH = 70
GROUND_H = 80
BIRD_DRAW_SIZE = (120, 120)
BIRD_HIT_W = 60
BIRD_HIT_H = 60
VIDEO_TRIGGER_SCORE = 10


# ══════════════════════════════════════════════════════════════════
#  INTRO
# ══════════════════════════════════════════════════════════════════
class IntroScreen(FloatLayout):
    def __init__(self, on_start, on_video, **kw):
        super().__init__(**kw)
        self.on_start = on_start
        self.on_video = on_video

        with self.canvas.before:
            Color(0.85, 0.1, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.add_widget(Label(text='JARETH',
                              font_size='64sp', bold=True,
                              color=(1, 1, 1, 1),
                              outline_color=(0, 0, 0, 1), outline_width=4,
                              size_hint=(None, None),
                              size=(400, 100),
                              pos_hint={'center_x': 0.5, 'center_y': 0.75}))

        self.add_widget(Label(text='ADVENTURE',
                              font_size='40sp', bold=True,
                              color=(1, 1, 0.2, 1),
                              outline_color=(0, 0, 0, 1), outline_width=4,
                              size_hint=(None, None),
                              size=(400, 80),
                              pos_hint={'center_x': 0.5, 'center_y': 0.63}))

        boton_start = Button(text='START',
                             font_size='32sp', bold=True,
                             background_color=(0, 0.7, 0, 1),
                             color=(1, 1, 1, 1),
                             size_hint=(None, None),
                             size=(220, 80),
                             pos_hint={'center_x': 0.5, 'center_y': 0.42})
        boton_start.bind(on_press=self._start)
        self.add_widget(boton_start)

        boton_video = Button(text='VER VIDEO',
                             font_size='24sp', bold=True,
                             background_color=(0.2, 0.2, 0.7, 1),
                             color=(1, 1, 1, 1),
                             size_hint=(None, None),
                             size=(220, 70),
                             pos_hint={'center_x': 0.5, 'center_y': 0.28})
        boton_video.bind(on_press=self._video)
        self.add_widget(boton_video)

    def _update_bg(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _start(self, *a):
        self.on_start()

    def _video(self, *a):
        self.on_video()


# ══════════════════════════════════════════════════════════════════
#  VIDEO SCREEN
# ══════════════════════════════════════════════════════════════════
class VideoScreen(FloatLayout):
    def __init__(self, on_finish, **kw):
        super().__init__(**kw)
        self.on_finish = on_finish

        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        if VIDEO_OK and os.path.exists(VIDEO_PATH):
            self.video = Video(source=VIDEO_PATH,
                               state='play',
                               options={'eos': 'stop'},
                               size_hint=(None, None))
            self.add_widget(self.video)
            self.video.bind(eos=self._video_ended)
            Clock.schedule_once(self._layout_video, 0)
        else:
            self.add_widget(Label(text='[no se pudo cargar el video]',
                                  font_size='24sp', color=(1, 1, 1, 1)))
            Clock.schedule_once(lambda dt: self.on_finish(), 2.0)

        skip = Button(text='SALTAR',
                      font_size='20sp', bold=True,
                      background_color=(0, 0, 0, 0.6),
                      color=(1, 1, 1, 1),
                      size_hint=(None, None),
                      size=(120, 50))
        skip.bind(on_press=lambda *a: self.on_finish())
        self.add_widget(skip)
        Clock.schedule_once(lambda dt: setattr(
            skip, 'pos', (Window.width - 140, 20)), 0)

    def _update_bg(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _layout_video(self, dt=0):
        if hasattr(self, 'video'):
            self.video.pos = (0, 0)
            self.video.size = (Window.width, Window.height)

    def _video_ended(self, *a):
        self.on_finish()


# ══════════════════════════════════════════════════════════════════
#  PÁJARO
# ══════════════════════════════════════════════════════════════════
class Bird(Widget):
    velocity_y = NumericProperty(0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = BIRD_DRAW_SIZE
        self.disabled = True

        self._visual = Image(source=BIRD_IMG,
                             size_hint=(None, None),
                             size=BIRD_DRAW_SIZE,
                             pos=self.pos)
        self._visual.disabled = True
        self.add_widget(self._visual)
        self.bind(pos=self._sync_visual, size=self._sync_visual)

    def _sync_visual(self, *a):
        self._visual.pos = self.pos
        self._visual.size = self.size

    def on_touch_down(self, touch):
        return False

    def on_touch_move(self, touch):
        return False

    def on_touch_up(self, touch):
        return False

    def hitbox_rect(self):
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        return (cx - BIRD_HIT_W / 2,
                cy - BIRD_HIT_H / 2,
                BIRD_HIT_W,
                BIRD_HIT_H)

    def jump(self):
        self.velocity_y = JUMP

    def update(self, dt):
        self.velocity_y += GRAVITY
        self.y += self.velocity_y


# ══════════════════════════════════════════════════════════════════
#  TUBOS
# ══════════════════════════════════════════════════════════════════
class PipePair(FloatLayout):
    def __init__(self, x, gap_y, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (PIPE_WIDTH, Window.height)
        self.pos = (x, 0)
        self.disabled = True

        gap_top = gap_y + PIPE_GAP / 2
        gap_bottom = gap_y - PIPE_GAP / 2

        self.top_pipe = Image(source=PIPE_IMG,
                              pos=(x, gap_top),
                              size=(PIPE_WIDTH, Window.height - gap_top),
                              size_hint=(None, None))
        self.top_pipe.disabled = True

        self.bottom_pipe = Image(source=PIPE_IMG,
                                 pos=(x, 0),
                                 size=(PIPE_WIDTH, gap_bottom),
                                 size_hint=(None, None))
        self.bottom_pipe.disabled = True

    def move(self, dx):
        self.x += dx
        self.top_pipe.x += dx
        self.bottom_pipe.x += dx

    def collides_with(self, bird):
        bx, by, bw, bh = bird.hitbox_rect()
        for pipe in (self.top_pipe, self.bottom_pipe):
            px, py, pw, ph = pipe.x, pipe.y, pipe.width, pipe.height
            if bx < px + pw and bx + bw > px and by < py + ph and by + bh > py:
                return True
        return False

    def is_offscreen(self):
        return self.top_pipe.x + self.top_pipe.width < 0


# ══════════════════════════════════════════════════════════════════
#  JUEGO
# ══════════════════════════════════════════════════════════════════
class FlappyGame(FloatLayout):
    bird = ObjectProperty(None)
    score = NumericProperty(0)
    game_over = False
    paused = False
    started = False
    video_shown = False

    def __init__(self, on_game_over, on_video, **kw):
        super().__init__(**kw)
        self.on_game_over = on_game_over
        self.on_video = on_video

        with self.canvas.before:
            Color(0.85, 0.1, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        with self.canvas.before:
            Color(0.4, 0.05, 0.05, 1)
            self.ground = Rectangle(pos=(0, 0), size=(Window.width, GROUND_H))

        self.bird = Bird()
        self.add_widget(self.bird)

        self.score_label = Label(text='0',
                                 font_size='48sp', bold=True,
                                 color=(1, 1, 1, 1),
                                 outline_color=(0, 0, 0, 1), outline_width=3,
                                 size_hint=(None, None),
                                 size=(200, 80))
        self.score_label.disabled = True
        self.add_widget(self.score_label)

        self.hint = Label(text='TOCA PARA SALTAR',
                          font_size='24sp', bold=True,
                          color=(1, 1, 1, 1),
                          outline_color=(0, 0, 0, 1), outline_width=3,
                          size_hint=(None, None),
                          size=(400, 60))
        self.hint.disabled = True
        self.add_widget(self.hint)

        self.pause_btn = Button(text='PAUSA',
                                font_size='20sp', bold=True,
                                background_color=(0, 0, 0, 0.6),
                                color=(1, 1, 1, 1),
                                size_hint=(None, None),
                                size=(110, 55))
        self.pause_btn.bind(on_press=self._toggle_pause)
        self.add_widget(self.pause_btn)

        self.pause_overlay = Label(text='PAUSADO',
                                   font_size='56sp', bold=True,
                                   color=(1, 1, 1, 1),
                                   outline_color=(0, 0, 0, 1), outline_width=4,
                                   size_hint=(None, None),
                                   size=(400, 100),
                                   opacity=0)
        self.pause_overlay.disabled = True
        self.add_widget(self.pause_overlay)

        self.remove_widget(self.pause_btn)
        self.add_widget(self.pause_btn)

        self.pipes = []
        self.pipe_spacing_counter = 0

        Clock.schedule_once(self._layout, 0)
        self.clock = Clock.schedule_interval(self.update, 1 / 60)

    def _layout(self, dt=0):
        h = Window.height
        w = Window.width
        self.bird.pos = (60, h / 2 - BIRD_DRAW_SIZE[1] / 2)
        self.score_label.pos = (w / 2 - 100, h - 100)
        self.hint.pos = (w / 2 - 200, h / 2 - 150)
        self.pause_btn.pos = (w - 130, h - 80)
        self.pause_overlay.pos = (w / 2 - 200, h / 2 - 50)

    def _update_bg(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.ground.size = (Window.width, GROUND_H)
        if self.bird is not None and not self.started:
            self._layout()

    def on_touch_down(self, touch):
        if self.pause_btn.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if self.game_over or self.paused:
            return True

        if not self.started:
            self.started = True
            self.hint.opacity = 0
            self.bird.jump()
            return True

        self.bird.jump()
        return True

    def _toggle_pause(self, *a):
        if self.game_over:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.text = 'REANUDAR'
            self.pause_overlay.opacity = 1
        else:
            self.pause_btn.text = 'PAUSA'
            self.pause_overlay.opacity = 0

    def spawn_pipe(self):
        h = Window.height
        gap_y = random.randint(int(GROUND_H + PIPE_GAP / 2 + 40),
                               int(h - PIPE_GAP / 2 - 40))
        p = PipePair(Window.width, gap_y)
        self.pipes.append(p)
        self.add_widget(p.top_pipe)
        self.add_widget(p.bottom_pipe)
        self.remove_widget(self.hint); self.add_widget(self.hint)
        self.remove_widget(self.pause_btn); self.add_widget(self.pause_btn)
        self.remove_widget(self.pause_overlay); self.add_widget(self.pause_overlay)

    def update(self, dt):
        if self.game_over or self.paused:
            return
        if not self.started:
            return

        h = Window.height
        self.bird.update(dt)

        if self.bird.top > h:
            self.bird.top = h
            self.bird.velocity_y = 0

        if self.bird.y < GROUND_H:
            self.end_game()
            return

        self.pipe_spacing_counter += -PIPE_SPEED
        if self.pipe_spacing_counter >= PIPE_SPACING:
            self.pipe_spacing_counter = 0
            self.spawn_pipe()

        for p in list(self.pipes):
            p.move(PIPE_SPEED)
            if p.collides_with(self.bird):
                self.end_game()
                return
            if p.is_offscreen():
                self.remove_widget(p.top_pipe)
                self.remove_widget(p.bottom_pipe)
                self.pipes.remove(p)
                self.score += 1
                self.score_label.text = str(self.score)

                if self.score >= VIDEO_TRIGGER_SCORE and not self.video_shown:
                    self.video_shown = True
                    self.paused = True
                    Clock.schedule_once(lambda dt: self.on_video(), 0.3)

    def end_game(self):
        self.game_over = True
        self.bird.velocity_y = -12
        Clock.schedule_once(lambda dt: self.on_game_over(), 1.2)

    def cleanup(self):
        try:
            self.clock.cancel()
        except Exception:
            pass
        for p in self.pipes:
            self.remove_widget(p.top_pipe)
            self.remove_widget(p.bottom_pipe)
        self.pipes.clear()


# ══════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════
class JarethApp(App):
    def build(self):
        Window.clearcolor = (0.85, 0.1, 0.1, 1)
        self.root_widget = FloatLayout()
        self.game = None
        self.intro = None
        self.video_screen = None
        self._show_intro()
        return self.root_widget

    def _show_intro(self):
        if self.game is not None:
            self.game.cleanup()
            self.root_widget.remove_widget(self.game)
            self.game = None
        if self.video_screen is not None:
            self.root_widget.remove_widget(self.video_screen)
            self.video_screen = None
        self.intro = IntroScreen(on_start=self._start_game,
                                 on_video=self._show_video)
        self.root_widget.add_widget(self.intro)

    def _start_game(self):
        if self.intro is not None:
            self.root_widget.remove_widget(self.intro)
            self.intro = None
        self.game = FlappyGame(on_game_over=self._back_to_intro,
                               on_video=self._show_video)
        self.root_widget.add_widget(self.game)

    def _show_video(self):
        if platform == 'android':
            if play_video_android(VIDEO_PATH, on_finish=self._video_done):
                return

        if self.video_screen is not None:
            return
        self.video_screen = VideoScreen(on_finish=self._video_done)
        self.root_widget.add_widget(self.video_screen)

    def _video_done(self):
        if self.video_screen is not None:
            self.root_widget.remove_widget(self.video_screen)
            self.video_screen = None
        if self.game is not None:
            self.game.paused = False

    def _back_to_intro(self):
        self._show_intro()


if __name__ == '__main__':
    JarethApp().run()
