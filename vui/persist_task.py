import os
from collections import Counter
import core


class Resource(object):

    def __init__(self, filename):
        self.filename = filename
        self.lines = open(filename).read().splitlines()

    def persist(self):
        print 'persisting', self.filename
        with open(self.filename, 'w') as f:
            for line in self.lines:
                print >> f, line


class PersistTask(object):

    LIMIT = 10
    MAX_SAVE = 10

    def __init__(self, home):
        self.home = home
        self.counter = Counter()
        self.store = {}

    def open(self, name):
        # look up the file in home and get its data
        fn = os.path.join(self.home, name)
        content_id = name # hash(fn)
        try:
            resource = self.store[content_id]
        except KeyError:
            resource = self.store[content_id] = Resource(fn)
        return content_id, resource.lines

    def handle(self, message):
        if not isinstance(message, core.ModifyMessage):
            return
        try:
            content_id = message.details['content_id']
        except KeyError:
            return
        if not content_id:
            return
        self.counter[content_id] += 1
        if self.counter[content_id] > self.LIMIT:
            self.persist(content_id)

    def persist(self, content_id):
        del self.counter[content_id]
        self.store[content_id].persist()

    def task_run(self):
        for content_id, _ in self.counter.most_common(self.MAX_SAVE):
            self.persist(content_id)


if __name__ == '__main__':
    JOY_HOME = os.path.expanduser('~/.joypy')
    pt = PersistTask(JOY_HOME)
    content_id, lines = pt.open('scratch.txt')

    pt.persist(content_id)


    print pt.counter
    mm = core.ModifyMessage(None, None, content_id=content_id)
    pt.handle(mm)
    print pt.counter
