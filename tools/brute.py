"""Полный перебор: задаём переменные и их возможные значения, условия — функции.
Печатает, сколько вариантов проходят ВСЕ условия, и сами варианты.

У корректной логической задачи решение ровно одно.
0 решений  -> условие формализовано неверно (лишнее/неверное ограничение).
>1 решения -> чего-то не хватает или ответ не зависит от выбора (проверь, что спрашивают).

Использование (из tasks/N/check.py):
    import sys; sys.path.insert(0, "tools")   # если запускаешь из корня репозитория
    from brute import solve, assign
"""
import sys
try:  # Windows: не падать на символах, которых нет в кодировке консоли
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

from itertools import product, permutations


def solve(variables, constraints, show=20, quiet=False):
    """variables: {"A": [True, False], "B": range(1, 7), ...}
    constraints: [lambda v: ..., ...]  где v — словарь {имя: значение}
    Возвращает список всех решений (словарей)."""
    names = list(variables)
    sols = []
    for values in product(*(list(variables[n]) for n in names)):
        v = dict(zip(names, values))
        if all(c(v) for c in constraints):
            sols.append(v)
    if not quiet:
        _report(sols, show)
    return sols


def assign(people, items, constraints, show=20, quiet=False):
    """Каждому из people — РАЗНЫЙ элемент из items (расстановки, места, порядок).
    v[person] = item. Для «кто на каком месте» items = range(1, n+1)."""
    sols = []
    for perm in permutations(items, len(people)):
        v = dict(zip(people, perm))
        if all(c(v) for c in constraints):
            sols.append(v)
    if not quiet:
        _report(sols, show)
    return sols


def _report(sols, show):
    print(f"Решений, удовлетворяющих всем условиям: {len(sols)}")
    for s in sols[:show]:
        print("  ", s)
    if len(sols) > show:
        print(f"   ... и ещё {len(sols) - show}")
    if len(sols) == 0:
        print("!! 0 решений: проверь формализацию условий")
    elif len(sols) > 1:
        print("!! решений больше одного: проверь, не потеряно ли условие, и совпадает ли ответ во всех")


def common(sols, key):
    """Одинаково ли значение key во всех решениях (тогда ответ определён однозначно)."""
    vals = {repr(s[key]) for s in sols}
    print(f"{key}: варианты во всех решениях -> {sorted(vals)}")
    return vals


if __name__ == "__main__":
    # Пример: рыцари (True, всегда правда) и лжецы (False, всегда лгут).
    # A: «B — лжец».  B: «A и C одного типа».  C: «A — рыцарь».
    # Высказывание рыцаря истинно, лжеца — ложно  =>  (говорящий == истинность фразы)
    sols = solve(
        {"A": [True, False], "B": [True, False], "C": [True, False]},
        [
            lambda v: v["A"] == (not v["B"]),
            lambda v: v["B"] == (v["A"] == v["C"]),
            lambda v: v["C"] == v["A"],
        ],
    )
    # Пример расстановки: 3 человека на местах 1..3, Аня не первая, Боря перед Витей
    assign(["Аня", "Боря", "Витя"], range(1, 4),
           [lambda v: v["Аня"] != 1, lambda v: v["Боря"] < v["Витя"]])
