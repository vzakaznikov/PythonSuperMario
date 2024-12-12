from testflows.core import debug

from .base import Model


class Box(Model):
    """Model for the behavior of solid blocks in the game."""

    class State:
        def __init__(self):
            self.bumped = False

    def __init__(self, game, name="box", color="green", bump_frames=15):
        super().__init__(game)
        self.color = self.game.vision.COLOR_MAP[color]
        self.name = name
        self.bump_frames = bump_frames
        # recorded state of blocks
        self.state = {}

    def are_boxes_same(self, box1, box2, tolerance=0):
        """
        Compare two bounding boxes to determine if they are the same within a given tolerance.

        Args:
            box1: The first bounding box as a tensor of [x, y, w, h].
            box2: The second bounding box as a tensor of [x, y, w, h].
            tolerance (float): The maximum allowed difference for coordinates to be considered equal.

        Returns:
            bool: True if the boxes are the same within the tolerance, False otherwise.
        """
        # Compute the absolute difference between the two boxes
        x = abs(box1.x - box2.x)
        y = abs(box1.y - box2.y)
        w = abs(box1.w - box2.w)
        h = abs(box1.h - box2.h)
        differences = [x, y, w, h]

        # Check if all differences are within the tolerance
        return all([d <= tolerance for d in differences])

    def bottom_touch(self, box1, box2):
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

    def find_block(self, block, state):
        """Find the block in the specified state."""
        this_block = None

        for box in state.boxes.get(self.name, []):
            if box.id == block.id:
                this_block = box
                break

        assert this_block, f"Block {self.name} {block} was not found"

        return this_block

    def find_mario(self, state):
        """Find Mario in the specified state."""
        mario = state.boxes.get("player", [])
        mario = mario[0] if mario else None

        return mario

    def is_closer(self, block, brick, mario):
        """Check if the block is closer to Mario than the brick."""
        brick_distance = abs(mario.box.centerx - brick.box.centerx)
        block_distance = abs(mario.box.centerx - block.box.centerx)

        return brick_distance < block_distance

    def expect_stay(self, block, behavior):
        """Expect the block to stay in the same place."""

        if len(behavior) < 2:
            # Not enough data to make a decision
            return

        state = behavior[-1]
        viewport = state.viewport

        if not self.game.vision.in_view(block.box, viewport):
            # Block is not in the current view
            return

        # Find the block in the current state
        this_block = self.find_block(block, state)
        # Check block position is the same
        matched = self.are_boxes_same(this_block.box, block.box)

        if not matched:
            # overlay the missing block
            self.game.vision.overlay(
                boxes=[self.game.vision.adjust_box(block.box, viewport)],
                thickness=5,
                color=self.color,
            )
            assert matched, f"Block {self.name} {block} unexpectedly moved"

    def expect_bump(self, block, behavior):
        """Expect the block to be bumped."""

        if self.state[block.id].bumped:
            # Already bumped so we don't expect it to move again
            return

        behavior = behavior[-self.bump_frames :]

        bumped_block = None

        for i, state in enumerate(behavior[1:], 1):
            viewport = state.viewport

            if not self.game.vision.in_view(block.box, viewport):
                # Block is not in the current view
                continue

            this_block = self.find_block(block, state)
            mario = self.find_mario(state)

            if not mario:
                continue

            if self.bottom_touch(this_block.box, mario.box):
                # check conflict with bricks
                bricks = behavior[i - 1].boxes.get("brick", [])
                touched_bricks = [
                    brick for brick in bricks if self.bottom_touch(brick.box, mario.box)
                ]
                # if any bricks are closer than this block
                if any(
                    [
                        self.is_closer(this_block, brick, mario)
                        for brick in touched_bricks
                    ]
                ):
                    # skip this bump
                    break

                # check conflict with adjacent blocks
                # FIXME: looks like the closest block to the left is chosen
                other_blocks = state.boxes.get("box", [])
                touched_other_blocks = [
                    other_block
                    for other_block in other_blocks
                    if other_block is not this_block
                    and self.bottom_touch(other_block.box, mario.box)
                ]
                # if any other blocks are closer than this block
                if any(
                    [
                        self.is_closer(this_block, other_block, mario)
                        for other_block in touched_other_blocks
                    ]
                ):
                    # skip this bump
                    break

                bumped_block = (i, this_block)

                # overlay the bumped block
                self.game.vision.overlay(
                    boxes=[
                        self.game.vision.adjust_box(this_block.box, viewport),
                        self.game.vision.adjust_box(mario.box, viewport),
                    ],
                    thickness=5,
                    color=self.color,
                )

            # If block was bumped in the previous state
            if bumped_block and bumped_block[0] < i:
                if self.are_boxes_same(this_block.box, bumped_block[1].box):
                    # When block returns to its original position
                    # mark the block as bumped
                    self.state[block.id].bumped = True
                    debug(f"Block {self.name} {block} was bumped")
                    return True
                # expect block to return to its original position
                elif i - bumped_block[0] >= 11:
                    assert (
                        False
                    ), f"Block {self.name} {block} never returned to the original position"

        if bumped_block:
            return True

    def expect(self, behavior):
        """Expect the block to behave correctly."""

        if len(behavior) < 2:
            # Not enough data to make a decision
            return

        previous_state = behavior[-2]

        blocks = previous_state.boxes.get(self.name, [])

        for block in blocks:
            # Add the block to the state if it is not there
            if block.id not in self.state:
                self.state[block.id] = self.State()

            # Expect different behaviors
            (self.expect_bump(block, behavior) or self.expect_stay(block, behavior))
