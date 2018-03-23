'''
This file is execfile()'d with a namespace containing:

  D - the Joy dictionary
  d - the Display object
  pt - the PersistTask object
  log - the log.txt viewer
  loop - the TheLoop main loop object
  stack_holder - the Python list object that holds the Joy stack tuple
  world - the Joy environment

'''
from joy.library import FunctionWrapper, SimpleFunctionWrapper
from joy.utils.stack import list_to_stack, pushback


def install(command): D[command.name] = command


@install
@SimpleFunctionWrapper
def good_viewer_location(stack):
    viewers = list(d.iter_viewers())
    if viewers:
        viewers.sort(key=lambda (V, x, y): V.w * V.h)
        V, x, y = viewers[-1]
        coords = (x + 1, (y + V.h / 2, ()))
    else:
        coords = (0, (0, ()))
    return coords, stack


@install
@FunctionWrapper
def cmp_(stack, expression, dictionary):
    L, (E, (G, (b, (a, stack)))) = stack
    expression = pushback(G if a > b else L if a < b else E, expression)
    return stack, expression, dictionary


@install
@SimpleFunctionWrapper
def list_viewers(stack):
    lines = []
    for x, T in d.tracks:
        lines.append('x: %i, w: %i, %r' % (x, T.w, T))
        for y, V in T.viewers:
            lines.append('    y: %i, h: %i, name: %s, %r' % (y, V.h, V.content_id, V))
    return '\n'.join(lines), stack


@install
@SimpleFunctionWrapper
def splitlines(stack):
    text, stack = stack
    assert isinstance(text, str), repr(text)
    return list_to_stack(text.splitlines()), stack


@install
@SimpleFunctionWrapper
def hiya(stack):
    if d.focused_viewer:
        d.focused_viewer.insert('Hi World!')
    return stack
