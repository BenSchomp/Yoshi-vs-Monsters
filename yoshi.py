import pygame, random, sys
from pygame.locals import *

WINDOWWIDTH = 750
WINDOWHEIGHT = 750
HORIZON = 2 * (WINDOWHEIGHT/3)
TEXTCOLOR = (255, 255, 255)
BACKGROUNDCOLOR = (66, 138, 255)
FOREGROUNDCOLOR = (0, 127, 14)
SUNCOLOR = (255, 216, 0)
FPS = 40
MONSTERMINSIZE = 25
MONSTERMAXSIZE = 65
MONSTERMINSPEED = 1
MONSTERMAXSPEED = 5
NUMBEROFMONSTERS = 4
ADDNEWMONSTERRATE = 100
YOSHIMOVERATE = 5

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
    textobj = font.render(text, 1, TEXTCOLOR)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def drawTextBox(text, surface):
    textbox = surface.subsurface(pygame.Rect(200,200,400,200))
    textbox.fill((0,0,0))

# setup pygame, the window, and mouse cursor
pygame.init()
mainClock = pygame.time.Clock()
windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
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
windowSurface.fill(BACKGROUNDCOLOR)
#pygame.draw.rect(windowSurface, (0,0,0), pygame.Rect(200,200,200,200))
#drawText('Yoshi vs. Monsters!!!', font, windowSurface, (WINDOWWIDTH/3)-40, (WINDOWHEIGHT/3))
#drawText('Press any key to start...', font_small, windowSurface, (WINDOWWIDTH/3)+25, (WINDOWHEIGHT/3)+150)
drawTextBox("Hello World!", windowSurface)
pygame.display.update()
waitForKeyPress()

topScore = 0
try:
    f = open('data/hiscore.dat', 'r')
    try:
        x = f.readline()
        if x.isdigit():
            topScore = int(x)
    finally:
        f.close()

except IOError:
    print 'File not found!'

print 'topScore: ', topScore

while True:
    # setup the start of the game
    monsters = []
    score = 0
    newMonsterRate = ADDNEWMONSTERRATE
    yoshiRect.topleft = (WINDOWWIDTH/2, WINDOWHEIGHT - 100)
    moveLeft = moveRight = moveUp = moveDown = facingLeft = False
    monsterAddCounter = 0
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

            monsterScale = (random.randint (6,10) * 10) / 100.0 # {.6, .7, .8, .9, 1.0}
            monsterType = random.randint(0,NUMBEROFMONSTERS-1)
            monsterWidth = int(monsterSizes[monsterType][0] * monsterScale)
            monsterHeight = int(monsterSizes[monsterType][1] * monsterScale)
            newMonster = {'rect': pygame.Rect(random.randint(0, WINDOWWIDTH-monsterWidth),0, monsterWidth, monsterHeight),
                          'speed': random.randint(MONSTERMINSPEED, MONSTERMAXSPEED),
                          'surface': pygame.transform.scale(monsterImages[monsterType], (monsterWidth, monsterHeight)),
                          }
            monsters.append(newMonster)
            # print 'New Monster, Type %d: [%d, %d] * %f = [%d, %d]' % (monsterType, monsterSizes[monsterType][0], monsterSizes[monsterType][1], monsterScale, monsterWidth, monsterHeight)
            
        # move yoshi around
        if moveLeft and yoshiRect.left > 0:
            yoshiRect.move_ip(-1 * YOSHIMOVERATE, 0)
            if not facingLeft:
                yoshiImage = pygame.transform.flip(yoshiImage, 1, 0)
                facingLeft = True
        if moveRight and yoshiRect.right < WINDOWWIDTH:
            yoshiRect.move_ip(YOSHIMOVERATE, 0)
            if facingLeft:
                yoshiImage = pygame.transform.flip(yoshiImage, 1, 0)
                facingLeft = False
        if moveUp and yoshiRect.bottom > HORIZON + 30:
            yoshiRect.move_ip(0, -1 * YOSHIMOVERATE)
        if moveDown and yoshiRect.bottom < WINDOWHEIGHT:
            yoshiRect.move_ip(0, YOSHIMOVERATE)

        # move monsters down
        for m in monsters:
            m['rect'].move_ip(0, m['speed'])
            if m['rect'].top > WINDOWHEIGHT:
                monsters.remove(m)
             
        # move the mouse cursor to match the player
        #pygame.mouse.set_pos(yoshiRect.centerx, yoshiRect.centery)

        # draw the game world on the window
        windowSurface.fill(BACKGROUNDCOLOR)
        pygame.draw.rect(windowSurface, FOREGROUNDCOLOR, pygame.Rect(0,HORIZON,WINDOWWIDTH,HORIZON))
        pygame.draw.circle(windowSurface, SUNCOLOR, (600, 100), 60)

        # draw scores
        drawText('Score: %s' % (score), font, windowSurface, 10, 0)
        drawText('Top Score: %s' % (topScore), font_small, windowSurface, 10, 40)

        # draw yoshi
        windowSurface.blit(yoshiImage, yoshiRect)

        # draw each monster
        for m in monsters:
            windowSurface.blit(m['surface'], m['rect'])

        pygame.display.update()
   
        # check if any monster has hit yoshi
        if yoshiHasHitMonster(yoshiRect, monsters):
            if score > topScore:
                topScore = score # new high score!
                f = open('data/hiscore.dat', 'w')
                f.write(str(topScore))
                f.close()
                
            break

        mainClock.tick(FPS)

    # stop the game
    pygame.mixer.music.stop()
    gameOverSound.play()

    drawText('GAME OVER!', font, windowSurface, (WINDOWWIDTH/3), (WINDOWHEIGHT/3))
    pygame.display.update()
    
    pygame.time.delay(3000)
    drawText('Press any key to play again...', font, windowSurface, (WINDOWWIDTH/3)-100, (WINDOWHEIGHT/3)+150)
    pygame.display.update()
    
    waitForKeyPress()

    gameOverSound.stop()




