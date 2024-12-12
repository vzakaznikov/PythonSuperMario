import os
import sys
import time
import pygame as pg
from testflows.core import *
from testflows.asserts import error

append_path(sys.path, os.path.join(current_dir(), ".."), pos=0)

import tests.actions as actions
import tests.models as models
import actions.game
import actions.vision
import models.game


@TestScenario
def check_start(self):
    """Start the game."""

    with Given("start the game"):
        game = actions.game.start()
        self.context.game = game

    with Then("the game is started"):
        game.vision.overlay(game.screen)
        assert "little_mario" in game.vision.result.dboxes, error()


@TestScenario
def check_jump(self):
    """Jump in the game."""

    with Given("start the game"):
        game = actions.game.start()
        self.context.game = game

    with When("jump"):
        with actions.game.press_jump():
            for i in range(62):
                debug(f'{game.keys} {game.vision.result.dboxes["little_mario"]}')
                next(game.play)
                game.vision.overlay(game.screen)

    with Then("Mario jumps"):
        for i in range(30):
            debug(f'{game.keys} {game.vision.result.dboxes["little_mario"]}')
            next(game.play)
            game.vision.overlay(game.screen)


@TestScenario
def check_move_right(self):
    """Move right in the game."""

    with Given("start the game"):
        game = actions.game.start()
        self.context.game = game

    model = models.game.Game(game)

    with When("move right"):
        with actions.game.press_right():
            for i in range(60):
                next(game.play)
                try:
                    model.expect(game.behavior)
                except AssertionError as exc:
                    debug(exc)
                    pause()

    with Then("Mario moves right"):
        for i in range(0):
            next(game.play)
            game.vision.overlay(game.screen)


@TestScenario
def manual_play(self):
    """Manually test the game using the model."""

    with Given("start the game"):
        game = actions.game.start()
        self.context.game = game

    model = models.game.Game(game)

    game.manual = True
    try:
        for i in range(game.fps * 300):
            next(game.play)
            # game.vision.overlay()
            try:
                model.expect(game.behavior)
            except AssertionError as exc:
                debug(f"Error: {exc}")
                pause()
                continue
    finally:
        game.manual = False


@TestFeature
def regression(self):
    """Regression tests for the Super Mario game."""

    Scenario(run=manual_play)


if main():
    regression()
