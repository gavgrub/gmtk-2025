import pygame, sys, math

width = 1000
height = 600
fps = 60

delta_t = 0.1
NUM_ITER = 10

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

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
    def __init__(self, x, y, diameter, color):
        self.diameter = diameter
        self.radius = diameter / 2

        image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(image, color, (self.radius, self.radius), self.radius)

        super().__init__(x, y, image)

    # Determines if a point is intersecting with the circle (special due to the circular hitbox)
    def intersecting(self, x, y):
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return distance < self.radius

# Worm body segments
class Particle:
    def __init__(self, x, y, m = 1.0, f = 0.99):
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
        global worm

        if (self == worm.head):
            color = GREY
        elif (self.intersection == True):
            color = BLUE
        else:
            color = WHITE

        pygame.draw.circle(surf, color, (int(self.x) + width / 2, int(self.y) + height / 2), size)
        
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
    segmentSep = 10
    bodySize = 10

    def __init__(self, x, y, length = 40):

        # Create the worm body
        self.body = []
        for i in range(length):
            p = Particle(x + i * Worm.segmentSep, y)
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

        # Remove things from no stick
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
                if (distance < Worm.bodySize) and (indexDistance > 4):

                    startIndex = min(self.body.index(a), self.body.index(b))

                    total = 0
                    object = None
                    for i in range(startIndex, indexDistance + startIndex):
                        if self.body[i].intersection and not (self.body[i].intersectingWith in self.noStick):
                            total += 1
                            object = self.body[i].intersectingWith
                    average = total / indexDistance

                    if (average > 0.5):
                        for i in self.body:
                            i.fixed = False

                        a.fixed = True
                        b.fixed = True

                        self.head, self.tail = self.tail, self.head

                        for i in self.body:
                            if not i.intersectingWith == None:
                                self.noStick.add(i.intersectingWith)
                        break

    def draw(self):
        # particles draw
        for i in range(len(self.body)):
            self.body[i].draw(screen, Worm.bodySize)
        # constraints draw
        #for i in range(len(self.constraints)):
        #    self.constraints[i].draw(screen, 1)

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

        strength = 2
        self.head.oldx = self.head.x - dx * strength
        self.head.oldy = self.head.y - dy * strength

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
                    worm = Worm(50, 50)

    @staticmethod
    def update():
        Objects.update()
        worm.update()

class Renderer:
    @staticmethod
    def draw(screen):
        screen.fill(BLACK)
        worm.draw()
        Objects.draw(screen)
        pygame.display.flip()
    
#Create Window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Main")
clock = pygame.time.Clock()

worm = Worm(50, 50)

for i in range(0, 6):
    Objects.add(Circle(math.cos(math.pi / 3 * i) * 200, math.sin(math.pi / 3 * i) * 200, 30, GREEN))

#Game Loop
while True:
    clock.tick(fps)
    Controller.input()
    Controller.update()
    Renderer.draw(screen)