"""Behavior model for Super Mario Bros game."""

from .base import Model
from .box import Box
from .mario import Mario


class Game(Model):
    """Model for the behavior of the game."""

    def __init__(self, game):
        self.game = game
        # models for each game elements
        self.box = Box(game=game)
        self.mario = Mario(game=game)

    def expect(self, behavior):
        """Expect the game to behave correctly."""

        self.box.expect(behavior)
        self.mario.expect(behavior)
