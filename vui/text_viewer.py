import string
import pygame
from core import (
    ARROW_KEYS,
    BACKGROUND as BG,
    FOREGROUND as FG,
    ModifyMessage,
    )
import viewer
reload(viewer)


MenuViewer = viewer.MenuViewer


class Font(object):

    IMAGE = pygame.image.load('Iosevka12.BMP')
    LOOKUP = (string.ascii_letters +
              string.digits +
              '''@#$&_~|`'"%^=-+*/\<>[]{}(),.;:!?''')

    def __init__(self, char_w=8, char_h=19, line_h=19):
        self.char_w = char_w
        self.char_h = char_h
        self.line_h = line_h

    def size(self, text):
        return self.char_w * len(text), self.line_h

    def render(self, text):
        surface = pygame.Surface(self.size(text))
        surface.fill(BG)
        x = 0
        for ch in text:
            if not ch.isspace():
                try:
                    i = self.LOOKUP.index(ch)
                except ValueError:
                    # render a lil box...
                    r = (x + 1, self.line_h / 2 - 3,
                         self.char_w - 2, self.line_h / 2)
                    pygame.draw.rect(surface, FG, r, 1)
                else:
                    iy, ix = divmod(i, 26)
                    ix *= self.char_w
                    iy *= self.char_h
                    area = ix, iy, self.char_w, self.char_h
                    surface.blit(self.IMAGE, (x, 0), area)
            x += self.char_w
        return surface

    def __contains__(self, char):
        assert len(char) == 1, repr(char)
        return char in self.LOOKUP


FONT = Font()


class TextViewer(MenuViewer):

    class Cursor(object):

        def __init__(self, viewer):
            self.v = viewer
            self.x = self.y = 0
            self.w, self.h = 2, FONT.line_h
            self.mem = pygame.Surface((self.w, self.h))
            self.can_fade = False

        def set_to(self, x, y):
            self.fade()
            self.x, self.y = x, y
            self.draw()

        def draw(self):
            r = self.x * FONT.char_w, self.screen_y, self.w, self.h
            self.mem.blit(self.v.body_surface, (0, 0), r)
            self.v.body_surface.fill(FG, r)
            self.can_fade = True

        def fade(self):
            if self.can_fade:
                dest = self.x * FONT.char_w, self.screen_y
                self.v.body_surface.blit(self.mem, dest)
                self.can_fade = False

        @property
        def screen_y(self):
            return (self.y - self.v.at_line) * FONT.line_h

        def up(self, mod):
            if self.y:
                self.fade()
                self.y -= 1
                self.x = min(self.x, len(self.v.lines[self.y]))
                self.draw()
                if self.y < self.v.at_line:
                    self.v.scroll_down()

        def down(self, mod):
            if self.y < len(self.v.lines) - 1:
                self.fade()
                self.y += 1
                self.x = min(self.x, len(self.v.lines[self.y]))
                self.draw()
                if self.y > self.v.at_line + self.v.h_in_lines :
                    self.v.scroll_up()

        def left(self, mod):
            if self.x:
                self.fade()
                self.x -= 1
                self.draw()
            elif self.y:
                self.fade()
                self.y -= 1
                self.x = len(self.v.lines[self.y])
                self.draw()
                if self.y < self.v.at_line:
                    self.v.scroll_down()

        def right(self, mod):
            if self.x < len(self.v.lines[self.y]):
                self.fade()
                self.x += 1
                self.draw()
            elif self.y < len(self.v.lines) - 1:
                self.fade()
                self.y += 1
                self.x = 0
                self.draw()
                if self.y > self.v.at_line + self.v.h_in_lines :
                    self.v.scroll_up()

    def __init__(self, surface):
        self.cursor = self.Cursor(self)
        MenuViewer.__init__(self, surface)
        self.lines = ['']
        self.content_id = None
        self.at_line = 0
        self.bg = BG

    def scroll_up(self):
        if self.at_line < len(self.lines) - 1:
            self.at_line += 1
            self.draw_body()
            self.cursor.draw()

    def scroll_down(self):
        if self.at_line:
            self.at_line -= 1
            self.draw_body()
            self.cursor.draw()

    def resurface(self, surface):
        self.cursor.fade()
        MenuViewer.resurface(self, surface)
        self.body_surface = surface.subsurface(self.body_rect)
        self.line_w = self.body_rect.w / FONT.char_w + 1
        self.h_in_lines = self.body_rect.h / FONT.line_h - 1

    def handle(self, message):
        if super(TextViewer, self).handle(message):
            return
        if (isinstance(message, ModifyMessage)
            and message.subject is self.lines
            ):
            # TODO: check self.at_line
            self.draw_body()

    def draw_menu(self):
        MenuViewer.draw_menu(self)

    def draw_body(self):
        MenuViewer.draw_body(self)
        y, h = 0, self.body_rect.height
        for line in self.lines[self.at_line:]:
            if y > h: break
            self.draw_line(y, line)
            y += FONT.line_h

    def draw_line(self, y, line):
        surface = FONT.render(line[:self.line_w])
        self.body_surface.blit(surface, (0, y))

    def focus(self):
        self.cursor.v = self
        self.cursor.draw()

    def unfocus(self):
        self.cursor.fade()

    def body_click(self, display, x, y, button):
        if button == 1:
            i, line, index = self.at(x, y)
            self.cursor.set_to(index, i)
        elif button == 2:
            self.scroll_down()
        elif button == 3:
            self.scroll_up()

    def at(self, x, y):
        i = self.at_line + y / FONT.line_h
        try:
            line = self.lines[i]
        except IndexError:
            i = len(self.lines) - 1
            line = self.lines[i]
            index = len(line)
        else:
            index = min(x / FONT.char_w, len(line))
        return i, line, index

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
        if (button0
            and display.focused_viewer is self
            and self.body_rect.collidepoint(x, y)
            ):
            bx, by = self.body_rect.topleft
            row, line, column = self.at(x - bx, y - by)
            self.cursor.set_to(column, row)

    def key_down(self, display, uch, key, mod):

        if key in ARROW_KEYS:
            self._arrow_key(key, mod)
            return

        line, i = self.lines[self.cursor.y], self.cursor.x

        modified = ()
        if key == pygame.K_RETURN:
            self._return_key(mod, line, i)
            modified = True
        elif key == pygame.K_BACKSPACE:
            modified = self._backspace_key(mod, line, i)
        elif key == pygame.K_DELETE:
            modified = self._delete_key(mod, line, i)
        elif uch and uch in FONT or uch == ' ':
            self._printable_key(uch, mod, line, i)
            modified = True
        else:
            print '%r %i %s' % (uch, key, bin(mod))

        if modified:
            message = ModifyMessage(
                self, self.lines, content_id=self.content_id)
            display.broadcast(message)

    def _printable_key(self, uch, mod, line, i):
        line = line[:i] + uch + line[i:]
        self.lines[self.cursor.y] = line
        self.cursor.fade()
        self.cursor.x += 1
        self.draw_line(self.cursor.screen_y, line)
        self.cursor.draw()

    def _backspace_key(self, mod, line, i):
        res = False
        if i:
            line = line[:i - 1] + line[i:]
            self.lines[self.cursor.y] = line
            self.cursor.fade()
            self.cursor.x -= 1
            self.draw_line(self.cursor.screen_y, line + ' ')
            self.cursor.draw()
            res = True
        elif self.cursor.y:
            y = self.cursor.y
            left, right = self.lines[y - 1:y + 1]
            self.lines[y - 1:y + 1] = [left + right]
            self.cursor.x = len(left)
            self.cursor.y -= 1
            self.draw_body()
            self.cursor.draw()
            res = True
        return res

    def _delete_key(self, mod, line, i):
        res = False
        if i < len(line):
            line = line[:i] + line[i + 1:]
            self.lines[self.cursor.y] = line
            self.cursor.fade()
            self.draw_line(self.cursor.screen_y, line + ' ')
            self.cursor.draw()
            res = True
        elif self.cursor.y < len(self.lines) - 1:
            y = self.cursor.y
            left, right = self.lines[y:y + 2]
            self.lines[y:y + 2] = [left + right]
            self.draw_body()
            self.cursor.draw()
            res = True
        return res

    def _arrow_key(self, key, mod):
        if key == pygame.K_UP: self.cursor.up(mod)
        elif key == pygame.K_DOWN: self.cursor.down(mod)
        elif key == pygame.K_LEFT: self.cursor.left(mod)
        elif key == pygame.K_RIGHT: self.cursor.right(mod)

    def _return_key(self, mod, line, i):
        self.cursor.fade()
        # Ignore the mods for now.
        n = self.cursor.y
        self.lines[n:n + 1] = [line[:i], line[i:]]
        self.cursor.y += 1
        self.cursor.x = 0
        if self.cursor.y > self.at_line + self.h_in_lines:
            self.scroll_up()
        else:
            self.draw_body()
            self.cursor.draw()
