import pygame as pg
import numpy as np
import imagehash

from PIL import Image
from copy import deepcopy

from testflows.core import *
from contextlib import contextmanager

from game.source import tools
from game.source import constants as c
from game.source.states import main_menu, load_screen, level

from .vision import Vision

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

# Define keybindings
keys = {
    "action": pg.K_s,
    "jump": pg.K_a,
    "left": pg.K_LEFT,
    "right": pg.K_RIGHT,
    "down": pg.K_DOWN,
    "enter": pg.K_RETURN,
}

all_key_codes = [code for name, code in vars(pg).items() if name.startswith("K_")]


class Keys:
    def __init__(self):
        self.keys = {}

    def key_code(self, name):
        return pg.key.key_code(name)

    def key_name(self, key):
        return pg.key.name(key)

    def __contains__(self, key):
        return key in self.keys

    def __getitem__(self, key):
        if key in self.keys:
            return self.keys[key]
        return False

    def __setitem__(self, key, value):
        self.keys[key] = value

    def __delitem__(self, key):
        del self.keys[key]

    def __str__(self):
        return f"Keys({','.join([self.key_name(key) for key in self.keys])})"


class BehaviorState:
    def __init__(self, keys, boxes, viewport):
        self.keys = deepcopy(keys)
        self.boxes = boxes
        self.viewport = deepcopy(viewport)

    def __str__(self):
        return f"BehaviorState(keys={self.keys}, boxes={self.boxes}, viewport={self.viewport})"

    def __repr__(self):
        return str(self)


class Control(tools.Control):
    def __init__(self, fps=60, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fps = fps
        self.keys = Keys()
        self.screen = pg.display.get_surface()
        self.vision = Vision(self)
        self.behavior = []
        self.play = None
        self.manual = False

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.KEYDOWN:
                if self.manual:
                    pressed = pg.key.get_pressed()
                    for code in all_key_codes:
                        if pressed[code]:
                            self.keys[code] = True
                else:
                    if hasattr(event, "key"):
                        self.keys[event.key] = True
            elif event.type == pg.KEYUP:
                if self.manual:
                    pressed = pg.key.get_pressed()
                    for code in all_key_codes:
                        if code in self.keys and not pressed[code]:
                            del self.keys[code]
                else:
                    if hasattr(event, "key"):
                        del self.keys[event.key]

    def main(self):
        """Main game loop."""

        def _main():
            while not self.done:
                self.event_loop()
                self.update()

                self.vision.detect()
                self.behavior.append(
                    BehaviorState(self.keys, self.vision.boxes, self.vision.viewport)
                )

                yield self

                pg.display.update()
                self.clock.tick(self.fps)

        self.play = _main()


@contextmanager
def simulate_keypress(key):
    """
    Simulate a key press and release event for the given key.
    """
    # Simulate KEYDOWN event
    keydown_event = pg.event.Event(pg.KEYDOWN, key=key)
    pg.event.post(keydown_event)

    yield

    # Simulate KEYUP event
    keyup_event = pg.event.Event(pg.KEYUP, key=key)
    pg.event.post(keyup_event)


def press_enter():
    """Press the enter key."""
    return simulate_keypress(key=keys["enter"])


def press_right():
    """Press the right arrow key."""
    return simulate_keypress(key=keys["right"])


def press_left():
    """Press the left arrow key."""
    return simulate_keypress(key=keys["left"])


def press_down():
    """Press the down arrow key."""
    return simulate_keypress(key=keys["down"])


def press_jump():
    """Press the jump key."""
    return simulate_keypress(key=keys["jump"])


def press_action():
    """Press the action key."""
    return simulate_keypress(keys["action"])


@TestStep(When)
def capture_screen(self, screen):
    """
    Capture the current PyGame screen and return it as a Pillow Image.
    """
    # Convert the PyGame screen to a NumPy array
    screen_array = pg.surfarray.array3d(screen)

    # Convert from (width, height, color) to (height, width, color)
    screen_array = np.transpose(screen_array, (1, 0, 2))

    # Create a Pillow Image from the array
    screen_image = Image.fromarray(screen_array)
    screen_hash = imagehash.average_hash(screen_image)

    return screen_image, screen_hash


@TestStep(When)
def wait_ready(self, game):
    """Wait for game to be loaded and ready."""
    next(game.play)

    with press_enter():
        next(game.play)

    for i in range(3 * game.fps):
        next(game.play)


@TestStep(Given)
def start(self, wait_for_ready=True):
    """Start the game."""

    game = Control()
    state_dict = {
        c.MAIN_MENU: main_menu.Menu(),
        c.LOAD_SCREEN: load_screen.LoadScreen(),
        c.LEVEL: level.Level(),
        c.GAME_OVER: load_screen.GameOver(),
        c.TIME_OUT: load_screen.TimeOut(),
    }
    game.setup_states(state_dict, c.MAIN_MENU)
    try:
        game.main()
        if wait_for_ready:
            wait_ready(game=game)
        yield game
    finally:
        pg.quit()
