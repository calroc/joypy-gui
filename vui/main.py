#!/usr/bin/env python
import os, pickle, sys, traceback

# To enable "hot" reloading in the IDLE shell.
for name in 'core display viewer text_viewer stack_viewer persist_task'.split():
    try:
        del sys.modules[name]
    except KeyError:
        pass

import pygame
from joy.library import initialize, SimpleFunctionWrapper
from joy.utils.stack import list_to_stack
import core, display, text_viewer, persist_task


FULLSCREEN = '-f' in sys.argv


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


try:
    D = D
except NameError:
    D = initialize()

    @SimpleFunctionWrapper
    def splitlines(stack):
        text, stack = stack
        assert isinstance(text, str), repr(text)
        return list_to_stack(text.splitlines()), stack
    D['splitlines'] = splitlines

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
    if FULLSCREEN:
        screen = pygame.display.set_mode()
    else:
        screen = pygame.display.set_mode((1024, 768))
    clock = pygame.time.Clock()
    pygame.event.set_allowed(None)
    pygame.event.set_allowed(core.ALLOWED_EVENTS)
    pt = persist_task.PersistTask(JOY_HOME)
    pt.register_commands(D)
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


def init_context(screen, clock, pt):
    tracks = (144 - 89, 144, 89) if FULLSCREEN else (89, 144)
    d = display.Display(screen, D.__contains__, *tracks)
    d.register_commands(D)
    log = init_text(d, pt, 0, 0, 'Log', 'log.txt')
    t = init_text(d, pt, d.w / 2, 0, 'Joy', 'scratch.txt')
    loop = core.TheLoop(d, clock)
    stack_id, stack_holder = pt.open('stack.pickle')
    world = core.World(stack_id, stack_holder, D, d.broadcast, log)
    return locals()


d = None # To have a reference to it in the IDLE shell window.
def main():
    global d
    screen, clock, pt = init()
    name_space = init_context(screen, clock, pt)
    name_space['D'] = D
    loop = name_space['loop']
    d = name_space['d']
    world = name_space['world']
    loop.install_task(pt.task_run, 10000)  # save files every ten seconds
    d.handlers.append(pt.handle)
    d.handlers.append(world.handle)

    @SimpleFunctionWrapper
    def evaluate(stack):
        code, stack = stack
        assert isinstance(code, str), repr(code)
        exec code in name_space.copy()
        return stack
    D['evaluate'] = evaluate
        
    error_guard(loop.loop)


if __name__ == '__main__':
    main()
