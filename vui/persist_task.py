import os, pickle
from collections import Counter
from dulwich.errors import NotGitRepository
from dulwich.repo import Repo
import core


def open_repo(repo_dir=None, initialize=False):
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir, 0700)
        return Repo.init(repo_dir)
    try:
        return Repo(repo_dir)
    except NotGitRepository:
        if initialize:
            return Repo.init(repo_dir)
        raise


def foo(repo):
    c = repo.controldir()
    def repo_relative_path(path):
        return os.path.relpath(path, os.path.commonprefix((c, path)))
    return repo_relative_path


class Resource(object):

    def __init__(self, filename, repo_relative_filename):
        self.filename = filename
        self.repo_relative_filename = repo_relative_filename
        self.thing = self._from_file(open(filename))

    def _from_file(self, f):
        return f.read().splitlines()

    def _to_file(self, f):
        for line in self.thing:
            print >> f, line

    def persist(self, repo):
        print 'persisting', self.filename
        with open(self.filename, 'w') as f:
            os.chmod(self.filename, 0600)
            self._to_file(f)
            f.flush()
            os.fsync(f.fileno())
            # For goodness's sake, write it to the disk already!
        repo.stage([self.repo_relative_filename])


class PickledResource(Resource):

    def _from_file(self, f):
        return [pickle.load(f)]

    def _to_file(self, f):
        pickle.dump(self.thing[0], f)


class PersistTask(object):

    LIMIT = 10
    MAX_SAVE = 10

    def __init__(self, home):
        self.home = home
        self.repo = open_repo(home)
        self._r = foo(self.repo)
        self.counter = Counter()
        self.store = {}

    def open(self, name):
        # look up the file in home and get its data
        fn = os.path.join(self.home, name)
        content_id = name # hash(fn)
        try:
            resource = self.store[content_id]
        except KeyError:
            R = PickledResource if name.endswith('.pickle') else Resource
            resource = self.store[content_id] = R(fn, self._r(fn))
        return content_id, resource.thing

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
            self.commit('due to activity')

    def persist(self, content_id):
        del self.counter[content_id]
        self.store[content_id].persist(self.repo)

    def task_run(self):
        if not self.counter:
            return
        for content_id, _ in self.counter.most_common(self.MAX_SAVE):
            self.persist(content_id)
        self.commit()

    def commit(self, message='auto-commit'):
        print 'commit', message
        return self.repo.do_commit(message, committer=core.COMMITTER)

if __name__ == '__main__':
    JOY_HOME = os.path.expanduser('~/.joypy')
    pt = PersistTask(JOY_HOME)
    content_id, thing = pt.open('stack.pickle')
    pt.persist(content_id)
    print pt.counter
    mm = core.ModifyMessage(None, None, content_id=content_id)
    pt.handle(mm)
    print pt.counter
