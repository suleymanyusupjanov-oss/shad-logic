"""Симулятор исполнителя Робот из КуМира.

Координаты как на поле КуМира: x — номер столбца (1..W, слева направо),
y — номер строки (1..H, сверху вниз). Край поля — стена.
Шаг в стену -> исключение Отказ (в КуМире Робот «разбивается»).

Поле удобно задавать картинкой ASCII (from_ascii) — так же, как рисуют лабиринты:

    +-+-+-+-+
    |R . . .|      R — робот, . — пустая клетка, * — отмеченная точкой (её надо закрасить),
    + +-+-+ +      # — уже закрашенная, @ — робот в отмеченной клетке
    |. * *|.|      «|» между клетками — вертикальная стена,
    +-+-+-+-+      «-» под клеткой — горизонтальная стена

Использование в tasks/N/check.py (запуск из корня репозитория):
    import sys; sys.path.insert(0, "tools")
    from robot import Field, Robot, Отказ, from_ascii, show, compare
"""
import sys
try:  # Windows: всегда печатать в UTF-8, чтобы кириллица не превращалась в «?»
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class Отказ(Exception):
    """Робот шагнул в стену (или сделал слишком много шагов — похоже на бесконечный цикл)."""


_D = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


class Field:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.walls = set()        # множество frozenset({клетка1, клетка2}) — между ними стена
        self.painted = set()      # закрашенные клетки
        self.marked = set()       # отмеченные (точки) — ожидаемый результат примера
        self.rad = {}             # радиация в клетке
        self.temp = {}            # температура в клетке
        self.start = None         # где стоит робот

    # --- стены ---
    def inside(self, c):
        return 1 <= c[0] <= self.w and 1 <= c[1] <= self.h

    def wall(self, x, y, side):
        """Стена у клетки (x, y) со стороны side: 'U' сверху, 'D' снизу, 'L' слева, 'R' справа."""
        dx, dy = _D[side]
        self.walls.add(frozenset({(x, y), (x + dx, y + dy)}))

    def hwall(self, y, x1, x2):
        """Горизонтальная стена ПОД строкой y (между y и y+1) над столбцами x1..x2."""
        for x in range(x1, x2 + 1):
            self.wall(x, y, "D")

    def vwall(self, x, y1, y2):
        """Вертикальная стена СПРАВА от столбца x (между x и x+1) вдоль строк y1..y2."""
        for y in range(y1, y2 + 1):
            self.wall(x, y, "R")

    def blocked(self, c, side):
        dx, dy = _D[side]
        n = (c[0] + dx, c[1] + dy)
        return (not self.inside(n)) or frozenset({c, n}) in self.walls

    def copy(self):
        f = Field(self.w, self.h)
        f.walls, f.painted, f.marked = set(self.walls), set(self.painted), set(self.marked)
        f.rad, f.temp, f.start = dict(self.rad), dict(self.temp), self.start
        return f


class Robot:
    """Методы названы как команды КуМира (пробел заменён на «_»)."""

    def __init__(self, field, x=None, y=None, max_steps=1_000_000):
        self.f = field
        if x is None:
            if field.start is None:
                raise ValueError("не задано, где стоит робот")
            x, y = field.start
        self.x, self.y = x, y
        self.steps = 0
        self.max_steps = max_steps

    @property
    def pos(self):
        return (self.x, self.y)

    def _move(self, side, name):
        if self.f.blocked(self.pos, side):
            raise Отказ(f"Отказ: команда «{name}» из клетки {self.pos} — там стена")
        self.steps += 1
        if self.steps > self.max_steps:
            raise Отказ(f"Больше {self.max_steps} шагов — похоже на бесконечный цикл")
        dx, dy = _D[side]
        self.x += dx
        self.y += dy

    # команды
    def вверх(self): self._move("U", "вверх")
    def вниз(self): self._move("D", "вниз")
    def влево(self): self._move("L", "влево")
    def вправо(self): self._move("R", "вправо")
    def закрасить(self): self.f.painted.add(self.pos)

    # условия
    def сверху_свободно(self): return not self.f.blocked(self.pos, "U")
    def снизу_свободно(self): return not self.f.blocked(self.pos, "D")
    def слева_свободно(self): return not self.f.blocked(self.pos, "L")
    def справа_свободно(self): return not self.f.blocked(self.pos, "R")
    def сверху_стена(self): return self.f.blocked(self.pos, "U")
    def снизу_стена(self): return self.f.blocked(self.pos, "D")
    def слева_стена(self): return self.f.blocked(self.pos, "L")
    def справа_стена(self): return self.f.blocked(self.pos, "R")
    def клетка_закрашена(self): return self.pos in self.f.painted
    def клетка_чистая(self): return self.pos not in self.f.painted

    # значения
    def радиация(self): return self.f.rad.get(self.pos, 0)
    def температура(self): return self.f.temp.get(self.pos, 0)


def from_ascii(text):
    """Поле из ASCII-картинки (формат — в начале файла). Возвращает Field
    с заполненными walls, marked (*), painted (#), start (R/@)."""
    lines = [ln.rstrip() for ln in text.strip("\n").splitlines() if ln.strip()]
    lines = [ln.strip() for ln in lines]
    w = (len(lines[0]) - 1) // 2
    h = (len(lines) - 1) // 2
    f = Field(w, h)
    for y in range(1, h + 1):
        top = lines[2 * y - 2].ljust(2 * w + 1)
        row = lines[2 * y - 1].ljust(2 * w + 1)
        bottom = lines[2 * y].ljust(2 * w + 1)
        for x in range(1, w + 1):
            ch = row[2 * x - 1]
            if ch in "*@":
                f.marked.add((x, y))
            if ch == "#":
                f.painted.add((x, y))
            if ch in "R@":
                f.start = (x, y)
            if x < w and row[2 * x] == "|":
                f.wall(x, y, "R")
            if y < h and bottom[2 * x - 1] == "-":
                f.wall(x, y, "D")
        _ = top
    return f


def show(field, robot=None, expected=None, title=None):
    """Печатает поле. Если передан expected (множество клеток): # закрашено верно,
    * надо было закрасить, но не закрашено, x закрашено лишнее."""
    exp = field.marked if expected is None else expected
    rpos = robot.pos if robot else None
    if title:
        print(title)
    out = []
    for y in range(0, field.h + 1):
        s = "+"
        for x in range(1, field.w + 1):
            if y == 0 or y == field.h or field.blocked((x, y), "D"):
                s += "-+"
            else:
                s += " +"
        out.append(s)
        if y == field.h:
            break
        yy = y + 1
        s = "|"
        for x in range(1, field.w + 1):
            c = (x, yy)
            p, e = c in field.painted, c in exp
            ch = "#" if (p and e) else "x" if p else "*" if e else "."
            if c == rpos:
                ch = "R"
            s += ch
            s += "|" if (x == field.w or field.blocked(c, "R")) else " "
        out.append(s)
    print("\n".join(out))


def compare(field, expected=None, quiet=False):
    """Сравнивает закрашенные клетки с ожидаемыми. True, если совпало ровно."""
    exp = field.marked if expected is None else set(expected)
    miss = exp - field.painted
    extra = field.painted - exp
    ok = not miss and not extra
    if not quiet:
        if ok:
            print(f"OK: закрашено ровно {len(exp)} нужных клеток")
        else:
            print(f"ОШИБКА: не закрашены {sorted(miss)}; лишние {sorted(extra)}")
    return ok


if __name__ == "__main__":
    f = from_ascii("""
        +-+-+-+-+
        |R * * .|
        + +-+-+ +
        |. . .|.|
        +-+-+-+-+
    """)
    r = Robot(f)
    r.вправо(); r.закрасить(); r.вправо(); r.закрасить()
    show(f, r)
    compare(f)
    print("снизу стена:", r.снизу_стена(), "| справа свободно:", r.справа_свободно())
    try:
        r.вниз()
    except Отказ as e:
        print(e)
