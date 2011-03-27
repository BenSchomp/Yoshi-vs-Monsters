import pygame, random, sys
from pygame.locals import *

# constants
GAME_WIDTH = 750
GAME_HEIGHT = 750
HORIZON_HEIGHT = GAME_HEIGHT * 2/3

TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (66, 138, 255)
FOREGROUND_COLOR = (0, 127, 14)
SUN_COLOR = (255, 216, 0)

FPS = 40
MONSTER_MIN_SCALE = 6
MONSTER_MIN_SPEED = 1
MONSTER_MAX_SPEED = 5
NUMBER_OF_MONSTERS = 4
NEW_MONSTER_RATE = 100
YOSHI_SPEED = 5
MUTE = True

def terminate():
    pygame.quit()
    sys.exit()

def waitForKeyPress():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: # pressing esc quits
                    terminate()
                return
            
def yoshiHasHitMonster(yoshiRect, monsters):
    for m in monsters:
        if yoshiRect.colliderect(m['rect']):
            return True
    return False

def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, TEXT_COLOR)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def drawTextBox(text, parent, spacing=2):
    textobjs = []
    boxwidth, boxheight = 0, 0
    linesize = font.get_linesize() # recommended line height
    padding = 40

    for line in text:
        textobjs.append(font.render(line, 1, TEXT_COLOR)) # render line
        textwidth, textheight = font.size(line) # height is ignored

        if textwidth > boxwidth:
            boxwidth = textwidth # maintain width of longest line

    numlines = len(text) # number of lines to render = n + (n - 1)(s - 1)
    boxheight = linesize * (numlines * spacing - spacing + 1)

    boxwidth += padding
    boxheight += padding

    # center textbox rectangle on parent
    textboxRect = pygame.Rect(0,0,boxwidth,boxheight)
    textboxRect.center = (parent.get_width() / 2, parent.get_height() / 3)

    # create textbox subsurface
    textbox = parent.subsurface(textboxRect)
    textbox.fill((0,0,0))

    y = padding / 2
    for t in textobjs:
        textrect = t.get_rect()
        textrect.center = (boxwidth / 2, y + (linesize / 2))
        textbox.blit(t, textrect)
        y += linesize * spacing

###############################################################################


# setup pygame, the window, and mouse cursor
pygame.init()
mainClock = pygame.time.Clock()
windowSurface = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption('Yoshi vs. Monsters')
# pygame.mouse.set_visible(False)


# setup fonts
font = pygame.font.SysFont(None, 48)
font_small = pygame.font.SysFont(None, 24)

# setup sounds
gameOverSound = pygame.mixer.Sound('data/gameover.wav')
pygame.mixer.music.load('data/confutatis.mid')

# setup images
yoshiImage = pygame.image.load('data/yoshi.png')
yoshiImage = yoshiImage.convert_alpha()
yoshiRect = yoshiImage.get_rect()
monsterImages = [pygame.image.load('data/monster1.png'),
                 pygame.image.load('data/monster2.png'),
                 pygame.image.load('data/monster3.png'),
                 pygame.image.load('data/monster4.png')]
for mi in monsterImages:
    mi = mi.convert_alpha()
    
monsterSizes = [[68,63], [70,73], [51,58], [53,76]]

# draw welcome screen
windowSurface.fill(BACKGROUND_COLOR)
drawTextBox(['Yoshi vs. Monsters!!!', 'Press any key to start...'], windowSurface, spacing=3)
pygame.display.update()
waitForKeyPress()

highScore = 0
try:
    f = open('data/hiscore.dat', 'r')
    try:
        x = f.readline()
        if x.isdigit():
            highScore = int(x)
    finally:
        f.close()

except IOError:
    print 'File not found!'

while True:
    # setup the start of the game
    monsters = []
    score = 0
    highScoreText = ''
    newMonsterRate = NEW_MONSTER_RATE
    monsterAddCounter = NEW_MONSTER_RATE / 2
    yoshiRect.center = (GAME_WIDTH / 2, GAME_HEIGHT * 5/6)
    moveLeft = moveRight = moveUp = moveDown = facingLeft = False
    if not MUTE:
        pygame.mixer.music.play(-1,0.0)

    while True: #the game loop!!
        score = score + 1

        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()

            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    moveLeft = True
                    moveRight = False
                if event.key == K_RIGHT:
                    moveLeft = False
                    moveRight = True
                if event.key == K_UP:
                    moveUp = True
                    moveDown = False
                if event.key == K_DOWN:
                    moveUp = False
                    moveDown = True
                    
            if event.type == KEYUP:
                if event.key == K_ESCAPE: # pressing esc quits
                    terminate()
                if event.key == K_LEFT:
                    moveLeft = False
                if event.key == K_RIGHT:
                    moveRight = False
                if event.key == K_UP:
                    moveUp = False
                if event.key == K_DOWN:
                    moveDown = False

            #if event.type == MOUSEMOTION:          

        monsterAddCounter += 1
        if monsterAddCounter == newMonsterRate:
            monsterAddCounter = 0
            if newMonsterRate > 40:
                newMonsterRate -= 2

            monsterScale = (random.randint (MONSTER_MIN_SCALE,10) * 10) / 100.0 # {.6, .7, .8, .9, 1.0}
            monsterType = random.randint(0,NUMBER_OF_MONSTERS-1)
            monsterWidth = int(monsterSizes[monsterType][0] * monsterScale)
            monsterHeight = int(monsterSizes[monsterType][1] * monsterScale)
            newMonster = {'rect': pygame.Rect(random.randint(0, GAME_WIDTH-monsterWidth),0, monsterWidth, monsterHeight),
                          'speed': random.randint(MONSTER_MIN_SPEED, MONSTER_MAX_SPEED),
                          'surface': pygame.transform.scale(monsterImages[monsterType], (monsterWidth, monsterHeight)),
                          }
            monsters.append(newMonster)
            # print 'New Monster, Type %d: [%d, %d] * %f = [%d, %d]' % (monsterType, monsterSizes[monsterType][0], monsterSizes[monsterType][1], monsterScale, monsterWidth, monsterHeight)
            
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
        if moveDown and yoshiRect.bottom < GAME_HEIGHT:
            yoshiRect.move_ip(0, YOSHI_SPEED)

        # move monsters down
        for m in monsters:
            m['rect'].move_ip(0, m['speed'])
            if m['rect'].top > GAME_HEIGHT:
                monsters.remove(m)
             
        # move the mouse cursor to match the player
        #pygame.mouse.set_pos(yoshiRect.centerx, yoshiRect.centery)

        # draw the game world on the window
        windowSurface.fill(BACKGROUND_COLOR)
        pygame.draw.rect(windowSurface, FOREGROUND_COLOR, pygame.Rect(0,HORIZON_HEIGHT,GAME_WIDTH,HORIZON_HEIGHT))
        pygame.draw.circle(windowSurface, SUN_COLOR, (600, 100), 60)

        # draw scores
        drawText('Score: %s' % (score), font, windowSurface, 10, 0)
        drawText('High Score: %s' % (highScore), font_small, windowSurface, 10, 40)

        # draw yoshi
        windowSurface.blit(yoshiImage, yoshiRect)

        # draw each monster
        for m in monsters:
            windowSurface.blit(m['surface'], m['rect'])

        pygame.display.update()
   
        # check if any monster has hit yoshi
        if yoshiHasHitMonster(yoshiRect, monsters):
            if score > highScore:
                highScore = score # new high score!
                highScoreText = 'New High Score!'
                f = open('data/hiscore.dat', 'w')
                f.write(str(highScore))
                f.close()
                
            break

        mainClock.tick(FPS)

    # stop the game
    pygame.mixer.music.stop()
    if not MUTE:
        gameOverSound.play()

    drawTextBox(['GAME OVER', highScoreText, 'Press any key to play again...'], windowSurface)
    pygame.display.update()
    waitForKeyPress()

    gameOverSound.stop()




