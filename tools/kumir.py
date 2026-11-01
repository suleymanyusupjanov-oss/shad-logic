"""Мини-интерпретатор КуМира (подмножество, достаточное для задач на Робота).

Запускает ТОТ САМЫЙ текст программы на КуМире на поле из robot.py — так можно
проверить алгоритм на примере с картинки и на сотнях случайных полей.

    import sys; sys.path.insert(0, "tools")
    from robot import from_ascii, Robot, compare, show
    from kumir import run
    f = from_ascii(ASCII_ПОЛЕ)
    robot, out = run(KUMIR_КОД, f)      # исключение Отказ / KumirError, если что-то не так
    compare(f)                          # закрашено ли ровно то, что отмечено

Поддерживается:
  использовать Робот; алг [имя] / нач / кон (несколько алгоритмов без параметров,
  первый — главный; имена с пробелами можно); цел/вещ/лог/сим/лит (+ := при объявлении);
  целтаб/вещтаб/логтаб a[1:n]; присваивание :=; вывод ..., нс; утв;
  нц пока <усл> … кц;  нц <n> раз … кц;  нц для i от a до b [шаг s] … кц;  нц … кц при <усл>;
  если <усл> [то] … [иначе …] все  (в одну строку или по строкам, «то» можно с новой строки);
  выход (из цикла, вне цикла — из алгоритма); стоп;
  команды Робота: вверх, вниз, влево, вправо, закрасить;
  условия: сверху/снизу/слева/справа свободно|стена, клетка закрашена|чистая;
  значения: радиация, температура; и, или, не, да, нет, =, <>, <, >, <=, >=, div, mod, abs, int.
НЕ поддерживается: алгоритмы с параметрами, выбор/при, ввод. Если встретится — KumirError.
Как на платформе теста: «дано»/«надо» запрещены, «нач» — сразу после строки «алг».
Пиши по одной команде в строке (или через «;») — так надёжнее и для КуМира, и для этой проверки.
"""
import re
import sys
from collections import defaultdict

try:  # Windows: всегда печатать в UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from robot import Robot, Отказ  # noqa: E402


class KumirError(Exception):
    pass


_ROBOT_COND = [
    (r"(сверху|снизу|слева|справа)\s+(свободно|стена)", lambda m: f"R.{m.group(1)}_{m.group(2)}()"),
    (r"клетка\s+(закрашена|чистая)", lambda m: f"R.клетка_{m.group(1)}()"),
    (r"радиация", lambda m: "R.радиация()"),
    (r"температура", lambda m: "R.температура()"),
]
_CMDS = {"вверх", "вниз", "влево", "вправо", "закрасить"}
_W = r"(?<![\w])"   # начало слова
_E = r"(?![\w])"    # конец слова


def _protect_strings(s):
    strs = []

    def rep(m):
        strs.append(m.group(0))
        return f"\x00{len(strs) - 1}\x00"
    return re.sub(r'"[^"]*"|\'[^\']*\'', rep, s), strs


def _restore(s, strs):
    return re.sub(r"\x00(\d+)\x00", lambda m: strs[int(m.group(1))], s)


def _expr(s, algs):
    s, strs = _protect_strings(s)
    for pat, rep in _ROBOT_COND:
        s = re.sub(_W + pat + _E, rep, s)
    s = re.sub(_W + r"и" + _E, " and ", s)
    s = re.sub(_W + r"или" + _E, " or ", s)
    s = re.sub(_W + r"не" + _E, " not ", s)
    s = re.sub(_W + r"да" + _E, "True", s)
    s = re.sub(_W + r"нет" + _E, "False", s)
    s = re.sub(_W + r"нс" + _E, lambda m: '"\\n"', s)
    s = s.replace("<>", "!=")
    s = re.sub(r"(?<![<>:=!])=(?!=)", "==", s)
    s = re.sub(_W + r"div" + _E, "_div", s)
    s = re.sub(_W + r"mod" + _E, "_mod", s)
    s = re.sub(_W + r"iabs" + _E, "abs", s)
    return _restore(s, strs).strip()


def _split_statements(code):
    """Комментарии «|» убираем, «;» и составные строки разбиваем на отдельные операторы."""
    out = []  # (номер строки КуМира, оператор)
    for ln, raw in enumerate(code.splitlines(), 1):
        s, strs = _protect_strings(raw)
        s = s.split("|", 1)[0]
        parts = []
        for piece in s.split(";"):
            # если ... то <оператор>  /  ... иначе ...  /  ... все  /  ... кц
            piece = re.sub(_W + r"то" + _E, "то\n", piece)
            piece = re.sub(_W + r"иначе" + _E, "\nиначе\n", piece)
            piece = re.sub(_W + r"(все)" + _E, r"\n\1", piece)
            piece = re.sub(_W + r"(кц_при|кц)" + _E, r"\n\1", piece)
            parts += piece.split("\n")
        for p in parts:
            p = _restore(p, strs).strip()
            if p:
                out.append((ln, p))
    return out


def translate(code):
    stmts = _split_statements(code)
    # имена алгоритмов
    algs = []
    for ln, st in stmts:
        if st == "алг" or st.startswith("алг "):
            name = st[3:].strip()
            if "(" in name:
                raise KumirError(f"строка {ln}: алгоритмы с параметрами не поддерживаются")
            algs.append(name)
    if not algs:
        raise KumirError("нет ни одного «алг»")
    pyname = {a: "алг_" + (re.sub(r"\W+", "_", a) if a else "главный") for a in algs}
    named = sorted([a for a in algs if a], key=len, reverse=True)

    py, lmap = [], []
    ind = 0
    stack = []          # типы открытых блоков: alg, while, for, post, if, else
    pending_if = False  # «если усл» без «то» — следующий «то» пропустить

    def emit(line, ln):
        py.append("    " * ind + line)
        lmap.append(ln)

    def loops_open():
        return any(b in ("while", "for", "post") for b in stack)

    expect_nach = False
    for ln, st in stmts:
        w = st.split()
        head = w[0]
        if st.startswith("использовать"):
            continue
        if head in ("дано", "надо"):
            raise KumirError(f"строка {ln}: «{head}» — КуМир на платформе теста это не принимает "
                             f"(«ожидалось 'нач' после заголовка функции»). Удали строку, условие пиши комментарием «|».")
        if expect_nach and head != "нач":
            raise KumirError(f"строка {ln}: после «алг» сразу должно идти «нач» (так требует КуМир на платформе)")
        expect_nach = False
        if head == "алг":
            name = st[3:].strip()
            emit(f"def {pyname[name]}():", ln)
            ind += 1
            emit("pass", ln)
            stack.append("alg")
            expect_nach = True
            continue
        if head == "нач":
            continue
        if head == "кон":
            while stack and stack[-1] != "alg":
                raise KumirError(f"строка {ln}: «кон», но не закрыт блок «{stack[-1]}»")
            stack.pop()
            ind -= 1
            continue
        if head == "то":
            if not pending_if:
                raise KumirError(f"строка {ln}: «то» без «если»")
            pending_if = False
            continue
        if head == "если":
            cond = st[4:].strip()
            has_to = bool(re.search(_W + r"то" + _E, cond))
            cond = re.sub(_W + r"то" + _E, "", cond).strip()
            emit(f"if {_expr(cond, algs)}:", ln)
            ind += 1
            emit("pass", ln)
            stack.append("if")
            pending_if = not has_to
            continue
        if head == "иначе":
            if not stack or stack[-1] != "if":
                raise KumirError(f"строка {ln}: «иначе» без «если»")
            stack[-1] = "else"
            ind -= 1
            emit("else:", ln)
            ind += 1
            emit("pass", ln)
            continue
        if head == "все":
            if not stack or stack[-1] not in ("if", "else"):
                raise KumirError(f"строка {ln}: «все» без «если»")
            stack.pop()
            ind -= 1
            continue
        if head == "нц":
            rest = st[2:].strip()
            if rest.startswith("пока"):
                emit(f"while {_expr(rest[4:], algs)}:", ln)
                stack.append("while")
            elif re.match(r"для\s", rest):
                m = re.match(r"для\s+(\w+)\s+от\s+(.+?)\s+до\s+(.+?)(?:\s+шаг\s+(.+))?$", rest)
                if not m:
                    raise KumirError(f"строка {ln}: не понял «нц для»: {st}")
                v, a, b, s = m.groups()
                s = s or "1"
                emit(f"for {v} in _range({_expr(a, algs)}, {_expr(b, algs)}, {_expr(s, algs)}):", ln)
                stack.append("for")
            elif re.search(_W + r"раз" + _E, rest):
                n = re.sub(_W + r"раз" + _E, "", rest)
                emit(f"for _ in range(int({_expr(n, algs)})):", ln)
                stack.append("for")
            elif rest == "":
                emit("while True:", ln)
                stack.append("post")
            else:
                raise KumirError(f"строка {ln}: не понял начало цикла: {st}")
            ind += 1
            emit("_tick()", ln)
            continue
        if head in ("кц", "кц_при"):
            if not stack or stack[-1] not in ("while", "for", "post"):
                raise KumirError(f"строка {ln}: «кц» без «нц»")
            kind = stack.pop()
            m = re.match(r"(кц\s+при|кц_при)\s+(.+)$", st)
            if m:
                if kind != "post":
                    raise KumirError(f"строка {ln}: «кц при» только для цикла «нц … кц при»")
                emit(f"if {_expr(m.group(2), algs)}: break", ln)
            elif kind == "post":
                raise KumirError(f"строка {ln}: у «нц» без условия должно быть «кц при <условие>»")
            ind -= 1
            continue
        if head in ("цел", "вещ", "лог", "сим", "лит"):
            default = {"цел": "0", "вещ": "0.0", "лог": "False", "сим": '""', "лит": '""'}[head]
            for part in [p.strip() for p in st[len(head):].split(",") if p.strip()]:
                m = re.match(r"(\w+)\s*(?::=|=)\s*(.+)$", part)
                if m:
                    emit(f"{m.group(1)} = {_expr(m.group(2), algs)}", ln)
                else:
                    emit(f"{part} = {default}", ln)
            continue
        if head in ("целтаб", "вещтаб", "логтаб", "симтаб", "литтаб"):
            for part in re.findall(r"(\w+)\s*\[", st[len(head):]):
                emit(f"{part} = defaultdict(int)", ln)
            continue
        if head == "вывод":
            emit(f"_out({_expr(st[5:], algs)})", ln)
            continue
        if head == "утв":
            emit(f"assert {_expr(st[3:], algs)}, 'утв не выполнено (строка {ln})'", ln)
            continue
        if head == "выход":
            emit("break" if loops_open() and stack[-1] != "alg" else "return", ln)
            continue
        if head == "стоп":
            emit("raise _Stop()", ln)
            continue
        if head in ("выбор", "при", "ввод"):
            raise KumirError(f"строка {ln}: «{head}» не поддерживается — перепиши через если")
        if st in _CMDS:
            emit(f"R.{st}()", ln)
            continue
        if st in named:
            emit(f"{pyname[st]}()", ln)
            continue
        if ":=" in st:
            left, right = st.split(":=", 1)
            emit(f"{left.strip()} = {_expr(right, algs)}", ln)
            continue
        raise KumirError(f"строка {ln}: непонятная команда «{st}»")

    if stack:
        raise KumirError(f"не закрыт блок «{stack[-1]}» (нет кон/все/кц)")
    main = pyname[algs[0]]
    return "\n".join(py) + f"\n{main}()\n", lmap


class _Stop(Exception):
    pass


def run(code, field, x=None, y=None, max_loop=1_000_000, verbose=False):
    """Выполнить программу на КуМире на поле field. Возвращает (robot, вывод)."""
    src, lmap = translate(code)
    if verbose:
        print(src)
    robot = Robot(field, x, y)
    out = []
    ticks = [0]

    def _tick():
        ticks[0] += 1
        if ticks[0] > max_loop:
            raise Отказ(f"больше {max_loop} проходов циклов — похоже на бесконечный цикл")

    def _out(*a):
        out.append("".join(str(v) for v in a))

    def _range(a, b, s):
        return range(a, b + 1, s) if s > 0 else range(a, b - 1, s)

    env = {"R": robot, "_tick": _tick, "_out": _out, "_range": _range, "_Stop": _Stop,
           "defaultdict": defaultdict, "_div": lambda a, b: a // b, "_mod": lambda a, b: a % b,
           "abs": abs, "int": int}
    try:
        exec(compile(src, "<kumir>", "exec"), env)
    except _Stop:
        pass
    except (Отказ, KumirError):
        raise
    except Exception as e:  # ошибка выполнения — показать строку КуМира
        tb = e.__traceback__
        kl = None
        while tb:
            if tb.tb_frame.f_code.co_filename == "<kumir>":
                pl = tb.tb_lineno
                if 1 <= pl <= len(lmap):
                    kl = lmap[pl - 1]
            tb = tb.tb_next
        raise KumirError(f"ошибка выполнения{f' в строке {kl}' if kl else ''}: {type(e).__name__}: {e}")
    return robot, "".join(out)


if __name__ == "__main__":
    from robot import from_ascii, show, compare
    code = """
использовать Робот
алг
нач
  | закрасить всю верхнюю строку, потом вернуться
  закрасить
  нц пока справа свободно
    вправо; закрасить
  кц
  нц пока слева свободно
    влево
  кц
кон
"""
    f = from_ascii("""
        +-+-+-+-+
        |@ * * *|
        +-+ + +-+
        |. . . .|
        +-+-+-+-+
    """)
    r, _ = run(code, f)
    show(f, r)
    compare(f)
