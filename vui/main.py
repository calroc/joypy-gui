#!/usr/bin/env python
import os, pickle, sys, traceback

import pygame
import display
reload(display)
import text_viewer
reload(text_viewer)
from core import TheLoop, World, ALLOWED_EVENTS
from persist_task import PersistTask

from joy.library import initialize


JOY_HOME = os.environ.get('JOY_HOME')
if JOY_HOME is None:
    JOY_HOME = os.path.expanduser('~/.joypy')
    if not os.path.isabs(JOY_HOME):
        raise ValueError('what directory?')


def init_text(display, pt, x, y, title, filename):
    # TODO eventually title should go in the menu?
    viewer = display.open_viewer(x, y, text_viewer.TextViewer)
    viewer.content_id, viewer.lines = pt.open(filename)
    viewer.draw()
    return viewer


D = initialize()
##for func in ():
##  D[func.__name__] = func

##stack = load_stack()

try:
    A = A
except NameError:
    A = None

def init():
    global A
    if A:
        return A
    print 'Initializing Pygame...'
    pygame.init()
    print 'Creating window...'
    screen = pygame.display.set_mode((1024, 768))
    clock = pygame.time.Clock()
    pygame.event.set_allowed(None)
    pygame.event.set_allowed(ALLOWED_EVENTS)
    pt = PersistTask(JOY_HOME)
    A = screen, clock, pt
    return A


def error_guard(loop, n=10):
    error_count = 0
    while error_count < n:
        try:
            loop()
            break
        except:
            traceback.print_exc()
            error_count += 1

d = None
def main():
    global d
    screen, clock, pt = init()
    d = display.Display(screen, D.__contains__, 89, 144)
    loop = TheLoop(d, clock)
    content_id, stack_holder = pt.open('stack.pickle')
    world = World(stack_holder, D, d.broadcast, content_id)
    loop.install_task(pt.task_run, 2000)  # save files every two seconds
    d.handlers.append(pt.handle)
    d.handlers.append(world.handle)
    log = init_text(d, pt, 0, 0, 'Log', 'log.txt')
    t = init_text(d, pt, d.w / 2, 0, 'Joy', 'scratch.txt')
    error_guard(loop.loop)


if __name__ == '__main__':
  main()
