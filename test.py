import time
import random
import pygame
import pygame as pg
import threading
from pygame.locals import KEYDOWN, K_RIGHT, K_SPACE, K_LEFT, KEYUP, K_a, QUIT
from game.source.main import main

import pyautogui

# Simulate holding keys for controlling Mario
def control_mario():
    time.sleep(2)  # Wait for the game to start
    print("Starting interactive control...")
    screen = pg.display.get_surface()

    for i in range(10):
        pg.image.save(screen, f"screenshot_{i}.png")
        # Simulate pressing and holding the RIGHT arrow key
        pyautogui.keyDown("right")
        time.sleep(2)  # Hold for 2 seconds
        pyautogui.keyUp("right")

        # Simulate pressing the SPACE key (jump)
        pyautogui.press("space")

        # Simulate pressing and holding the LEFT arrow key
        pyautogui.keyDown("left")
        time.sleep(1)  # Hold for 1 second
        pyautogui.keyUp("left")

    print("Finished interactive control.")

def test():
   for i in range(10):
       simulate_key_hold(K_a, random.random())
       time.sleep(1)

if __name__=='__main__':
    thread = threading.Thread(target=control_mario)
    thread.start()
    main()
    thread.join()
    pg.quit()
