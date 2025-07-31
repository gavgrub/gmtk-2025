import pygame
from colorsys import hsv_to_rgb

def getColorMap():
    width, height = 360, 100
    surface = pygame.Surface((width, height))
    for x in range(width):
        hue = x / width
        for y in range(height):
            sat = 1 - (y / height)
            value = 1.0
            r, g, b = hsv_to_rgb(hue, sat, value)
            color = (int(r * 255), int(g * 255), int(b * 255))
            surface.set_at((x, y), color)
    return surface