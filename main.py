# Entry point for the web build: pygbag runs main.py and needs the game loop to be async.
# On desktop you can keep running `python3 yoshi.py`.
import asyncio

# pygbag only loads the packages it sees imported in main.py, so pygame must be
# imported here, before yoshi.py does `from pygame.locals import *`.
import pygame
import pygame.locals

import yoshi

asyncio.run(yoshi.main())
