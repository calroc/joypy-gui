from sys import stderr
from traceback import format_exc
import pygame
from joy.joy import run
from joy.utils.stack import stack_to_string


COMMITTER = 'Simon Forman <forman.simon@gmail.com>'


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


TASK_EVENTS = tuple(range(pygame.USEREVENT, pygame.NUMEVENTS))
AVAILABLE_TASK_EVENTS = set(TASK_EVENTS)


ALLOWED_EVENTS = [pygame.QUIT, pygame.KEYUP, pygame.KEYDOWN]
ALLOWED_EVENTS.extend(MOUSE_EVENTS)
ALLOWED_EVENTS.extend(TASK_EVENTS)

        
# messaging support


class Message(object):

    def __init__(self, sender):
        self.sender = sender


class CommandMessage(Message):

    def __init__(self, sender, command):
        Message.__init__(self, sender)
        self.command = command


class ModifyMessage(Message):

    def __init__(self, sender, subject, **details):
        Message.__init__(self, sender)
        self.subject = subject
        self.details = details


# Joy Interpreter & Context


class World(object):

    def __init__(self, stack_holder, dictionary, notify, content_id):
        self.stack_holder = stack_holder
        self.dictionary = dictionary
        self.notify = notify
        self._id = content_id

    def handle(self, message):
        if not isinstance(message, CommandMessage):
            return
        c, s, d = message.command, self.stack_holder[0], self.dictionary
        self.stack_holder[0], _, self.dictionary = run(c, s, d)
        cm = ModifyMessage(self, self.stack_holder, content_id=self._id)
        self.notify(cm)
        print stack_to_string(self.stack_holder[0])


# main loop


class TheLoop(object):

    FRAME_RATE = 24

    def __init__(self, display, clock):
        self.display = display
        self.clock = clock
        self.tasks = {}
        self.running = False

    def install_task(self, F, milliseconds):
        try:
            task_event_id = AVAILABLE_TASK_EVENTS.pop()
        except KeyError:
            raise RuntimeError('out of task ids')
        self.tasks[task_event_id] = F
        pygame.time.set_timer(task_event_id, milliseconds)
        return task_event_id

    def remove_task(self, task_event_id):
        assert task_event_id in self.tasks, repr(task_event_id)
        pygame.time.set_timer(task_event_id, 0)
        del self.tasks[task_event_id]
        AVAILABLE_TASK_EVENTS.add(task_event_id)

    def __del__(self):
        for task_event_id in self.tasks:
            pygame.time.set_timer(task_event_id, 0)

    def run_task(self, task_event_id):
        task = self.tasks[task_event_id]
        try:
            task()
        except:
            traceback = format_exc()
            self.remove_task(task_event_id)
            # TODO: when we can open a textviewer and load any ol' text, do that instead.
            print >> stderr, traceback
            print >> stderr, 'TASK removed due to ERROR', task

    def loop(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.type in self.tasks:
                    self.run_task(event.type)
                else:
                    self.display.dispatch_event(event)
            pygame.display.update()
            self.clock.tick(self.FRAME_RATE)


##if __name__ == '__main__':
##    pass
