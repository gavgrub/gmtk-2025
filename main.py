# GMTK Game Jam Submission 2025
# Created by Gavin Grubert
# Sorry to whichever poor soul decides it's a good idea to look over this code

import pygame, sys, math, os, random
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #Hides stupid welcome message

from util.text import *
from util.helper import *

width = 1024
height = 576
fps = 60

delta_t = 0.1
NUM_ITER = 10

win = False #flips to true when the game is won

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

WORM_1 = (84, 109, 166)
WORM_2 = (69, 88, 146)

CENTER = (48, 180, 201)
EDGE = (42, 52, 76) 

#Set up assets
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

sndDir = os.path.join(app_path, 'snd')
imgDir = os.path.join(app_path, 'img')

class Level:
    current = 0
    spawn = (0, 0)
    length = 0
    levels = []

    # Game Levels
    @staticmethod
    def intro():
        global worm

        Objects.clear()
        Level.spawnWorm(-400, 0, 50)

        for i in range(3):
            Objects.add(Circle(i * 150 - 150, 0, 40, CENTER, EDGE))

        Objects.add(Win(300, 0))

    @staticmethod
    def spawnWorm(x, y, length):
        global worm
        Level.spawn = (x, y)
        Level.length = length
        worm = Worm(x, y, 50)

    @staticmethod
    def respawnWorm():
        global worm
        worm = Worm(Level.spawn[0], Level.spawn[1], 50)

    @staticmethod
    def next():
        Level.levels[Level.current]()
        Level.current += 1
        if (Level.current >= len(Level.levels)):
            Level.current = 0

Level.levels = [Level.intro]

# Manages all of the objects in the map
class Objects:
    objects = []
    
    @staticmethod
    def add(object):
        Objects.objects.append(object)

    @staticmethod
    def update():
        for object in Objects.objects:
            object.update()

    @staticmethod
    def draw(screen):
        for object in Objects.objects:
            object.draw(screen)

    @staticmethod
    def clear():
        Objects.objects = []

class Object:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
    def update(self):
        pass
    def draw(self, screen):
        screen.blit(self.image, (self.x - self.image.get_width() / 2 + width / 2, self.y - self.image.get_height() / 2 + height / 2))
    # Determines if a point is intersecting with that object
    def intersecting(self, x, y):
        return (self.x - self.image.get_width() / 2 < x < self.x + self.image.get_width() / 2) and (self.y - self.image.get_height() / 2 < y < self.y + self.image.get_height() / 2)

class Circle(Object):
    def __init__(self, x, y, diameter, color, border, borderWidth = 5):
        self.diameter = diameter
        self.radius = diameter / 2

        image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(image, color, (self.radius, self.radius), self.radius)
        pygame.draw.circle(image, border, (self.radius, self.radius), self.radius, borderWidth)

        super().__init__(x, y, image)

    # Determines if a point is intersecting with the circle (special due to the circular hitbox)
    def intersecting(self, x, y):
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return distance < self.radius
    
class Win(Circle):
    def __init__(self, x, y):
        super().__init__(x, y, 40, WHITE, WHITE)
        self.image = win_img

    def intersecting(self, x, y):
        global win
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        if distance < self.radius:
            win = True
        return distance < self.radius

# Worm body segments
class Particle:
    def __init__(self, x, y, color = WHITE, m = 1.0, f = 0.99):
        self.f = f
        self.m = m
        self.x = x
        self.y = y
        self.oldx = x
        self.oldy = y
        self.newx = x
        self.newy = y
        self.ax = 0
        self.ay = 0
        self.color = color
        
        self.fixed = False
        self.intersection = False
        self.intersectingWith = None
        
    def update(self, delta_t, canIntersect = True):
        self.intersection = False
        self.intersectingWith = None

        if self.fixed:
            return

        # Collision process
        # Window
        if self.x < -width / 2 or self.x > width / 2:
            self.x, self.oldx = self.oldx, self.x
        if self.y < -height / 2 or self.y > height / 2:
            self.y, self.oldy = self.oldy, self.y

        # Objects
        if canIntersect:
            for object in Objects.objects:
                if object.intersecting(self.x, self.y):
                    self.x, self.oldx = self.oldx, self.x
                    self.y, self.oldy = self.oldy, self.y
                    self.intersectingWith = object
                    self.intersection = True
                    break

        friction = 0.99
        velocity_x = (self.x - self.oldx) * friction
        velocity_y = (self.y - self.oldy) * friction

        # Verlet integration with friction
        self.newx = self.x + velocity_x + self.ax * delta_t * delta_t
        self.newy = self.y + velocity_y + self.ay * delta_t * delta_t
        self.oldx = self.x
        self.oldy = self.y
        self.x = self.newx
        self.y = self.newy
        
    def draw(self, surf, size):
        pygame.draw.circle(surf, self.color, (int(self.x) + width / 2, int(self.y) + height / 2), size)
        
class Constraint:
    def __init__(self, index0, index1, listPointer):
        self.index0 = index0
        self.index1 = index1
        delta_x = listPointer[index0].x - listPointer[index1].x
        delta_y = listPointer[index0].y - listPointer[index1].y
        self.restLength = math.sqrt(delta_x * delta_x + delta_y * delta_y)

        self.listPointer = listPointer
        
    def update(self):
        
        delta_x = self.listPointer[self.index1].x - self.listPointer[self.index0].x
        delta_y = self.listPointer[self.index1].y - self.listPointer[self.index0].y
        deltaLength = math.sqrt(delta_x * delta_x + delta_y * delta_y)
        diff = (deltaLength - self.restLength)/deltaLength
        
        if self.listPointer[self.index0].fixed == False:
            self.listPointer[self.index0].x += 0.5 * diff * delta_x
            self.listPointer[self.index0].y += 0.5 * diff * delta_y
        if self.listPointer[self.index1].fixed == False:
            self.listPointer[self.index1].x -= 0.5 * diff * delta_x
            self.listPointer[self.index1].y -= 0.5 * diff * delta_y
            
    def draw(self, surf, size):
        x0 = self.listPointer[self.index0].x
        y0 = self.listPointer[self.index0].y
        x1 = self.listPointer[self.index1].x
        y1 = self.listPointer[self.index1].y
        pygame.draw.line(surf, WHITE, (int(x0) + width / 2, int(y0) + height / 2), (int(x1) + width / 2, int(y1) + height / 2), size)

# This class handles the main character in the game
class Worm:
    segmentSep = 5
    bodySize = 10

    def __init__(self, x, y, length = 50):

        primaryColor = WORM_1
        secondaryColor = WORM_2

        # Create the worm body
        self.body = []
        for i in range(length):
            primaryColor, secondaryColor = secondaryColor, primaryColor
            p = Particle(x + Worm.segmentSep, y, primaryColor)
            Worm.segmentSep *= -1
            self.body.append(p)

        self.constraints = []
        for i in range(length - 1):
            index0 = i
            index1 = i + 1
            c = Constraint(index0, index1, self.body)
            self.constraints.append(c)

        # Determine the start and the end of the worm
        self.head = self.body[0]
        self.tail = self.body[-1]

        # Lock the last part of the worm body
        self.tail.fixed = True

        self.noStick = set()

    def update(self):
        # body parts update
        for i in range(len(self.body)):
            self.body[i].update(delta_t, self.body[i] != self.head)
        # constraints update
        for n in range(NUM_ITER):
            for i in range(len(self.constraints)):
                self.constraints[i].update()

        # Remove things list of things you can't stick to if you're no longer touching them
        canRemove = self.noStick.copy()
        for i in self.body:
            if i.intersectingWith in canRemove:
                canRemove.remove(i.intersectingWith)
        for i in canRemove:
            if i in self.noStick:
                self.noStick.remove(i)

        # Determining if the head and any individual part of the worm are touching each other
        # If so, whether to consider that a new loop has been created
        for a in self.body:
            for b in self.body:

                distance = math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
                indexDistance = abs(self.body.index(a) - self.body.index(b))
                if (distance < Worm.bodySize) and (indexDistance > 5):

                    startIndex = min(self.body.index(a), self.body.index(b))

                    total = 0
                    for i in range(startIndex, indexDistance + startIndex):
                        if self.body[i].intersection and not (self.body[i].intersectingWith in self.noStick):
                            total += 1
                    average = total / indexDistance

                    if (average > 0.4):
                        for i in self.body:
                            i.fixed = False

                        a.fixed = True
                        b.fixed = True

                        self.head, self.tail = self.tail, self.head

                        for i in self.body:
                            if not i.intersectingWith == None:
                                self.noStick.add(i.intersectingWith)

                        # Play squeak noise
                        globals()[f"squeak_{random.randrange(1, 6)}"].play()

                        break

    def draw(self):
        xMouse, yMouse = pygame.mouse.get_pos()

        # Draw the body of the worm
        for i in range(len(self.body)):
            self.body[i].draw(screen, Worm.bodySize)
        
        # Draw the eyes and pupils
        angle = math.atan2(self.head.oldy - self.head.newy, self.head.oldx - self.head.newx)
        radius = Worm.bodySize * 0.75

        xEye1 = self.head.x + math.cos(angle + math.pi / 4) * Worm.bodySize * 0.75 + width / 2
        yEye1 = self.head.y + math.sin(angle + math.pi / 4) * Worm.bodySize * 0.75 + height / 2
        eyeAngle1 = math.atan2(yMouse - yEye1, xMouse - xEye1)
        pygame.draw.circle(screen, WHITE, (xEye1, yEye1), radius)

        xEye2 = self.head.x + math.cos(angle - math.pi / 4) * Worm.bodySize * 0.75 + width / 2
        yEye2 = self.head.y + math.sin(angle - math.pi / 4) * Worm.bodySize * 0.75 + height / 2
        eyeAngle2 = math.atan2(yMouse - yEye2, xMouse - xEye2)
        pygame.draw.circle(screen, WHITE, (xEye2, yEye2), radius)

        # Draw the pupils
        pygame.draw.circle(screen, BLACK, (xEye1 + math.cos(eyeAngle1) * radius * 0.5, yEye1 + math.sin(eyeAngle1) * radius * 0.5), radius * 0.75)
        pygame.draw.circle(screen, BLACK, (xEye2 + math.cos(eyeAngle2) * radius * 0.5, yEye2 + math.sin(eyeAngle2) * radius * 0.5), radius * 0.75)

    # This function moves the worm
    def move(self, x, y):
        if self.head.fixed:
            return

        dx = x - self.head.x
        dy = y - self.head.y

        dist = math.hypot(dx, dy)

        max_force = 5  # Maximum movement per update
        if dist > 0:
            dx = dx / dist * min(dist, max_force)
            dy = dy / dist * min(dist, max_force)

        strength = 1.5
        self.head.oldx = self.head.x - dx * strength
        self.head.oldy = self.head.y - dy * strength

# Start menu of the game
def startMenu():
    playButton = button_img.copy()
    drawText(playButton, "Play", 24, playButton.get_width() / 2, playButton.get_height() / 2, pos="center")

    timeHeld = [0 for i in range(1)]

    running = True
    while running:
        xMouse, yMouse = pygame.mouse.get_pos()
        pressed1, pressed2, pressed3 = pygame.mouse.get_pressed()
        clock.tick(fps)

        #Process input (events)
        for event in pygame.event.get():
            #Check for closeing window
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(menu, (0, 0))

        # Buttons
        #Play button
        x, y = (width / 2, height * 3 / 5)
        if not (timeHeld[0] > 10) and (x - playButton.get_width() / 2 < xMouse < x + playButton.get_width() / 2) and (y - playButton.get_height() / 2 < yMouse < y + playButton.get_height() / 2):
            timeHeld[0] += 1
            if pressed1:
                running = False
                button_clicked.play()
        elif not (timeHeld[0] <= 0):
            timeHeld[0] -= 1
        
        factor = smoothstep(0, 0.1, timeHeld[0] / 10) + 1
        if (timeHeld[0] < 10):
            playButtonScaled = pygame.transform.scale(playButton, (playButton.get_width() * factor, playButton.get_height() * factor))
        screen.blit(playButtonScaled, (x - playButtonScaled.get_width() / 2, y - playButtonScaled.get_height() / 2))

        pygame.display.flip()

class Controller:
    @staticmethod
    def input():
        global worm

        pressed1, pressed2, pressed3 = pygame.mouse.get_pressed()
        xMouse, yMouse = pygame.mouse.get_pos()

        # Moving the worm
        if pressed1:
            worm.move(xMouse - width / 2, yMouse - height / 2)

        #Process input (events)
        for event in pygame.event.get():
            #Check for closeing window
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    Level.respawnWorm()
                    respawn.play()

    @staticmethod
    def update():
        global win

        Objects.update()
        worm.update()

        #Win condition
        if win:
            win = False
            oldScreen = screen.copy()
            Level.next()
            Renderer.draw(screen)
            newScreen = screen.copy()
            clapping.play()
            transitionScreen(screen, oldScreen, newScreen)
        
def transitionScreen(screen, oldSurface, newSurface, fadeSpeed=8):
    clock = pygame.time.Clock()
    screenWidth, screenHeight = screen.get_size()

    # Fade to black
    for alpha in range(0, 256, fadeSpeed):
        darkOverlay = pygame.Surface((screenWidth, screenHeight))
        darkOverlay.fill((0, 0, 0))
        darkOverlay.set_alpha(alpha)
        screen.blit(oldSurface, (0, 0))
        screen.blit(darkOverlay, (0, 0))
        pygame.display.flip()
        clock.tick(fps)

    # Fade to new surface
    for alpha in range(0, 256, fadeSpeed):
        fadeOverlay = pygame.Surface((screenWidth, screenHeight))
        fadeOverlay.fill((0, 0, 0))
        fadeOverlay.set_alpha(255 - alpha)
        screen.blit(newSurface, (0, 0))
        screen.blit(fadeOverlay, (0, 0))
        pygame.display.flip()
        clock.tick(fps)

class Renderer:
    @staticmethod
    def draw(screen):
        screen.blit(background_1, (0, 0))
        Objects.draw(screen)
        worm.draw()
        pygame.display.flip()

#This Method Loads All The Files In The flags Folder
def loadImages(file, colorkey = None):
    global cityImage, regionImage
    #Get A List Of All Files In img
    array = os.listdir(file)

    #Iterate Through Every Image In The List array
    for i in range(len(os.listdir(file))):
        name = array[i].replace(".png", "")

        #Add Colorkey To Each Image And Set Their Rect To The Correct Size
        globals()[name] = pygame.image.load(os.path.join(file, array[i])).convert_alpha()
        if not (colorkey == None):
            globals()[name].set_colorkey(colorkey)

#This Method Loads All The Files In The snd Folder
def loadSounds(file, volume = 1):
    #Get A List Of All Files In snd
    array = os.listdir(file)

    #Iterate Through Every Image In The List array
    for i in range(len(os.listdir(file))):
        if ".wav" in array[i]:
            #Load Sound File
            globals()[array[i].replace(".wav", "")] = pygame.mixer.Sound(os.path.join(file, array[i]))
            globals()[array[i].replace(".wav", "")].set_volume(volume)

    clapping.set_volume(2)
    respawn.set_volume(8)
    
#Create Window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Loopbugs")
pygame.display.set_icon(pygame.image.load("img/icon.png"))
clock = pygame.time.Clock()

# Load assests
loadImages(imgDir, BLACK)
loadSounds(sndDir)

startMenu()

# Music
pygame.mixer.music.load("snd/Little Samba - Quincas Moreira.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

Level.next()

#Game Loop
while True:
    clock.tick(fps)
    Controller.input()
    Controller.update()
    Renderer.draw(screen)