import pygame as pg
from dataclasses import dataclass

from testflows.core import *


@dataclass
class Element:
    name: str
    box: pg.Rect
    id: int


class Vision:
    """Vision model for object detection using YOLO."""

    COLOR_MAP = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "gray": (128, 128, 128),
        "pink": (255, 192, 203),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
    }

    def __init__(self, game):
        self.game = game
        self.boxes = {}
        self.viewport = pg.Rect(0, 0, 0, 0)

    def overlay(self, boxes=None, color=(255, 0, 0), thickness=3):
        """
        Overlay boxes directly on the screen.

        Args:
            screen (pg.Surface): The Pygame screen to draw on.
            missing_boxes (list of torch.Tensor): List of tensors representing missing boxes
                                                in the format [x1, y1, x2, y2].
            color (tuple): RGB color of the rectangle (default is red).
            thickness (int): Thickness of the rectangle's border.
        """
        screen = self.game.screen

        if boxes is None:
            visible = self.get_visible()
            boxes = [box for element in visible for box in visible[element]]

        for box in boxes:
            x1, y1, w, h = map(int, box)

            # Draw a rectangle directly on the screen
            pg.draw.rect(screen, color, pg.Rect(x1, y1, w, h), thickness)

        # Update the Pygame display
        pg.display.flip()  # Refresh the screen to show the changes

    def get_visible(self):
        """
        Get all currently visible elements on the screen.

        Args:
            sprite_group (pg.sprite.Group): Group of all sprites.
            screen_rect (pg.Rect): Rect representing the screen boundaries.

        Returns:
            list: List of visible sprites.
        """
        visible = []

        if self.game.state_name != "level":
            # Return an empty set if the state is not "level"
            return {}

        sprite_group = []
        viewport = self.game.state.viewport

        for attr_name in vars(self.game.state):
            attr = getattr(self.game.state, attr_name)
            if isinstance(attr, pg.sprite.Sprite):
                sprite_group.append(attr)
            elif isinstance(attr, pg.sprite.Group):
                sprite_group += [sprite for sprite in attr]

        for sprite in sprite_group:
            if viewport.colliderect(sprite.rect):
                visible.append(sprite)

        boxes = {}
        for sprite in set(visible):
            name = sprite.__class__.__name__.lower()
            # remove checkpoints
            if name == "checkpoint":
                continue
            if name not in boxes:
                boxes[name] = []
            x, y, w, h = sprite.rect

            rect = pg.Rect(x, y, w, h)

            boxes[name].append(Element(name, rect, id(sprite)))

        return boxes

    def adjust_box(self, box, viewport):
        """Adjust the box coordinates to the viewport."""
        x, y, w, h = box

        # adjust the coordinates to the viewport
        # taking into account visible width
        if x < viewport.x:
            w = (x + w) - viewport.x
            x = 0
        else:
            x = x - viewport.x
            w = min(w, viewport.x + viewport.w - x)

        # keep y and height the same
        y = y
        h = h

        return pg.Rect(x, y, w, h)

    def in_view(self, box, viewport):
        """Check if the box is in the current viewport."""
        return viewport.colliderect(box)

    def detect(self):
        """Detect visible game elements."""
        self.boxes = self.get_visible()
        if self.boxes:
            self.viewport = self.game.state.viewport
        return self
