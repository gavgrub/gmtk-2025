import pygame

# Colors
WHITE = (255, 255, 255)

# Function to draw text onto a surface
@staticmethod
def drawText(surf, text, size, x, y, color=WHITE, pos="midtop", font="arial"):
    fontSurface = pygame.font.match_font(font, size)
    textSurface = fontSurface.render(text, True, color)
    textRect = textSurface.get_rect()

    # Position of the text on the item
    if pos in {"top", "left", "right", "bottom", "topleft", "bottomleft", "topright", "bottomright", "midtop", "midleft", "midbottom", "midright", "center", "centerx", "centery"}:
        setattr(textRect, pos, (x, y))
    else:
        raise Exception("Invalid position for text rect!")

    surf.blit(textSurface, textRect)