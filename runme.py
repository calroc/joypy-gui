#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''\
Joypy - Copyright © 2018 Simon Forman
This program comes with ABSOLUTELY NO WARRANTY; for details right-click "warranty".
This is free software, and you are welcome to redistribute it under certain conditions; right-click "sharing" for details.
Right-click "words" to see a list of all words, and ... to print the docs for a word.

Mouse button chords.

L M R - command
1     - Point, sweep selection
1 2   - Cut the selection, place text on stack
1   2 - Run the selection as Joy code

  1   - Paste selection (bypass stack), scroll
2 1   - Paste from top of stack, preserve
  1 2 - Paste from top of stack, pop

    1 - Execute command word under mouse cursor
2   1 - Print docs of command word under mouse cursor
  2 1 - Lookup word (kinda useless now)

'''
import os, pickle, sys, traceback
from joy.utils.stack import stack_to_string
from joy.library import initialize
from gui.misc import FileFaker
from gui.textwidget import TextViewerWidget, tk, get_font
from gui.world import World


JOY_HOME = os.environ.get('JOY_HOME', '.')
STACK_FN = os.path.join(JOY_HOME, 'stack.pickle')
JOY_FN = os.path.join(JOY_HOME, 'scratch.txt')
LOG_FN = os.path.join(JOY_HOME, 'log.txt')


class StackDisplayWorld(World):

  def print_stack(self):
    print '\n%s <-' % stack_to_string(self.stack)

  def save(self):
    with open(STACK_FN, 'wb') as f:
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


D = initialize()
D['reset_log'] = reset_log
D['show_log'] = show_log
if os.path.exists(STACK_FN):
  with open(STACK_FN) as f:
    try:
      stack = pickle.load(f)
    except:
      traceback.print_exc()
      w = StackDisplayWorld(dictionary=D)
    else:
      w = StackDisplayWorld(stack=stack, dictionary=D)
t = TextViewerWidget(w)
log_window = tk.Toplevel()
log_window.protocol("WM_DELETE_WINDOW", log_window.withdraw)
log = TextViewerWidget(w, log_window, width=80, height=50)
FONT = get_font()  # Requires Tk root already set up.
init_text(log, 'Log', LOG_FN)
init_text(t, 'Joy', JOY_FN)


sys.stdout, old_stdout = FileFaker(log), sys.stdout
try:
  t.mainloop()
finally:
  sys.stdout = old_stdout
