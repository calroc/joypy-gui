#!/usr/bin/env python
import os, pickle, sys, traceback
import pygame
from joy.library import initialize, DefinitionWrapper, SimpleFunctionWrapper
import core, display, text_viewer, persist_task


FULLSCREEN = '-f' in sys.argv


JOY_HOME = os.environ.get('JOY_HOME')
if JOY_HOME is None:
    JOY_HOME = os.path.expanduser('~/.joypy')
    if not os.path.isabs(JOY_HOME):
        raise ValueError('what directory?')


def init_text(display, pt, x, y, filename):
    viewer = display.open_viewer(x, y, text_viewer.TextViewer)
    viewer.content_id, viewer.lines = pt.open(filename)
    viewer.draw()
    return viewer


def load_definitions(pt, dictionary):
    lines = pt.open('definitions.txt')[1]
    for line in lines:
        if '==' in line:
            DefinitionWrapper.add_def(line, dictionary)


def load_primitives(home, name_space):
    fn = os.path.join(home, 'library.py')
    if os.path.exists(fn):
        execfile(fn, name_space)


def init():
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
    return screen, clock, pt


def init_context(screen, clock, pt):
    D = initialize()
    d = display.Display(
        screen,
        D.__contains__,
        *((144 - 89, 144, 89) if FULLSCREEN else (89, 144))
        )
    d.register_commands(D)
    pt.register_commands(D)
    log = init_text(d, pt, 0, 0, 'log.txt')
    t = init_text(d, pt, d.w / 2, 0, 'scratch.txt')
    loop = core.TheLoop(d, clock)
    stack_id, stack_holder = pt.open('stack.pickle')
    world = core.World(stack_id, stack_holder, D, d.broadcast, log)
    loop.install_task(pt.task_run, 10000)  # save files every ten seconds
    d.handlers.append(pt.handle)
    d.handlers.append(world.handle)
    load_definitions(pt, D)
    return locals()


def error_guard(loop, n=10):
    error_count = 0
    while error_count < n:
        try:
            loop()
            break
        except:
            traceback.print_exc()
            error_count += 1


def main(screen, clock, pt):
    name_space = init_context(screen, clock, pt)
    load_primitives(pt.home, name_space.copy())

    @SimpleFunctionWrapper
    def evaluate(stack):
        code, stack = stack
        exec code in name_space.copy()
        return stack

    name_space['D']['evaluate'] = evaluate

    error_guard(name_space['loop'].loop)

    return name_space['d']


if __name__ == '__main__':
    main(*init())
