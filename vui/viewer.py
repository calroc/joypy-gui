# -*- coding: utf-8 -*-
#
#    Copyright © 2018 Simon Forman
#
#    This file is part of joy.py
#
#    joy.py is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    joy.py is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with joy.py.  If not see <http://www.gnu.org/licenses/>.
#
'''
This module implements a simple visual display system modeled on Oberon.

Refer to Chapter 4 of the Project Oberon book for more information.

There is a Display object that manages a pygame surface and N  vertical
tracks each of which manages zero or more viewers.


Still to do:
* Persistance of data
* Joy integration
* Command evaluation
  * Menu text, commands and name or title
* Selecting text
  * Cut/Copy/Paste
* Home/End keys
* Vertical scrolling w/ scrollbar
* Horizontal scrolling w/ keys
* Horizontal scrolling w/ scrollbar
* Pgup/down keys?
* Tab key?

Done:
- Content change notification
- Vertical scrolling w/ keys
- Enter/return key
- Arrow keys should wrap at line ends
- Backspace/delete wrap at line ends

'''
from copy import copy
import pygame
from core import BACKGROUND, FOREGROUND, GREY, MOUSE_EVENTS


class Display(object):
    '''
    Manage tracks and viewers on a screen (Pygame surface.)

    The size and number of tracks are defined by passing in at least two
    ratios, e.g. Display(screen, 1, 4, 4) would create three tracks, one
    small one on the left and two larger ones of the same size, each four
    times wider than the left one.

    All tracks take up the whole height of the display screen.  Tracks
    manage zero or more Viewers.  When you "grow" a viewer a new track is
    created that overlays or hides one or two existing tracks, and when
    the last viewer in an overlay track is closed the track closes too
    and reveals the hidden tracks (and their viewers, if any.)
    '''

    def __init__(self, screen, *track_ratios):
        self.screen = screen
        self.w, self.h = screen.get_width(), screen.get_height()
        self.focused_viewer = None
        self.tracks = []  # (x, track)
        self.handlers = []
        # Create the tracks.
        if not track_ratios: track_ratios = 1, 4
        x, total = 0, sum(track_ratios)
        for ratio in track_ratios[:-1]:
            track_width = self.w * ratio / total
            assert track_width >= 10  # minimum width 10 pixels
            self._open_track(x, track_width)
            x += track_width
        self._open_track(x, self.w - x)

    def _open_track(self, x, w):
        '''Helper function to create the pygame surface and Track.'''
        track_surface = self.screen.subsurface((x, 0, w, self.h))
        self.tracks.append((x, Track(track_surface)))

    def open_viewer(self, x, y, class_):
        '''
        Open a viewer of class_ at the x, y location on the display,
        return the viewer.
        '''
        track = self._track_at(x)[0]
        return track.open_viewer(y, class_)

    def close_viewer(self, viewer):
        '''Close the viewer.'''
        for x, track in self.tracks:
            if track.close_viewer(viewer):
                if not track.viewers and track.hiding:
                    i = self.tracks.index((x, track))
                    self.tracks[i:i + 1] = track.hiding
                    assert sorted(self.tracks) == self.tracks
                    for _, exposed_track in track.hiding:
                        exposed_track.redraw()
                if viewer is self.focused_viewer:
                    self.focused_viewer = None
                break

    def change_viewer(self, viewer, y, relative=False):
        '''
        Adjust the top of the viewer to a new y within the boundaries of
        its neighbors.

        If relative is False new_y should be in screen coords, else new_y
        should be relative to the top of the viewer.
        '''
        for _, track in self.tracks:
            if track.change_viewer(viewer, y, relative):
                break

    def grow_viewer(self, viewer):
        '''
        Cause the viewer to take up its whole track or, if it does
        already, take up another track, up to the whole screen.

        This is the inverse of closing a viewer.  "Growing" a viewer
        actually creates a new copy and a new track to hold it.  The old
        tracks and viewers are retained, and they get restored when the
        covering track closes, which happens automatically when the last
        viewer in that track is closed.
        '''
        for x, track in self.tracks:
            for _, V in track.viewers:
                if V is viewer:
                    return self._grow_viewer(x, track, viewer)

    def _grow_viewer(self, x, track, viewer):
        '''Helper function to "grow" a viewer.'''
        new_viewer = None

        if viewer.h < self.h:
            # replace the track with a new track that contains
            # a copy of the viewer at full height.
            new_track = Track(track.surface)  # Reuse it, why not?
            new_viewer = copy(viewer)
            new_track._grow_by(new_viewer, 0, self.h - viewer.h)
            new_track.viewers.append((0, new_viewer))
            new_track.hiding = [(x, track)]
            self.tracks[self.tracks.index((x, track))] = x, new_track

        elif viewer.w < self.w:
            # replace two tracks
            i = self.tracks.index((x, track))
            try: # prefer the one on the right
                xx, xtrack = self.tracks[i + 1]
            except IndexError:
                i -= 1 # okay, the one on the left
                xx, xtrack = self.tracks[i]
                hiding = [(xx, xtrack), (x, track)]
            else:
                hiding = [(x, track), (xx, xtrack)]
            # We know there has to be at least one other track because it
            # there weren't then that implies that the one track takes up
            # the whole display screen (the only way you can get just one
            # track is by growing a viewer to cover the whole screen.)
            # Ergo, viewer.w == self.w, so this branch doesn't run.
            new_x = min(x, xx)
            new_w = track.w + xtrack.w
            r = new_x, 0, new_w, self.h
            new_track = Track(self.screen.subsurface(r))
            new_viewer = copy(viewer)
            r = 0, 0, new_w, self.h
            new_viewer.resurface(new_track.surface.subsurface(r))
            new_track.viewers.append((0, new_viewer))
            new_track.hiding = hiding
            self.tracks[i:i + 2] = [(new_x, new_track)]
            new_viewer.draw()

        return new_viewer

    def _move_viewer(self, to, rel_y, viewer, x, y):
        '''
        Helper function to move (really copy) a viewer to a new location.
        '''
        h = to.split(rel_y)
        new_viewer = copy(viewer)
        if not isinstance(to, Track):
            to = next(T for _, T in self.tracks
                        for _, V in T.viewers
                            if V is to)
        new_viewer.resurface(to.surface.subsurface((0, y, to.w, h)))
        to.viewers.append((y, new_viewer))
        to.viewers.sort()  # bisect.insort() would be overkill here.
        new_viewer.draw()
        self.close_viewer(viewer)

    def _track_at(self, x):
        '''
        Return the track at x along with the track-relative x coordinate,
        raise ValueError if x is off-screen.
        '''
        for track_x, track in self.tracks:
            if x < track_x + track.w:
                return track, x - track_x
        raise ValueError('x outside display: %r' % (x,))

    def at(self, x, y):
        '''
        Return the viewer (which can be a Track) at the x, y location,
        along with the relative-to-viewer-surface x and y coordinates.
        If there is no viewer at the location the Track will be returned
        instead.
        '''
        track, x = self._track_at(x)
        viewer, y = track.viewer_at(y)
        return viewer, x, y

    def broadcast(self, message):
        for _, track in self.tracks:
            track.broadcast(message)
        for handler in self.handlers:
            handler(message)

    def redraw(self):
        for _, track in self.tracks:
            track.redraw()

    def focus(self, viewer):
        if isinstance(viewer, Track):
            if self.focused_viewer: self.focused_viewer.unfocus()
            self.focused_viewer = None
        elif viewer is not self.focused_viewer:
            if self.focused_viewer: self.focused_viewer.unfocus()
            self.focused_viewer = viewer
            viewer.focus()

    def dispatch_event(self, event):
        '''
        Display event handling.
        '''
        # Keyboard events.
        if event.type == pygame.KEYUP:
            if self.focused_viewer:
                self.focused_viewer.key_up(self, event.key, event.mod)
            return
        if event.type == pygame.KEYDOWN:
            if self.focused_viewer:
                self.focused_viewer.key_down(
                    self, event.unicode, event.key, event.mod)
            return

        # Mouse events.
        assert event.type in MOUSE_EVENTS  # Use pygame.event.set_allowed().

        V, x, y = self.at(*event.pos)

        if event.type == pygame.MOUSEMOTION:
            if not isinstance(V, Track):
                V.mouse_motion(self, x, y, *(event.rel + event.buttons))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.focus(V)
            V.mouse_down(self, x, y, event.button)

        elif event.type == pygame.MOUSEBUTTONUP:

            # Check for moving viewer.
            if (event.button == 2
                and self.focused_viewer
                and V is not self.focused_viewer
                and V.MINIMUM_HEIGHT < y < V.h - self.focused_viewer.MINIMUM_HEIGHT
                ):
                self._move_viewer(V, y, self.focused_viewer, *event.pos)

            else:
                V.mouse_up(self, x, y, event.button)


class Viewer(object):

    MINIMUM_HEIGHT = 11

    def __init__(self, surface):
        self.resurface(surface)
        self.last_touch = 0, 0

    def resurface(self, surface):
        self.w, self.h = surface.get_width(), surface.get_height()
        self.surface = surface

    def split(self, y):
        '''
        Split the viewer at the y coordinate (which is relative to the
        viewer's surface and must be inside it somewhere) and return the
        remaining height.  The upper part of the viewer remains (and gets
        redrawn on a new surface) and the lower space is now available
        for e.g. a new viewer.
        '''
        assert y >= self.MINIMUM_HEIGHT
        new_viewer_h = self.h - y
        self.resurface(self.surface.subsurface((0, 0, self.w, y)))
        if y <= self.last_touch[1]: self.last_touch = 0, 0
        self.draw()
        return new_viewer_h

    def handle(self, message):
        assert self is not message.sender
        pass

    def draw(self):
        '''Draw the viewer onto its surface.'''
        self.surface.fill(BACKGROUND)
        x, y, h = self.w - 1, self.MINIMUM_HEIGHT, self.h - 1
        # Right-hand side.
        pygame.draw.line(self.surface, FOREGROUND, (x, 0), (x, h))
        # Between header and body.
        pygame.draw.line(self.surface, FOREGROUND, (0, y), (x, y))
        # Bottom.
        pygame.draw.line(self.surface, FOREGROUND, (0, h), (x, h))

    def close(self):
        '''Close the viewer and release any resources, etc...'''

    def focus(self):
        pass

    def unfocus(self):
        pass

    # Event handling.

    def mouse_down(self, display, x, y, button):
        self.last_touch = x, y

    def mouse_up(self, display, x, y, button):
        pass

    def mouse_motion(self, display, x, y, dx, dy, button0, button1, button2):
        pass

    def key_up(self, display, key, mod):
        if key == pygame.K_q and mod & pygame.KMOD_CTRL: # Ctrl-q
            display.close_viewer(self)
            return True
        if key == pygame.K_g and mod & pygame.KMOD_CTRL: # Ctrl-g
            display.grow_viewer(self)
            return True

    def key_down(self, display, uch, key, mod):
        pass


class Track(Viewer):

    def __init__(self, surface):
        Viewer.__init__(self, surface)
        self.viewers = []  # (y, viewer)
        self.hiding = None
        self.draw()

    def split(self, y):
        '''
        Split the Track at the y coordinate and return the height
        available for a new viewer.  Tracks manage a vertical strip of
        the display screen so they don't resize their surface when split.
        '''
        h = self.viewers[0][0] if self.viewers else self.h
        assert h > y
        return h - y

    def draw(self, rect=None):
        '''Draw the track onto its surface, clearing all content.

        If rect is passed only draw to that area.  This supports e.g.
        closing a viewer that then exposes part of the track.
        '''
        self.surface.fill(GREY, rect=rect)

    def viewer_at(self, y):
        '''
        Return the viewer at y along with the viewer-relative y coordinate,
        if there's no viewer at y return this track and y.
        '''
        for viewer_y, viewer in self.viewers:
            if viewer_y < y <= viewer_y + viewer.h:
                return viewer, y - viewer_y
        return self, y

    def open_viewer(self, y, class_):
        '''Open and return a viewer of class_ at y.'''
        # Todo: if y coincides with some other viewer's y replace it.
        viewer, viewer_y =  self.viewer_at(y)
        h = viewer.split(viewer_y)
        new_viewer = class_(self.surface.subsurface((0, y, self.w, h)))
        new_viewer.draw()
        self.viewers.append((y, new_viewer))
        self.viewers.sort()  # Could use bisect module but how many
                             # viewers will you ever have?
        return new_viewer

    def close_viewer(self, viewer):
        '''Close the viewer, reuse the freed space.'''
        for y, V in self.viewers:
            if V is viewer:
                self._close_viewer(y, V)
                return True
        return False

    def _close_viewer(self, y, viewer):
        '''Helper function to do the actual closing.'''
        i = self.viewers.index((y, viewer))
        del self.viewers[i]
        if i: # The previous viewer gets the space.
            previous_y, previous_viewer = self.viewers[i - 1]
            self._grow_by(previous_viewer, previous_y, viewer.h)
        else: # This track gets the space.
            self.draw((0, y, self.w, viewer.surface.get_height()))
        viewer.close()

    def _grow_by(self, viewer, y, h):
        '''Grow a viewer (located at y) by height h.

        This might seem like it should be a method of the viewer, but
        the viewer knows nothing of its own y location on the screen nor
        the parent track's surface (to make a new subsurface) so it has
        to be a method of the track, which has both. 
        '''
        h = viewer.surface.get_height() + h
        try:
            surface = self.surface.subsurface((0, y, self.w, h))
        except ValueError:  # subsurface rectangle outside surface area
            pass
        else:
            viewer.resurface(surface)
            if h <= viewer.last_touch[1]: viewer.last_touch = 0, 0
            viewer.draw()

    def change_viewer(self, viewer, new_y, relative=False):
        '''
        Adjust the top of the viewer to a new y within the boundaries of
        its neighbors.

        If relative is False new_y should be in screen coords, else new_y
        should be relative to the top of the viewer.
        '''
        for old_y, V in self.viewers:
            if V is viewer:
                if relative: new_y += old_y
                if new_y != old_y: self._change_viewer(new_y, old_y, V)
                return True
        return False

    def _change_viewer(self, new_y, old_y, viewer):
        new_y = max(0, min(self.h, new_y))
        i = self.viewers.index((old_y, viewer))
        if new_y < old_y: # Enlarge self, shrink upper neighbor.
            if i:
                previous_y, previous_viewer = self.viewers[i - 1]
                if new_y - previous_y < self.MINIMUM_HEIGHT:
                    return
                h = previous_viewer.split(new_y - previous_y)
            else:
                h = old_y - new_y
            self._grow_by(viewer, new_y, h)
            
        else: # Shink self, enlarge upper neighbor.
            # Enforce invariant.
            try:
                h, _ = self.viewers[i + 1]
            except IndexError: # No next viewer.
                h = self.h
            if h - new_y < self.MINIMUM_HEIGHT:
                return

            # Change the viewer and adjust the upper viewer or track.
            h = new_y - old_y
            self._grow_by(viewer, new_y, -h) # grow by negative height!
            if i:
                previous_y, previous_viewer = self.viewers[i - 1]
                self._grow_by(previous_viewer, previous_y, h)
            else:
                self.draw((0, old_y, self.w, h))

        self.viewers[i] = new_y, viewer
        # self.viewers.sort()  # Not necessary, invariant holds.
        assert sorted(self.viewers) == self.viewers

    def broadcast(self, message):
        for _, viewer in self.viewers:
            if viewer is not message.sender:
                viewer.handle(message)

    def redraw(self):
        '''Redraw the track and all of its viewers.'''
        self.draw()
        for _, viewer in self.viewers:
            viewer.draw()


class MenuViewer(Viewer):

    MINIMUM_HEIGHT = 26

    def __init__(self, surface):
        Viewer.__init__(self, surface)
        self.resizing = 0
        self.bg = 100, 150, 100

    def resurface(self, surface):
        Viewer.resurface(self, surface)
        n = self.MINIMUM_HEIGHT - 2
        self.close_rect = pygame.rect.Rect(self.w - 2 - n, 1, n, n)
        self.grow_rect = pygame.rect.Rect(1, 1, n, n)
        self.body_rect = pygame.rect.Rect(
            0, self.MINIMUM_HEIGHT + 1,
            self.w - 1, self.h - self.MINIMUM_HEIGHT - 2)

    def draw(self):
        '''Draw the viewer onto its surface.'''
        Viewer.draw(self)
        if not self.resizing:
            self.draw_menu()
            self.draw_body()

    def draw_menu(self):
        # menu buttons
        pygame.draw.rect(self.surface, FOREGROUND, self.close_rect, 1)
        pygame.draw.rect(self.surface, FOREGROUND, self.grow_rect, 1)

    def draw_body(self):
        self.surface.fill(self.bg, self.body_rect)

    def mouse_down(self, display, x, y, button):
        Viewer.mouse_down(self, display, x, y, button)
        if y <= self.MINIMUM_HEIGHT:
            self.menu_click(display, x, y, button)
        else:
            bx, by = self.body_rect.topleft
            self.body_click(display, x - bx, y - by, button)

    def body_click(self, display, x, y, button):
        if button == 1:
            self.draw_an_a(x, y)

    def menu_click(self, display, x, y, button):
        if button == 1:
            self.resizing = 1
        elif button == 3:
            if self.close_rect.collidepoint(x, y):
                display.close_viewer(self)
                return True
            elif self.grow_rect.collidepoint(x, y):
                display.grow_viewer(self)
                return True

    def mouse_up(self, display, x, y, button):

        if button == 1 and self.resizing:
            if self.resizing == 2:
                self.resizing = 0
                self.draw()
            self.resizing = 0
            return True

    def mouse_motion(self, display, x, y, rel_x, rel_y, button0, button1, button2):
        if self.resizing and button0:
            self.resizing = 2
            display.change_viewer(self, rel_y, relative=True)
            return True
        else:
            self.resizing = 0
            #self.draw_an_a(x, y)

    def key_up(self, display, key, mod):
        if Viewer.key_up(self, display, key, mod):
            return True

    def draw_an_a(self, x, y):
        # Draw a crude letter A.
        lw, lh = 10, 14
        try: surface = self.surface.subsurface((x - lw, y - lh, lw, lh))
        except ValueError: return
        draw_a(surface, blend=1)


class SomeViewer(MenuViewer):

    def __init__(self, surface):
        MenuViewer.__init__(self, surface)

    def resurface(self, surface):
        MenuViewer.resurface(self, surface)

    def draw_menu(self):
        MenuViewer.draw_menu(self)

    def draw_body(self):
        pass

    def body_click(self, display, x, y, button):
        pass

    def menu_click(self, display, x, y, button):
        if MenuViewer.menu_click(self, display, x, y, button):
            return True

    def mouse_up(self, display, x, y, button):
        if MenuViewer.mouse_up(self, display, x, y, button):
            return True

    def mouse_motion(self, display, x, y, rel_x, rel_y, button0, button1, button2):
        if MenuViewer.mouse_motion(self, display, x, y, rel_x, rel_y,
                               button0, button1, button2):
            return True

    def key_down(self, display, uch, key, mod):
        try:
            print chr(key),
        except ValueError:
            pass


# Note that Oberon book says that if you split at the exact top of a viewer
# it should close, and I think this implies the new viewer gets the old
# viewer's whole height.  I haven't implemented that yet, so the edge-case
# in the code is broken by "intent" for now..


def draw_a(surface, color=FOREGROUND, blend=False):
    w, h = surface.get_width() - 2, surface.get_height() - 2
    pygame.draw.aalines(surface, color, False, (
        (1, h), (w / 2, 1), (w, h), (1, h / 2)
        ), blend)