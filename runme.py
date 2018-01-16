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
import os, pickle, sys
from joy.utils.stack import stack_to_string
from joy.library import initialize
from gui.misc import FileFaker
from gui.textwidget import TextViewerWidget, tk, get_font
from gui.world import World


class StackDisplayWorld(World):

  def print_stack(self):
    print '\n' + stack_to_string(self.stack)

  def save(self):
    with open('stack.pickle', 'wb') as f:
      pickle.dump(self.stack, f)
      f.flush()
      os.fsync(f.fileno())


def init_text(t, title, filename):
  t.winfo_toplevel().title(title)
  t.pack(expand=True, fill=tk.BOTH)
  t.filename = filename
  t['font'] = FONT  # See below.


D = initialize()
w = StackDisplayWorld(dictionary=D)

t = TextViewerWidget(w)
log = TextViewerWidget(w, tk.Toplevel(), width=80, height=50)
FONT = get_font()  # Requires Tk root already set up.
init_text(log, 'Log', 'log.txt')
init_text(t, 'Joy', 'scratch.txt')


def reset_log(*args):
  log.delete('0.0', tk.END)
  print __doc__
  return args
D['reset_log'] = reset_log


sys.stdout, old_stdout = FileFaker(log), sys.stdout
try:
  reset_log()
  t.mainloop()
finally:
  sys.stdout = old_stdout
