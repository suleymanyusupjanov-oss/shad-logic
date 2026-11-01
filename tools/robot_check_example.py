"""ОБРАЗЕЦ проверки задачи на Робота (учебная задача, не с теста).

Условие-образец: справа от Робота вертикальная стена неизвестной длины (не меньше 1).
Робот стоит в клетке слева от верхнего конца стены. Закрасить все клетки, которые
примыкают к стене слева. Робот может закончить где угодно.

Схема проверки (так же делать в tasks/N/check.py):
1. Пример с картинки — ASCII-поле, точки = *.
2. Генератор случайных полей того же вида (меняем всё, что условие разрешает менять).
3. Эталон — какие клетки должны быть закрашены — считаем ПРЯМО ПО ОПРЕДЕЛЕНИЮ из условия,
   без Робота (иначе проверяли бы алгоритм им же самим).
4. Запускаем ТОТ ЖЕ текст на КуМире на примере и на сотнях случайных полей.
"""
import random
import sys
sys.path.insert(0, "tools")
from robot import Field, from_ascii, show, compare, Отказ   # noqa: E402
from kumir import run, KumirError                          # noqa: E402

KUMIR = """
использовать Робот
алг
нач
  нц пока справа стена
    закрасить
    вниз
  кц
кон
"""
# Ошибка-ловушка: последняя клетка цикла закрашена, но Робот делает лишний «вниз».
# Если снизу стена (стена поля), будет Отказ — случайные поля это поймают.

EXAMPLE = """
+-+-+-+-+
|. . . .|
+ + + + +
|. @|. .|
+ + + + +
|. *|. .|
+ + + + +
|. . . .|
+-+-+-+-+
"""


def expected(f, col, y1, y2):
    """Эталон по определению: клетки слева от стены (x = col, строки y1..y2)."""
    return {(col, y) for y in range(y1, y2 + 1)}


def random_case(rng):
    w, h = rng.randint(3, 12), rng.randint(2, 12)
    col = rng.randint(1, w - 1)
    y1 = rng.randint(1, h)
    y2 = rng.randint(y1, h)
    f = Field(w, h)
    f.vwall(col, y1, y2)
    f.start = (col, y1)
    return f, expected(f, col, y1, y2)


def check_one(f, exp):
    try:
        run(KUMIR, f)
    except (Отказ, KumirError) as e:
        return f"сбой: {e}"
    return None if compare(f, exp, quiet=True) else "закрашено не то"


if __name__ == "__main__":
    f = from_ascii(EXAMPLE)
    err = check_one(f, f.marked)
    print("Пример с картинки:", err or "OK")
    show(f, title="Пример после выполнения:")
    rng = random.Random(1)
    bad = 0
    for i in range(500):
        f, exp = random_case(rng)
        err = check_one(f, exp)
        if err:
            bad += 1
            if bad <= 2:
                print(f"\nСлучайное поле #{i}: {err}")
                show(f, expected=exp)
    print(f"\nСлучайных полей: 500, ошибок: {bad}")
