#!/usr/bin/env python
import os, pickle, sys, traceback

import pygame
import viewer
reload(viewer)
import text_viewer
reload(text_viewer)
from core import TheLoop, ALLOWED_EVENTS


from dulwich.errors import NotGitRepository
from dulwich.repo import Repo

from joy.utils.stack import stack_to_string
from joy.library import initialize


JOY_HOME = os.environ.get('JOY_HOME')
if JOY_HOME is None:
    JOY_HOME = os.path.expanduser('~/.joypy')
    if not os.path.isabs(JOY_HOME):
        JOY_HOME = os.path.abspath('./JOY_HOME')

if not os.path.exists(JOY_HOME):
    os.makedirs(JOY_HOME, 0700)
    repo = Repo.init(JOY_HOME)
else:  # path does exist
    try:
        repo = Repo(JOY_HOME)
    except NotGitRepository:
        repo = Repo.init(JOY_HOME)


def repo_relative_path(path):
    return os.path.relpath(
        path,
        os.path.commonprefix((repo.controldir(), path))
        )


STACK_FN = os.path.join(JOY_HOME, 'stack.pickle')
JOY_FN = os.path.join(JOY_HOME, 'scratch.txt')
LOG_FN = os.path.join(JOY_HOME, 'log.txt')


#relative_STACK_FN = repo_relative_path(STACK_FN)


def load_stack():
    if os.path.exists(STACK_FN):
        with open(STACK_FN) as f:
          return pickle.load(f)
    return ()


def save_stack():
    with open(STACK_FN, 'wb') as f:
        os.chmod(STACK_FN, 0600)
        pickle.dump(self.stack, f)
        f.flush()
        os.fsync(f.fileno())
    repo.stage([self.relative_STACK_FN])
    commit_id = repo.do_commit(
        'message',
        committer='Simon Forman <forman.simon@gmail.com>',
        )
    #print >> sys.stderr, commit_id


def init_text(viewer, title, filename):
    if os.path.exists(filename):
        with open(filename) as f:
            viewer.lines[:] = f.read().splitlines()
        viewer.draw()
#    repo_relative_filename = repo_relative_path(filename)


##D = initialize()
##for func in ():
##  D[func.__name__] = func


##stack = load_stack()

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
    A = screen, clock
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

 
def main():
    screen, clock = init()
    d = viewer.Display(screen, 89, 144)
    loop = TheLoop(d, clock)
    log = d.open_viewer(0, 0, text_viewer.TextViewer)
    init_text(log, 'Log', LOG_FN)
    t = d.open_viewer(d.w / 2, 0, text_viewer.TextViewer)
    init_text(t, 'Joy - ' + JOY_HOME, JOY_FN)
    error_guard(loop.loop)


if __name__ == '__main__':
  main()
