import string
import pygame
from core import (
    ARROW_KEYS,
    BACKGROUND as BG,
    FOREGROUND as FG,
    CommandMessage,
    ModifyMessage,
    )
import viewer
reload(viewer)


MenuViewer = viewer.MenuViewer


def _is_command(display, word):
    return display.lookup(word) or word.isdigit() or all(
        not s or s.isdigit() for s in word.split('.', 1)
        ) and len(word) > 1


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

    MINIMUM_HEIGHT = FONT.line_h + 3
    CLOSE_TEXT = FONT.render('close')
    GROW_TEXT = FONT.render('grow')

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
            r = self.x * FONT.char_w, self.screen_y(), self.w, self.h
            self.mem.blit(self.v.body_surface, (0, 0), r)
            self.v.body_surface.fill(FG, r)
            self.can_fade = True

        def fade(self):
            if self.can_fade:
                dest = self.x * FONT.char_w, self.screen_y()
                self.v.body_surface.blit(self.mem, dest)
                self.can_fade = False

        def screen_y(self, row=None):
            if row is None: row = self.y
            return (row - self.v.at_line) * FONT.line_h

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
        self.command = None

    def resurface(self, surface):
        self.cursor.fade()
        MenuViewer.resurface(self, surface)

        w, h = self.CLOSE_TEXT.get_size()
        self.close_rect = pygame.rect.Rect(self.w - 2 - w, 1, w, h)
        w, h = self.GROW_TEXT.get_size()
        self.grow_rect = pygame.rect.Rect(1, 1, w, h)

        self.body_surface = surface.subsurface(self.body_rect)
        self.line_w = self.body_rect.w / FONT.char_w + 1
        self.h_in_lines = self.body_rect.h / FONT.line_h - 1
        self.command_rect = self.command = None

    def handle(self, message):
        if super(TextViewer, self).handle(message):
            return
        if (isinstance(message, ModifyMessage)
            and message.subject is self.lines
            ):
            # TODO: check self.at_line
            self.draw_body()

    def draw_menu(self):
        #MenuViewer.draw_menu(self)
        self.surface.blit(self.GROW_TEXT, (1, 1))
        self.surface.blit(self.CLOSE_TEXT,
                          (self.w - 2 - self.CLOSE_TEXT.get_width(), 1))
        

    def draw_body(self):
        MenuViewer.draw_body(self)
        ys = xrange(0, self.body_rect.height, FONT.line_h)
        ls = self.lines[self.at_line:self.at_line + self.h_in_lines + 2]
        for y, line in zip(ys, ls):
            self.draw_line(y, line)

    def draw_line(self, y, line):
        surface = FONT.render(line[:self.line_w])
        self.body_surface.blit(surface, (0, y))

    def _redraw_line(self, row):
        try: line = self.lines[row]
        except IndexError: line = ' ' * self.line_w
        else:
            n = self.line_w - len(line)
            if n > 0: line = line + ' ' * n
        self.draw_line(self.cursor.screen_y(row), line)

    def focus(self):
        self.cursor.v = self
        self.cursor.draw()

    def unfocus(self):
        self.cursor.fade()

    def scroll_up(self):
        if self.at_line < len(self.lines) - 1:
            self._fade_command()
            self.at_line += 1
            self.body_surface.scroll(0, -FONT.line_h)
            row = self.h_in_lines + self.at_line
            self._redraw_line(row)
            self._redraw_line(row + 1)
            self.cursor.draw()

    def scroll_down(self):
        if self.at_line:
            self._fade_command()
            self.at_line -= 1
            self.body_surface.scroll(0, FONT.line_h)
            self._redraw_line(self.at_line)
            self.cursor.draw()

    def command_down(self, display, x, y):
        if self.command_rect and self.command_rect.collidepoint(x, y):
            return
        self._fade_command()
        line, column, row = self.at(x, y)
        word_start = line.rfind(' ', 0, column) + 1
        word_end = line.find(' ', column)
        if word_end == -1: word_end = len(line)
        word = line[word_start:word_end]
        if not _is_command(display, word):
            return
        r = self.command_rect = pygame.Rect(
            word_start * FONT.char_w, # x
            y / FONT.line_h * FONT.line_h, # y
            len(word) * FONT.char_w, # w
            FONT.line_h # h
            )
        pygame.draw.line(self.body_surface, FG, r.bottomleft, r.bottomright)
        self.command = word

    def command_up(self, display):
        if self.command:
            command = self.command
            self._fade_command()
            display.broadcast(CommandMessage(self, command))

    def _fade_command(self):
        self.command = None
        r, self.command_rect = self.command_rect, None
        if r:
            pygame.draw.line(self.body_surface, BG, r.bottomleft, r.bottomright)

    def at(self, x, y):
        '''
        Given screen coordinates return the line, row, and column of the
        character there.
        '''
        row = self.at_line + y / FONT.line_h
        try:
            line = self.lines[row]
        except IndexError:
            row = len(self.lines) - 1
            line = self.lines[row]
            column = len(line)
        else:
            column = min(x / FONT.char_w, len(line))
        return line, column, row

    def body_click(self, display, x, y, button):
        if button == 1:
            line, column, row = self.at(x, y)
            self.cursor.set_to(column, row)
        elif button == 2:
            if pygame.KMOD_SHIFT & pygame.key.get_mods():
                self.scroll_up()
            else:
                self.scroll_down()
        elif button == 3:
            self.command_down(display, x, y)
        elif button == 4: self.scroll_down()
        elif button == 5: self.scroll_up()

    def menu_click(self, display, x, y, button):
        if MenuViewer.menu_click(self, display, x, y, button):
            return True

    def mouse_up(self, display, x, y, button):
        if MenuViewer.mouse_up(self, display, x, y, button):
            return True
        elif button == 3 and self.body_rect.collidepoint(x, y):
            self.command_up(display)

    def mouse_motion(self, display, x, y, rel_x, rel_y, button0, button1, button2):
        if MenuViewer.mouse_motion(self, display, x, y, rel_x, rel_y,
                                   button0, button1, button2):
            return True
        if (button0
            and display.focused_viewer is self
            and self.body_rect.collidepoint(x, y)
            ):
            bx, by = self.body_rect.topleft
            line, column, row = self.at(x - bx, y - by)
            self.cursor.set_to(column, row)
        elif button2 and self.body_rect.collidepoint(x, y):
            bx, by = self.body_rect.topleft
            self.command_down(display, x - bx, y - by)

    def key_down(self, display, uch, key, mod):

        if key in ARROW_KEYS:
            self._arrow_key(key, mod)
            return

        line, i = self.lines[self.cursor.y], self.cursor.x

        modified = ()
        if key == pygame.K_r:
            display.broadcast(CommandMessage(self, '23'))
        elif key == pygame.K_RETURN:
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
        self.draw_line(self.cursor.screen_y(), line)
        self.cursor.draw()

    def _backspace_key(self, mod, line, i):
        res = False
        if i:
            line = line[:i - 1] + line[i:]
            self.lines[self.cursor.y] = line
            self.cursor.fade()
            self.cursor.x -= 1
            self.draw_line(self.cursor.screen_y(), line + ' ')
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
            self.draw_line(self.cursor.screen_y(), line + ' ')
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
