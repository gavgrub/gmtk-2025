import pygame, sys, math

width = 1000
height = 600
fps = 60

delta_t = 0.1
NUM_ITER = 10

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

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
        print(distance)
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
        
    def update(self, delta_t):
        if self.fixed:
            return

        # Collision process
        # Window
        if self.x < -width / 2 or self.x > width / 2:
            self.x, self.oldx = self.oldx, self.x
        if self.y < -height / 2 or self.y > height / 2:
            self.y, self.oldy = self.oldy, self.y

        # Objects
        intersecting = False
        for object in Objects.objects:
            if object.intersecting(self.x, self.y):
                intersecting = True
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
        pygame.draw.circle(surf, WHITE, (int(self.x) + width / 2, int(self.y) + height / 2), size)

        
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

    def __init__(self, x, y, length = 20):

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

        #Lock the last part of the worm body
        self.body[-1].fixed = True

    def update(self):
        # body parts update
        for i in range(len(self.body)):
            self.body[i].update(delta_t)
        # constraints update
        for n in range(NUM_ITER):
            for i in range(len(self.constraints)):
                self.constraints[i].update()

    def draw(self):
        # particles draw
        for i in range(len(self.body)):
            self.body[i].draw(screen, 3)
        # constraints draw
        for i in range(len(self.constraints)):
            self.constraints[i].draw(screen, 1)

    # This function moves the worm
    def move(self, x, y):
        head = self.body[0]
        if head.fixed:
            return

        dx = x - head.x
        dy = y - head.y
        dist = math.hypot(dx, dy)

        max_force = 10  # Maximum movement per update
        if dist > 0:
            dx = dx / dist * min(dist, max_force)
            dy = dy / dist * min(dist, max_force)

        strength = 2
        head.oldx = head.x - dx * strength
        head.oldy = head.y - dy * strength

class Controller:
    @staticmethod
    def input():
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

worm = Worm(0, 0)

Objects.add(Circle(20, 20, 30, BLUE))

#Game Loop
while True:
    clock.tick(fps)
    Controller.input()
    Controller.update()
    Renderer.draw(screen)