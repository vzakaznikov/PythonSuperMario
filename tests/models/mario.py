from testflows.core import debug
from .base import Model


def find_element(name, state):
    """Find element in the specified state."""
    elements = state.boxes.get(name, [])
    element = elements[0] if elements else None

    return element


def find_mario(state):
    """Find Mario in the specified state."""
    return find_element("player", state)


def bottom_touch(box1, box2):
    """
    Check if box1's bottom edge touches box2's top edge.

    Args:
        box1 (pg.Rect): The first rectangle.
        box2 (pg.Rect): The second rectangle.

    Returns:
        bool: True if box1's bottom edge touches box2's top edge, False otherwise.
    """
    touched = (box2.top == box1.bottom) and (
        ((box1.left < box2.right) and (box1.left > box2.left))
        or ((box1.right < box2.right) and (box1.right > box2.left))
        or ((box1.left <= box2.left) and (box1.right >= box2.right))
    )
    return touched


def right_touch(box1, box2):
    """
    Check if box1's right edge touches box2's left edge.

    Args:
        box1 (pg.Rect): The first rectangle.
        box2 (pg.Rect): The second rectangle.

    Returns:
        bool: True if box1's right edge touches box2's left edge, False otherwise.
    """
    touched = (
        box1.left < box2.left and box1.right >= box2.left and box2.right > box1.right
    ) and (
        ((box1.bottom >= box2.top) and (box1.top < box2.top))
        or ((box1.top <= box2.bottom) and (box1.bottom > box2.top))
        or ((box1.top >= box2.top) and (box1.bottom <= box2.bottom))
    )
    return touched


def left_touch(box1, box2):
    """
    Check if box1's left edge touches box2's right edge.

    Args:
        box1 (pg.Rect): The first rectangle.
        box2 (pg.Rect): The second rectangle.

    Returns:
        bool: True if box1's left edge touches box2's right edge, False otherwise.
    """
    touched = (
        box2.left < box1.left and box1.left <= box2.right and box1.right > box2.right
    ) and (
        ((box1.bottom >= box2.top) and (box1.top < box2.top))
        or ((box1.top <= box2.bottom) and (box1.bottom > box2.top))
        or ((box1.top >= box2.top) and (box1.bottom <= box2.bottom))
    )
    return touched


def has_right_collision(game, element, state):
    """Check if the element has a right collision with another object."""
    for boxes in state.boxes.values():
        for box in boxes:
            if box is element:
                continue
            if right_touch(element.box, box.box):
                # Touched another object
                overlay(game, elements=[element, box], color=[0, 255, 0])
                return True

    return False


def has_left_collision(game, element, state):
    """Check if the element has a left collision with another object."""
    if element.box.left == 0:
        # Touched left edge of the world
        return True

    for boxes in state.boxes.values():
        for box in boxes:
            if box is element:
                continue
            if left_touch(element.box, box.box):
                # Touched another object
                overlay(game, elements=[element, box])
                return True

    return False


def has_bottom_collision(game, element, state, objects):
    """Check if the element has a bottom collision with another solid object."""
    boxes = []

    for name in objects:
        boxes += state.boxes.get(name, [])

    for box in boxes:
        if bottom_touch(element.box, box.box):
            # Touched another object
            overlay(game, elements=[element, box])
            return True

    return False


def dump(name, behavior, frames=10):
    """Dump elements's position in the last 10 states."""
    for i, s in enumerate(behavior[-frames:]):
        mario_s = find_element(name, s)
        if mario_s:
            debug(
                f"{i} Keys: {s.keys} {name.capitalize()}: {mario_s.box.x}, {mario_s.box.y}"
            )
        else:
            debug(f"{i} Keys: {s.keys} {name.capitalize()}: None")
    debug(f"Keys: {behavior[-1].boxes}")


def overlay(game, elements, thinckness=5, color=(255, 0, 0)):
    boxes = [
        game.vision.adjust_box(element.box, game.vision.viewport)
        for element in elements
    ]
    game.vision.overlay(
        boxes=boxes,
        thickness=thinckness,
        color=color,
    )


class Mario(Model):
    """Model for the behavior of Mario in the game."""

    # FIXME: move right collision with the "pole" and "poletop"
    # FIXME: move left collision with bottom edge of brick

    def expect_move_right(self, before, now, behavior):
        """Expect Mario to move right."""

        was_standing = False
        was_moving_left = False

        mario_2 = find_mario(behavior[-3])
        mario_1 = find_mario(before)
        mario_0 = find_mario(now)

        if not mario_2 or not mario_1 or not mario_0:
            # Mario is not in the previous or current state
            return

        if has_right_collision(self.game, mario_0, now):
            # Mario has right collision
            debug("Mario has right collision")
            return

        if mario_2.box.x == mario_1.box.x:
            # Mario was standing still
            was_standing = True

        elif mario_2.box.x > mario_1.box.x:
            # Mario was moving left
            was_moving_left = True

        if now.keys.key_code("right") not in now.keys:
            # Move right key is not pressed
            return

        if was_standing or was_moving_left:
            return

        # FIXME: handle Mario dying
        # FIXME: handle Mario transforming (small to big, big to fire, etc.)

        debug("Mario should move right")
        assert mario_1.box.x < mario_0.box.x, "Mario did not move right"

    def expect_move_left(self, before, now, behavior):
        """Expect Mario to move left."""

        was_standing = False
        was_moving_right = False

        mario_2 = find_mario(behavior[-3])
        mario_1 = find_mario(before)
        mario_0 = find_mario(now)

        if not mario_2 or not mario_1 or not mario_0:
            # Mario is not in the previous or current state
            return

        if has_left_collision(self.game, mario_0, now):
            # Mario has left collision
            debug("Mario has left collision")
            return

        if mario_2.box.x == mario_1.box.x:
            # Mario was standing still
            was_standing = True

        elif mario_2.box.x < mario_1.box.x:
            # Mario was moving right
            was_moving_right = True

        if now.keys.key_code("left") not in now.keys:
            # Move left key is not pressed
            return

        if was_standing or was_moving_right:
            return

        # FIXME: handle Mario dying
        # FIXME: handle Mario transforming (small to big, big to fire, etc.)

        debug("Mario should move left")
        assert mario_1.box.x > mario_0.box.x, "Mario did not move left"

    def expect_jump(self, before, now, behavior):
        """Expect Mario to jump."""
        on_the_ground_right_before = False
        on_the_ground_before = False
        jump_key_pressed_before = False
        jump_key_pressed_now = False

        right_before = behavior[-3]

        mario_right_before = find_mario(right_before)
        mario_before = find_mario(before)
        mario_now = find_mario(now)

        # FIXME: we need to assert full jump sequence where mario reaches the top of the jump

        if not mario_right_before or not mario_before or not mario_now:
            # Mario is not in the previous or current state
            return

        if has_bottom_collision(
            self.game,
            mario_right_before,
            right_before,
            objects=["box", "brick", "collider", "pipe"],
        ):
            on_the_ground_right_before = True

        if has_bottom_collision(
            self.game,
            mario_before,
            before,
            objects=["box", "brick", "collider", "pipe"],
        ):
            on_the_ground_before = True

        if before.keys.key_code("a") in before.keys:
            jump_key_pressed_before = True

        # FIXME: looks like Mario needs to be on the ground after completing previous jump for at least two frames

        if now.keys.key_code("a") in now.keys:
            # Jump key is not pressed
            jump_key_pressed_now = True

        if (
            on_the_ground_right_before
            and on_the_ground_before
            and not jump_key_pressed_before
            and jump_key_pressed_now
        ):
            debug("Mario should jump")
            dump("player", behavior)
            assert mario_now.box.y < mario_before.box.y, "Mario did not jump"

    def expect_fall(self, before, now, behavior):
        """Expect Mario to fall."""
        on_the_ground = False
        was_falling_or_standing = False
        was_jumping_and_reached_top = False

        mario_3 = find_mario(behavior[-4])
        mario_2 = find_mario(behavior[-3])
        mario_1 = find_mario(before)
        mario_0 = find_mario(now)

        if not mario_3 or not mario_2 or not mario_1 or not mario_0:
            return

        if has_bottom_collision(
            self.game, mario_1, before, objects=["box", "brick", "collider", "pipe"]
        ):
            on_the_ground = True

        if mario_2.box.y <= mario_1.box.y:
            was_falling_or_standing = True

        if mario_3:
            if mario_3.box.y >= mario_2.box.y and mario_2.box.y == mario_1.box.y:
                was_jumping_and_reached_top = True

        # FIXME: we need to consider collisions with other objects such as ememies

        if not on_the_ground:
            if was_jumping_and_reached_top and before.keys.key_code("a") in before.keys:
                # Jump key is pressed when Mario is on the top of his jump
                debug("Mario should stay in the air or start falling")
                assert (
                    mario_0.box.y >= mario_1.box.y
                ), "Mario should stay in the air or start falling"

            elif was_falling_or_standing:
                debug("Mario should fall")
                assert mario_0.box.y > mario_1.box.y, "Mario did not fall"

    def expect_die(self):
        """Expect Mario to die."""
        pass

    def expect_big_mario(self):
        """Expect Mario to become big."""
        pass

    def expect_fire_mario(self):
        """Expect Mario to become fire."""
        pass

    def expect_small_mario(self):
        """Expect Mario to become small."""
        pass

    def expect(self, behavior):
        """Expect Mario to behave correctly."""
        if len(behavior) < 2:
            # Not enough data to make a decision
            return

        before = behavior[-2]
        now = behavior[-1]

        try:
            self.expect_move_right(before, now, behavior)
            self.expect_move_left(before, now, behavior)
            self.expect_jump(before, now, behavior)
            self.expect_fall(before, now, behavior)

        except AssertionError as e:
            dump("player", behavior)
            raise
