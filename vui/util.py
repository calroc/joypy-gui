from collections import namedtuple
import pygame


BLACK = 0, 0, 0
GREY = 127, 127, 127
WHITE = 255, 255, 255
BLUE = 100, 100, 255
GREEN = 70, 200, 70


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


if __name__ == '__main__':
    pass
