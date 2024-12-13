from testflows.core import debug
from .base import Model

# BUG? pressing a and left or right will not result in jump
# FIXME: mario is invincible for some time when transforming from big to small

# BUG? first x is evaluated then y?
# FIXME: jump moving right and touching the edge of the obstacle
# 293ms     ⟥    [debug] 7 Keys: Keys(left,a) Player: 2535, 328         - here y touches pipe
#           39s 293ms     ⟥    [debug] 8 Keys: Keys(left,a) Player: 2530, 324 - here mario is stoppped by the pipe but jump continues up but x speed now is 0!
#           39s 293ms     ⟥    [debug] 9 Keys: Keys(left,a) Player: 2530, 320
#           39s 293ms     ⟥    [debug] Keys: {'pipe': [Element(name='pipe', box=<rect(2444, 366, 86, 170)>, id=129006182620880)], 'collider': [Element(name='collider', box=<rect(0, 538, 2953, 60)>, id=129006284272448), Element(name='collider', box=<rect(3048, 538, 635, 60)>, id=129006182615984)], 'player': [Element(name='player', box=<rect(2530, 320, 30, 40)>, id=129006182761808)]}


def find_element(name, state):
    """Find element in the specified state."""
    elements = state.boxes.get(name, [])
    element = elements[0] if elements else None

    return element


def find_mario(state):
    """Find Mario in the specified state."""
    return find_element("player", state)


def top_touch(box1, box2):
    """
    Check if box1's top edge touches box2's bottom edge.

    Args:
        box1 (pg.Rect): The first rectangle.
        box2 (pg.Rect): The second rectangle.

    Returns:
        bool: True if box1's top edge touches box2's bottom edge, False otherwise.
    """
    touched = (box1.top == box2.bottom) and (
        (box1.right > box2.left and box1.right <= box2.right)
        or (box1.left < box2.right and box1.left >= box2.left)
    )
    return touched


def bottom_touch(box1, box2):
    """
    Check if box1's bottom edge touches box2's top edge.

    Args:
        box1 (pg.Rect): The first rectangle.
        box2 (pg.Rect): The second rectangle.

    Returns:
        bool: True if box1's bottom edge touches box2's top edge, False otherwise.
    """
    touched = (box1.bottom == box2.top) and (
        (box1.right > box2.left and box1.right <= box2.right)
        or (box1.left < box2.right and box1.left >= box2.left)
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
        box1.left < box2.left and box1.right >= box2.left and box1.right < box2.right
    ) and (
        ((box1.bottom > box2.top) and (box1.bottom <= box2.bottom))
        or ((box1.top < box2.bottom) and (box1.top >= box2.top))
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
        box1.left > box2.left and box1.left <= box2.right and box1.right > box2.right
    ) and (
        ((box1.bottom > box2.top) and (box1.bottom <= box2.bottom))
        or ((box1.top < box2.bottom) and (box1.top >= box2.top))
    )
    return touched


def has_right_collision(game, element, state, objects=None):
    """Check if the element has a right collision with another object."""
    boxes = []

    if objects is None:
        objects = state.boxes.keys()

    for name in objects:
        boxes += state.boxes.get(name, [])

    for box in boxes:
        if box is element:
            continue
        if right_touch(element.box, box.box):
            # Touched another object
            overlay(game, elements=[element, box], color=[0, 255, 0])
            return True

    return False


def has_left_collision(game, element, state, objects=None):
    """Check if the element has a left collision with another object."""
    boxes = []

    if objects is None:
        objects = state.boxes.keys()

    for name in objects:
        boxes += state.boxes.get(name, [])

    for box in boxes:
        if box is element:
            continue
        if left_touch(element.box, box.box):
            # Touched another object
            overlay(game, elements=[element, box])
            return True

    return False


def has_bottom_collision(game, element, state, objects=None):
    """Check if the element has a bottom collision with another solid object."""
    boxes = []

    if objects is None:
        objects = state.boxes.keys()

    for name in objects:
        boxes += state.boxes.get(name, [])

    for box in boxes:
        if bottom_touch(element.box, box.box):
            # Touched another object
            overlay(game, elements=[element, box])
            return True

    return False


def has_top_collision(game, element, state, objects=None):
    """Check if the element has a top collision with another solid object."""
    boxes = []

    if objects is None:
        objects = state.boxes.keys()

    for name in objects:
        boxes += state.boxes.get(name, [])

    for box in boxes:
        if top_touch(element.box, box.box):
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

    class State:
        def __init__(self):
            self.died = False
            self.small = True
            self.big = False
            self.fire = False
            self.invincible = False

    def __init__(self, game):
        super().__init__(game)
        self.state = Mario.State()

    # FIXME: move right collision with the "pole" and "poletop"
    # FIXME: move left collision with bottom edge of brick

    def expect_move_right(self, before, now, behavior):
        """Expect Mario to move right."""

        was_standing = False
        was_moving_left = False

        mario_right_before = find_mario(behavior[-3])
        mario_before = find_mario(before)
        mario_now = find_mario(now)

        if not mario_right_before or not mario_before or not mario_now:
            # Mario is not in the previous or current state
            return

        if has_right_collision(self.game, mario_now, now):
            # Mario has right collision
            debug("Mario has right collision")
            return

        if mario_right_before.box.x == mario_before.box.x:
            # Mario was standing still
            was_standing = True

        elif mario_right_before.box.x > mario_before.box.x:
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
        assert mario_before.box.x < mario_now.box.x, "Mario did not move right"

    def expect_move_left(self, before, now, behavior):
        """Expect Mario to move left."""

        was_standing = False
        was_moving_right = False

        mario_right_before = find_mario(behavior[-3])
        mario_before = find_mario(before)
        mario_now = find_mario(now)

        if not mario_right_before or not mario_before or not mario_now:
            # Mario is not in the previous or current state
            return

        if has_left_collision(self.game, mario_now, now):
            # Mario has left collision
            debug("Mario has left collision")
            return

        if mario_now.box.left == 0:
            # Touched left edge of the world
            return

        if mario_right_before.box.x == mario_before.box.x:
            # Mario was standing still
            was_standing = True

        elif mario_right_before.box.x < mario_before.box.x:
            # Mario was moving right
            was_moving_right = True

        if now.keys.key_code("left") not in now.keys:
            # Move left key is not pressed
            return

        if was_standing or was_moving_right:
            return

        # FIXME: handle Mario transforming (small to big, big to fire, etc.)

        debug("Mario should move left")
        assert mario_before.box.x > mario_now.box.x, "Mario did not move left"

    def expect_jump(self, before, now, behavior):
        """Expect Mario to jump."""
        on_the_ground_right_before = False
        on_the_ground_before = False
        jump_key_pressed_before = False
        jump_key_pressed_now = False
        in_jump_before = False
        top_collision_before = False

        right_before = behavior[-3]

        mario_right_before = find_mario(right_before)
        mario_before = find_mario(before)
        mario_now = find_mario(now)

        # FIXME: we need to assert full jump sequence where mario reaches the top of the jump
        # jump sequence completes either on
        # 1. reaching the top of the jump due to gravity
        # 2. hitting obstacle on the top

        if not mario_right_before or not mario_before or not mario_now:
            # Mario is not in the previous or current state
            return

        if has_top_collision(self.game, mario_before, before):
            top_collision_before = True

        if has_bottom_collision(self.game, mario_right_before, right_before):
            on_the_ground_right_before = True

        if has_bottom_collision(self.game, mario_before, before):
            on_the_ground_before = True

        if mario_before.box.y < mario_right_before.box.y:
            in_jump_before = True

        if before.keys.key_code("a") in before.keys:
            jump_key_pressed_before = True

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
            assert mario_now.box.y < mario_before.box.y, "Mario did not jump"

        if in_jump_before:
            debug("Mario should not be on the ground while in jump")
            assert (
                on_the_ground_before is False
            ), "Mario should not be on the ground while in jump"

            if not top_collision_before:
                debug("Mario should continue rising or reach the top of the jump")
                assert (
                    mario_now.box.y <= mario_before.box.y
                    or mario_now.box.y > mario_before.box.y
                ), "Mario should continue rising or reach the top of the jump"

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

        if has_bottom_collision(self.game, mario_1, before):
            on_the_ground = True

        if mario_2.box.y <= mario_1.box.y:
            was_falling_or_standing = True

        if mario_3:
            if mario_3.box.y >= mario_2.box.y and mario_2.box.y == mario_1.box.y:
                was_jumping_and_reached_top = True

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

    def expect_die(self, before, now, behavior):
        """Expect Mario to die."""

        enemy_objects = ["goomba", "koopa", "piranha", "plant", "spiny"]

        mario_before = find_mario(before)
        mario_now = find_mario(now)

        if not mario_before or not mario_now:
            return

        if has_right_collision(self.game, mario_now, now, objects=enemy_objects):
            debug("Mario dies if touches enemy on the right")
            self.state.died = True
            return

        if has_left_collision(self.game, mario_now, now, objects=enemy_objects):
            debug("Mario dies if touches enemy on the left")
            self.state.died = True
            return

        if mario_now.box.bottom >= self.game.vision.viewport.height:
            debug("Mario dies if falls into the abyss")
            self.state.died = True
            return

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
            self.expect_die(before, now, behavior)

            if not self.state.died:
                self.expect_move_right(before, now, behavior)
                self.expect_move_left(before, now, behavior)
                self.expect_jump(before, now, behavior)
                self.expect_fall(before, now, behavior)

        except AssertionError as e:
            dump("player", behavior)
            raise
