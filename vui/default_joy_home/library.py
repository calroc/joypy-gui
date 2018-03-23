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
from joy.library import (
    DefinitionWrapper,
    FunctionWrapper,
    SimpleFunctionWrapper,
    )
from joy.utils.stack import list_to_stack, pushback
import core, text_viewer, stack_viewer


def install(command): D[command.name] = command


@install
@SimpleFunctionWrapper
def list_resources(stack):
    return '\n'.join(pt.scan()), stack


@install
@SimpleFunctionWrapper
def open_stack(stack):
    (x, (y, _)), stack = stack
    V = d.open_viewer(x, y, stack_viewer.StackViewer)
    V.draw()
    return stack


@install
@SimpleFunctionWrapper
def open_resource(stack):
    ((x, (y, _)), (name, stack)) = stack
    om = core.OpenMessage(world, name)
    d.broadcast(om)
    if om.status == core.SUCCESS:
        V = d.open_viewer(x, y, text_viewer.TextViewer)
        V.content_id, V.lines = om.content_id, om.thing
        V.draw()
    return stack


@install
@SimpleFunctionWrapper
def name_viewer(stack):
    name, stack = stack
    assert isinstance(name, str), repr(name)
    if d.focused_viewer and not d.focused_viewer.content_id:
        d.focused_viewer.content_id = name
        pm = core.PersistMessage(world, name, thing=d.focused_viewer.lines)
        d.broadcast(pm)
        d.focused_viewer.draw_menu()
    return stack


##@install
##@SimpleFunctionWrapper
##def persist_viewer(stack):
##    if self.focused_viewer:
##        
##        self.focused_viewer.content_id = name
##        self.focused_viewer.draw_menu()
##    return stack


@install
@SimpleFunctionWrapper
def inscribe(stack):
    definition, stack = stack
    DefinitionWrapper.add_def(definition, D)
    return stack


@install
@SimpleFunctionWrapper
def open_viewer(stack):
    ((x, (y, _)), (content, stack)) = stack
    V = d.open_viewer(x, y, text_viewer.TextViewer)
    V.lines = content.splitlines()
    V.draw()
    return stack


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
