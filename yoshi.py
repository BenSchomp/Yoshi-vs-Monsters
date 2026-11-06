import asyncio, pygame, random, sys
from pygame.locals import *

# game constants
GAME_WIDTH = 750
GAME_HEIGHT = 600
HORIZON_HEIGHT = GAME_HEIGHT * 2 // 3

ONE_SEC = 1000

TEXT_COLOR =    (255,255,255)
SKY_COLOR =    [(66,138,255), (255,120,0), (72,0,155), (28,0,63), (20,0,24)]
GROUND_COLOR = [(0,127,14), (0,89,14), (0,53,8), (0,33,4), (0,16,4)]
SUN_COLOR =    [(255,216,0), (255,216,0), (255,255,125), (255,255,125), (255,255,125)]
SUN_LOC =      [(550,150), (650,300), (-100,-100), (200,300), (300,200), (275,75)]
STAR_LOCS =    [[],[], [(200,100), (300,250), (500,50)],
                       [(325,100), (600,150), (500,50)],
                       [(550,200), (675,75), (500,50)]]

FPS = 40
MONSTER_MIN_SCALE = 6
MONSTER_MIN_SPEED = 1
MONSTER_MAX_SPEED = 5
NUMBER_OF_MONSTERS = 5
MAX_MONSTER_RATE = [110,90,70,50,30,15]

APPLE_TYPE = 0
# Each drop is a random pick of the 5 types (so ~1 in 5 is an apple), except:
# never two apples in a row, and if no apple has dropped for this long, the next drop is one.
MAX_SECONDS_WITHOUT_APPLE = 20
NUM_LEVELS = 5
APPLE_POINTS = [200, 250, 300, 400, 500]
LEVEL_UP_APPLES = [5,6,7,8,9]
LEVEL_UP_BONUS = [500, 1000, 2000, 3500, 5000]
FREE_GUY_POINTS = [25000, 75000]

YOSHI_SPEED = 5
MUSIC_VOL = 0.3
SOUND_VOL = 0.8

# web port: a browser tab can't be "quit", so quitting only works on desktop
RUNNING_IN_BROWSER = sys.platform == 'emscripten'
HIGH_SCORE_STORAGE_KEY = 'yoshi-vs-monsters-hiscore'

# util functions
def terminate():
    if RUNNING_IN_BROWSER:
        return
    pygame.quit()
    sys.exit()

async def waitForKeyPress():
    """Waits for a key to be released and returns which key it was."""
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            if event.type == KEYUP:
                return event.key
            if event.type == MOUSEBUTTONUP: # a click works like "any key"
                return None
        pygame.display.update() # keep the screen drawn even if the browser resized the canvas
        await asyncio.sleep(1 / FPS) # let the browser draw and deliver key events, without spinning the CPU

# Pauses keep pumping window events. If a window stops reading events for a
# few seconds, macOS shows the spinning beach ball (and the browser can stall).
async def waitWhileSoundPlays(channel):
    while channel is not None and channel.get_busy():
        pygame.event.pump()
        await asyncio.sleep(0.05)

async def pauseWithoutFreezing(milliseconds):
    pauseEndsAt = pygame.time.get_ticks() + milliseconds
    while pygame.time.get_ticks() < pauseEndsAt:
        pygame.event.pump()
        await asyncio.sleep(0.05)

def loadHighScore():
    try:
        if RUNNING_IN_BROWSER:
            import platform
            storedScore = platform.window.localStorage.getItem(HIGH_SCORE_STORAGE_KEY)
            return int(storedScore) if storedScore else 0
        with open('data/hiscore.dat', 'r') as f:
            x = f.readline()
            return int(x) if x.isdigit() else 0
    except (IOError, ValueError):
        return 0

def saveHighScore(highScore):
    if RUNNING_IN_BROWSER:
        import platform
        platform.window.localStorage.setItem(HIGH_SCORE_STORAGE_KEY, str(highScore))
        return
    with open('data/hiscore.dat', 'w') as f:
        f.write(str(highScore))
            
def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, TEXT_COLOR)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def drawTextBox(text, parent, spacing=2):
    """Each line is a string (drawn in `font`) or a (string, font) pair for a different size."""
    linesWithFonts = [line if isinstance(line, tuple) else (line, font) for line in text]
    textobjs = [(lineFont.render(line, 1, TEXT_COLOR), lineFont.get_linesize())
                for line, lineFont in linesWithFonts]
    padding = 40

    # each line takes its font's height, times the spacing (except after the last line)
    boxwidth = max(t.get_width() for t, _ in textobjs)
    boxheight = sum(linesize * spacing for _, linesize in textobjs) - textobjs[-1][1] * (spacing - 1)

    # add margins
    boxwidth += padding
    boxheight += padding

    # center textbox rectangle on parent
    textboxRect = pygame.Rect(0,0,boxwidth,boxheight)
    # sit a third of the way down, or lower if the box is too tall to fit there
    textboxRect.center = (parent.get_width() / 2, max(parent.get_height() / 3, boxheight / 2))

    # create textbox subsurface
    textbox = parent.subsurface(textboxRect)
    textbox.fill((0,0,0))
    pygame.draw.rect(parent, TEXT_COLOR, textboxRect, 2)

    # blit each textobj on the textbox surface
    y = padding / 2
    for t, linesize in textobjs:
        textrect = t.get_rect()
        textrect.center = (boxwidth / 2, y + (linesize / 2))
        textbox.blit(t, textrect)
        y += linesize * spacing

# M is "mute": it silences everything, and a second M brings back the music
# and whatever the sound effects were before muting.
# S flips the sound effects on or off, muted or not (so M then S = sound effects only).
# Music plays whenever the game isn't muted.
muted = False
soundEffectsOn = True
soundEffectsOnBeforeMute = True

def applyVolumes():
    for s in sounds.values():
        s.set_volume(SOUND_VOL if soundEffectsOn else 0)
    pygame.mixer.music.set_volume(MUSIC_VOL if not muted else 0)

def toggleMusicOrSoundsForKey(pressedKey):
    """Handles M and S. Returns True if the key was one of them."""
    global muted, soundEffectsOn, soundEffectsOnBeforeMute
    if pressedKey == ord('m'):
        if muted:
            muted = False
            soundEffectsOn = soundEffectsOnBeforeMute
        else:
            muted = True
            soundEffectsOnBeforeMute = soundEffectsOn
            soundEffectsOn = False
    elif pressedKey == ord('s'):
        soundEffectsOn = not soundEffectsOn
        if muted: # remember a choice made while muted for when M unmutes
            soundEffectsOnBeforeMute = soundEffectsOn
    else:
        return False
    applyVolumes()
    return True

def onOff(isOn):
    return 'ON' if isOn else 'OFF'

def withQuitHint(lines):
    """The quit option only exists on desktop; a browser tab can't quit."""
    return lines if RUNNING_IN_BROWSER else lines + ['', '[q] quit']

async def waitForKeyToContinue():
    """Title and game-over screens: Q quits (desktop only), any other key continues."""
    pressedKey = await waitForKeyPress()
    if pressedKey == ord('q'):
        terminate()

PAUSE_KEYS = (K_ESCAPE, K_SPACE) # either one pauses, and either one resumes

async def confirmRestart(gameScreenBehindMenu):
    """Returns True if the player confirms with Y; N or Esc cancels."""
    windowSurface.blit(gameScreenBehindMenu, (0, 0))
    drawTextBox(['Are you sure?', 'All progress will be lost.', '',
                 '[y] Yes   /   [n] No'], windowSurface, spacing=1)
    pygame.display.update()
    while True:
        pressedKey = await waitForKeyPress()
        if pressedKey == ord('y'):
            return True
        if pressedKey in (ord('n'), K_ESCAPE):
            return False

async def showPauseMenu():
    """Esc or space pauses the game. The menu lists the keys, can toggle music and
    sounds, and can restart. Returns True if the player chose to restart."""
    restartRequested = False
    gameScreenBehindMenu = windowSurface.copy()
    # Pause playback rather than turning the volume down: a sound cut off by a
    # volume change mid-play could get stuck repeating in the browser.
    pygame.mixer.pause()
    pygame.mixer.music.pause()
    while True:
        menuLines = withQuitHint(['PAUSED', '',
                                  '-- Use the arrow keys to move --',
                                  '[m] mute: ' + onOff(muted),
                                  '[s] sound effects: ' + onOff(soundEffectsOn),
                                  '[r] restart',
                                  '[esc] or [space] resume'])
        windowSurface.blit(gameScreenBehindMenu, (0, 0))
        drawTextBox(menuLines, windowSurface, spacing=1)
        pygame.display.update()

        pressedKey = await waitForKeyPress()
        if pressedKey == ord('q'):
            terminate()
        elif toggleMusicOrSoundsForKey(pressedKey): # playback is paused, so this stays silent until resume
            pass
        elif pressedKey == ord('r'):
            if await confirmRestart(gameScreenBehindMenu):
                restartRequested = True
                break
        elif pressedKey in PAUSE_KEYS:
            break
    pygame.mixer.unpause()
    pygame.mixer.music.unpause()
    if restartRequested:
        pygame.mixer.stop() # drop whatever sound effects were mid-play
    return restartRequested


################################################################################


# setup pygame, the window, and mouse cursor
# Browser audio runs on the same thread as the game, so the default small mixer
# buffer runs dry between frames and crackles. A bigger buffer smooths it out
# (sound effects start ~90ms later, which isn't noticeable here).
if RUNNING_IN_BROWSER:
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
pygame.init()
mainClock = pygame.time.Clock()
windowSurface = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption('Yoshi vs. Monsters')
pygame.mouse.set_visible(False)


# setup fonts
font = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)
font_original_version_line = pygame.font.SysFont(None, 30) # slightly smaller, for the v0.4 credit

# setup sounds & music (OGG, because browsers can't play WAV reliably or MIDI at all)
# source -- http://www.mfgg.net/index.php?act=resdb&param=03&c=5&id=24121
sounds = {'gameOver': pygame.mixer.Sound('data/gameover.ogg'),
          'yoshi':    pygame.mixer.Sound('data/yoshiii.ogg'),
          'owow':     pygame.mixer.Sound('data/owow.ogg'),
          'tongue':   pygame.mixer.Sound('data/tongue.ogg'),
          'appleX':   pygame.mixer.Sound('data/apple_loss.ogg'),
          'eggX':     pygame.mixer.Sound('data/egg_loss.ogg'),
          'ba-ding':  pygame.mixer.Sound('data/ba-ding.ogg'),
          'woah':     pygame.mixer.Sound('data/woah.ogg'), }
pygame.mixer.music.load('data/confutatis.ogg')
applyVolumes()

# setup images
yoshiImage = pygame.image.load('data/yoshi.png')
yoshiImage = yoshiImage.convert_alpha()
yoshiRect = yoshiImage.get_rect()
facingLeft = False

eggImage        = pygame.transform.scale(pygame.image.load('data/egg1.png'),(30,36))
appleImage      = pygame.transform.scale(pygame.image.load('data/apple1.png'), (25,27))
blankAppleImage = pygame.transform.scale(pygame.image.load('data/apple2.png'), (25,27))

monsterImages = [pygame.image.load('data/apple1.png'), # APPLE_TYPE is 0 index
                 pygame.image.load('data/monster1.png'),
                 pygame.image.load('data/monster2.png'),
                 pygame.image.load('data/monster3.png'),
                 pygame.image.load('data/monster4.png'),
                ]
for mi in monsterImages:
    mi = mi.convert_alpha()
    
monsterSizes = [[40,43], # apple1.png
                [68,63], [70,73], [51,58], [53,76]]

async def main():
    global facingLeft, yoshiImage
    ch = None # sound channel of the most recent effect
    # draw welcome screen
    windowSurface.fill(SKY_COLOR[0])
    drawTextBox(withQuitHint(['Yoshi vs. Monsters!!!',
                 '',
                 'Avoid the Monsters, eat the Apples.',
                 '',
                 '-- Use the arrow keys to move --',
                 '[esc]/[space] pause : [m]ute : [s]ounds',
                 '',
                 'PRESS ANY KEY OR CLICK TO START',
                 '',
                 ('v0.4 March 29, 2011', font_original_version_line),
                 'v0.5 November 6, 2026',
                 'by Elsie, Charlie & Ben Schomp']), windowSurface, spacing=1)
    pygame.display.update()
    await waitForKeyToContinue()

    # load high score
    highScore = loadHighScore()

    while True: # the program loop
        # a new game!
        score = 0
        level = 0
        appleCount = 0
        numberOfLives = 3
        gameWon = False
        restartRequested = False
        highScoreText = ''

        sounds['yoshi'].play()
        while numberOfLives > 0 and not gameWon: # the game loop
            # still alive!

            appleCount = 0 # reset the apples (maybe halve this on death?)
            pygame.mixer.music.play(-1,0.0) # start the music

            # reset monsters
            monsters = []
            previousDropWasApple = False
            framesSinceLastApple = 0
            newMonsterRate = MAX_MONSTER_RATE[level]
            monsterAddCounter = MAX_MONSTER_RATE[level] * 3 // 4

            # reset yoshi
            yoshiRect.center = (GAME_WIDTH / 2, GAME_HEIGHT - 120)
            moveLeft = moveRight = moveUp = moveDown = False
            if facingLeft:
                yoshiImage = pygame.transform.flip(yoshiImage, 1, 0)
                facingLeft = False

            playing = True
            while playing: # the event loop

                # process events
                for event in pygame.event.get():
                    if event.type == QUIT:
                        terminate()

                    if event.type == KEYDOWN:
                        #if event.key == ord('1'): level = 0
                        #if event.key == ord('2'): level = 1
                        #if event.key == ord('3'): level = 2
                        #if event.key == ord('4'): level = 3
                        #if event.key == ord('5'): level = 4

                        if event.key == K_LEFT:  moveLeft = True;  moveRight = False
                        if event.key == K_RIGHT: moveLeft = False; moveRight = True
                        if event.key == K_UP:    moveDown = False; moveUp = True
                        if event.key == K_DOWN:  moveDown = True;  moveUp = False

                    if event.type == KEYUP:
                        if event.key == K_LEFT:  moveLeft = False
                        if event.key == K_RIGHT: moveRight = False
                        if event.key == K_UP:    moveUp = False
                        if event.key == K_DOWN:  moveDown = False

                        toggleMusicOrSoundsForKey(event.key)
                        if event.key in PAUSE_KEYS:
                            restartRequested = await showPauseMenu()
                            if restartRequested:
                                playing = False
                            moveLeft = moveRight = moveUp = moveDown = False # keys may have been released while paused

                # end event processing

                # add a new monster?
                monsterAddCounter += 1
                framesSinceLastApple += 1
                if monsterAddCounter >= newMonsterRate:
                    monsterAddCounter = 0
                    if newMonsterRate > MAX_MONSTER_RATE[level+1]:
                        newMonsterRate -= 1

                    monsterScale = (random.randint (MONSTER_MIN_SCALE,10) * 10) / 100.0 # {.6, .7, .8, .9, 1.0}
                    if previousDropWasApple:
                        monsterType = random.randint(1, NUMBER_OF_MONSTERS-1) # any non-apple
                    elif framesSinceLastApple >= MAX_SECONDS_WITHOUT_APPLE * FPS:
                        monsterType = APPLE_TYPE
                    else:
                        monsterType = random.randint(0, NUMBER_OF_MONSTERS-1)
                    previousDropWasApple = monsterType == APPLE_TYPE
                    if previousDropWasApple:
                        framesSinceLastApple = 0
                    monsterWidth = int(monsterSizes[monsterType][0] * monsterScale)
                    monsterHeight = int(monsterSizes[monsterType][1] * monsterScale)
                    monsterSurface = pygame.transform.scale(monsterImages[monsterType], (monsterWidth, monsterHeight))
                    newMonster = {'rect': pygame.Rect(random.randint(0, GAME_WIDTH-monsterWidth),0, monsterWidth, monsterHeight),
                                  'speed': random.randint(MONSTER_MIN_SPEED+level, MONSTER_MAX_SPEED+level),
                                  'surface': monsterSurface,
                                  'mask': pygame.mask.from_surface(monsterSurface), # opaque pixels only, for collisions
                                  'type': monsterType,
                                  }
                    monsters.append(newMonster)
                    # debug: print 'New Monster, Type %d: [%d, %d] * %f = [%d, %d]' % (monsterType, monsterSizes[monsterType][0], monsterSizes[monsterType][1], monsterScale, monsterWidth, monsterHeight)

                # move yoshi around
                if moveLeft and yoshiRect.left > 0:
                    yoshiRect.move_ip(-1 * YOSHI_SPEED, 0)
                    if not facingLeft:
                        yoshiImage = pygame.transform.flip(yoshiImage, 1, 0)
                        facingLeft = True
                if moveRight and yoshiRect.right < GAME_WIDTH:
                    yoshiRect.move_ip(YOSHI_SPEED, 0)
                    if facingLeft:
                        yoshiImage = pygame.transform.flip(yoshiImage, 1, 0)
                        facingLeft = False
                if moveUp and yoshiRect.bottom > HORIZON_HEIGHT + 30:
                    yoshiRect.move_ip(0, -1 * YOSHI_SPEED)
                if moveDown and yoshiRect.bottom < GAME_HEIGHT - 42:
                    yoshiRect.move_ip(0, YOSHI_SPEED)

                # move monsters down
                for m in monsters:
                    m['rect'].move_ip(0, m['speed'])
                    if m['rect'].top > GAME_HEIGHT:
                        monsters.remove(m)
                        if m['type'] == APPLE_TYPE and appleCount > 0:
                            sounds['appleX'].play()
                            appleCount -= 1

                # draw the game world on the window
                windowSurface.fill(SKY_COLOR[level])
                pygame.draw.circle(windowSurface, SUN_COLOR[level], SUN_LOC[level], 60)
                if level >= 2:
                    for s in STAR_LOCS[level]:
                        pygame.draw.circle(windowSurface, SUN_COLOR[level], s, 3)
                pygame.draw.rect(windowSurface, GROUND_COLOR[level],
                                 pygame.Rect(0,HORIZON_HEIGHT,
                                             GAME_WIDTH,HORIZON_HEIGHT))

                # draw scores
                drawText('Score: %s' % (score), font, windowSurface, 10, 2)
                drawText('Level: %s' % (level+1), font, windowSurface, 650, 2)
                drawText('High Score: %s' % (highScore), font_small, windowSurface, 300, 5)
                # debug drawText('newMonsterRate: %s' % (newMonsterRate), font_small, windowSurface, 200, GAME_HEIGHT-30)

                # draw yoshi
                windowSurface.blit(yoshiImage, yoshiRect)

                # draw each monster
                for m in monsters:
                    windowSurface.blit(m['surface'], m['rect'])

                # draw life eggs
                for egg in range (0, numberOfLives):
                    eggRect = pygame.Rect((40*egg)+5, GAME_HEIGHT-40, 30, 36)
                    windowSurface.blit(eggImage, eggRect)

                # check if any monster has hit yoshi
                # Monsters only count when their visible pixels overlap Yoshi's, not just
                # their rectangles (which include transparent corners). Apples stay
                # rectangle-based so they're easy to catch.
                yoshiMask = pygame.mask.from_surface(yoshiImage)
                for m in monsters:
                    if not yoshiRect.colliderect(m['rect']):
                        continue
                    offsetFromYoshi = (m['rect'].x - yoshiRect.x, m['rect'].y - yoshiRect.y)
                    if m['type'] == APPLE_TYPE or yoshiMask.overlap(m['mask'], offsetFromYoshi):
                        if m['type'] == APPLE_TYPE:
                            ch = sounds['tongue'].play()
                            score += APPLE_POINTS[level]
                            appleCount += 1
                            # +500 animation? #drawText('+%d' % (APPLE_POINTS), font_small, m['surface'], m['rect'].x, m['rect'].y)
                            monsters.remove(m)
                        else:
                            # monster collision
                            pygame.mixer.music.stop()
                            ch = sounds['owow'].play()
                            numberOfLives -= 1
                            playing = False
                            break

                # draw appleCount
                for apple in range (0, LEVEL_UP_APPLES[level]):
                    appleRect = pygame.Rect(GAME_WIDTH-30-(30*apple),
                                            GAME_HEIGHT-30, 25, 27)
                    windowSurface.blit(appleImage if apple < appleCount else
                                       blankAppleImage, appleRect)

                # update the screen
                pygame.display.update()
                mainClock.tick(FPS)
                await asyncio.sleep(0) # hand control back to the browser each frame
                score += 1
                if FREE_GUY_POINTS and score > FREE_GUY_POINTS[0]:
                    FREE_GUY_POINTS.pop(0)
                    numberOfLives += 1
                    sounds['ba-ding'].play()

                if appleCount >= LEVEL_UP_APPLES[level]:
                    if ch: ch.queue(sounds['yoshi'])
                    appleCount = 0
                    score += LEVEL_UP_BONUS[level]
                    level += 1
                    if level >= NUM_LEVELS:
                        if ch: ch.queue(sounds['woah'])
                        playing = False
                        gameWon = True

            # -- end of event loop (still playing?) --

            if restartRequested:
                break # skip the lost-life sequence

            # in case the music is still going
            pygame.mixer.music.stop()

            # check end of game conditions
            if numberOfLives <= 0:
                ch = sounds['gameOver'].play()
            elif gameWon:
                break # don't subtract an egg

            # wait a bit...
            await waitWhileSoundPlays(ch)
            await pauseWithoutFreezing(ONE_SEC)

            # erase egg + sound effect
            pygame.draw.rect(windowSurface, GROUND_COLOR[level], eggRect )
            ch = sounds['eggX'].play()
            pygame.display.update();

            # wait again...
            await waitWhileSoundPlays(ch)
            await pauseWithoutFreezing(ONE_SEC)

            await pauseWithoutFreezing(ONE_SEC)
            pygame.event.clear()

        # -- end of game loop (still alive?) --

        if restartRequested: # straight into a new game: no game over screen or high score
            pygame.mixer.music.stop()
            pygame.event.clear()
            continue

        # game over :(
        pygame.mixer.music.stop()

        if score > highScore:
            highScore = score # new high score!
            highScoreText = 'New High Score!'
            saveHighScore(highScore)

        if gameWon:
            drawTextBox(withQuitHint(['CONGRATULATIONS!!!', '',
                         'You beat Yoshi vs. Monsters!',
                         '',
                         'Coming soon:',
                         'Yoshi vs. Robots!',
                         '', highScoreText, '',
                         'Press any key to play again...']),
                         windowSurface, spacing=1)
        else:
            drawTextBox(withQuitHint(['GAME OVER', '', highScoreText, '',
                         'Press any key to play again...']),
                         windowSurface, spacing=1)

        pygame.display.update()
        await pauseWithoutFreezing(ONE_SEC)
        pygame.event.clear()
        await waitForKeyToContinue()

        sounds['gameOver'].stop()
        gameOver = False

    # -- end of program loop (infinite)



if __name__ == '__main__':
    asyncio.run(main())
