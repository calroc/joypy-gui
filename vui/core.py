import pygame


BLACK = FOREGROUND = 0, 0, 0
GREY = 127, 127, 127
WHITE = BACKGROUND = 255, 255, 255
BLUE = 100, 100, 255
GREEN = 70, 200, 70


MOUSE_EVENTS = frozenset({
    pygame.MOUSEMOTION,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP
    })


ARROW_KEYS = frozenset({
    pygame.K_UP,
    pygame.K_DOWN,
    pygame.K_LEFT,
    pygame.K_RIGHT
    })


# Eight "trays" or "modes" made by the three main mode keys.
NORM = ()
CTRL = (pygame.KMOD_CTRL,)
ALT = (pygame.KMOD_ALT,)
SHIFT = (pygame.KMOD_SHIFT,)
CTRL_ALT = (pygame.KMOD_CTRL, pygame.KMOD_ALT)
ALT_SHIFT = (pygame.KMOD_ALT, pygame.KMOD_SHIFT)
CTRL_SHIFT = (pygame.KMOD_CTRL, pygame.KMOD_SHIFT)
CTRL_ALT_SHIFT = (pygame.KMOD_CTRL, pygame.KMOD_ALT, pygame.KMOD_SHIFT,)


def mods_of(mod):
    return tuple(flag for flag in CTRL_ALT_SHIFT if flag & mod)


# messaging support

class Message(object):

    def __init__(self, sender):
        self.sender = sender


class ModifyMessage(Message):

    def __init__(self, sender, subject, *details):
        Message.__init__(self, sender)
        self.subject = subject
        self.details = details


##if __name__ == '__main__':
##    pass
