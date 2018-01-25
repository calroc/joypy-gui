#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''\
Joypy - Copyright © 2018 Simon Forman
This program comes with ABSOLUTELY NO WARRANTY; for details right-click "warranty".
This is free software, and you are welcome to redistribute it under certain conditions; right-click "sharing" for details.
Right-click "words" or press F12 to see a list of all words,
Right-Left-click on a command word to print the docs for it.

Mouse button chords (to cancel a chord, click the third mouse button.)

Left - Point, sweep selection
Left-Middle - Cut the selection, place text on stack
Left-Right - Run the selection as Joy code

Middle - Paste selection (bypass stack), scroll
Middle-Left - Paste from top of stack, preserve
Middle-Right - Paste from top of stack, pop

Right - Execute command word under mouse cursor
Right-Left - Print docs of command word under mouse cursor
Right-Middle - Lookup word (kinda useless now)
'''
import os, pickle, sys, traceback
from joy.utils.stack import stack_to_string
from joy.library import initialize
from gui.misc import FileFaker
from gui.textwidget import TextViewerWidget, tk, get_font
from gui.world import World


JOY_HOME = os.environ.get('JOY_HOME')
if JOY_HOME is None:
  JOY_HOME = os.path.expanduser('~/.joypy')
  if not os.path.isabs(JOY_HOME):
    JOY_HOME = os.path.abspath('./JOY_HOME')
  print 'JOY_HOME=' + JOY_HOME
  if not os.path.exists(JOY_HOME):
    print 'creating...'
    os.makedirs(JOY_HOME, 0700)
STACK_FN = os.path.join(JOY_HOME, 'stack.pickle')
JOY_FN = os.path.join(JOY_HOME, 'scratch.txt')
LOG_FN = os.path.join(JOY_HOME, 'log.txt')


class StackDisplayWorld(World):

  def print_stack(self):
    print '\n%s <-' % stack_to_string(self.stack)

  def save(self):
    with open(STACK_FN, 'wb') as f:
      os.chmod(STACK_FN, 0600)
      pickle.dump(self.stack, f)
      f.flush()
      os.fsync(f.fileno())


def init_text(t, title, filename):
  t.winfo_toplevel().title(title)
  t.pack(expand=True, fill=tk.BOTH)
  if os.path.exists(filename):
    with open(filename) as f:
      t.insert(tk.END, f.read())
  t.filename = filename
  t['font'] = FONT  # See below.


def reset_log(*args):
  log.delete('0.0', tk.END)
  print __doc__
  return args


def show_log(*args):
  log_window.wm_deiconify()
  log_window.update()
  return args


def grand_reset(s, e, d):
  stack = load_stack() or ()
  reset_text(log, LOG_FN)
  reset_text(t, JOY_FN)
  return stack, e, d


def reset_text(t, filename):
  if os.path.exists(filename):
    with open(filename) as f:
      data = f.read()
    if  data:
      t.delete('0.0', tk.END)
      t.insert(tk.END, data)


def load_stack():
  if os.path.exists(STACK_FN):
    with open(STACK_FN) as f:
      try:
        return pickle.load(f)
      except:
        traceback.print_exc()


D = initialize()
for func in (reset_log, show_log, grand_reset):
  D[func.__name__] = func
stack = load_stack()
if stack is None:
  w = StackDisplayWorld(dictionary=D)
else:
  w = StackDisplayWorld(stack=stack, dictionary=D)
t = TextViewerWidget(w)
log_window = tk.Toplevel()
log_window.protocol("WM_DELETE_WINDOW", log_window.withdraw)
log = TextViewerWidget(w, log_window, width=80, height=50)
FONT = get_font('Iosevka')  # Requires Tk root already set up.
init_text(log, 'Log', LOG_FN)
init_text(t, 'Joy', JOY_FN)


GLOBAL_COMMANDS = {
  '<F12>': 'words',
  '<F1>': 'reset_log show_log',
  '<Escape>': 'clear reset_log show_log',
  }
for event, command in GLOBAL_COMMANDS.items():
  t.bind_all(event, lambda _, _command=command: w.interpret(_command))


sys.stdout, old_stdout = FileFaker(log), sys.stdout
try:
  t.mainloop()
finally:
  sys.stdout = old_stdout
