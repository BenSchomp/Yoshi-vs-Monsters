# Entry point for the web build: pygbag runs main.py and needs the game loop to be async.
# On desktop you can keep running `python3 yoshi.py`.
import asyncio
import yoshi

asyncio.run(yoshi.main())
