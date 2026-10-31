"""Точная вероятность перечислением исходов (ответ дробью, без погрешности).

Работает, когда можно выписать все РАВНОВЕРОЯТНЫЕ исходы (кубики, монеты,
карты, выбор шаров, перестановки). Для неравновероятных — передай веса.

    from exact import prob, expect, space
    S = space(range(1, 7), repeat=2)                 # два кубика: 36 пар
    prob(S, lambda w: sum(w) == 7)                   # 1/6
    prob(S, lambda w: sum(w) == 7, given=lambda w: 6 in w)   # условная: 2/11
    expect(S, lambda w: max(w))                      # матожидание максимума
"""
import sys
try:  # Windows: всегда печатать в UTF-8, чтобы кириллица не превращалась в «?»
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from fractions import Fraction
from itertools import product, permutations, combinations


def space(values, repeat=1):
    """Все упорядоченные исходы (с возвращением / независимые повторы)."""
    return list(product(values, repeat=repeat))


def draws(items, k, ordered=False):
    """Выбор k штук БЕЗ возвращения. items — список с повторами, если предметы одинаковые
    по виду (например ["Б","Б","Б","Ч","Ч"]): каждый предмет считается отдельным,
    поэтому исходы равновероятны."""
    idx = range(len(items))
    gen = permutations(idx, k) if ordered else combinations(idx, k)
    return [tuple(items[i] for i in c) for c in gen]


def prob(outcomes, event, given=None, weights=None, show=True):
    """P(event | given). outcomes — список исходов; weights — их вероятности (если не равны)."""
    if weights is None:
        weights = [Fraction(1)] * len(outcomes)
    else:
        weights = [Fraction(w) for w in weights]
    cond = [(w, p) for w, p in zip(outcomes, weights) if given is None or given(w)]
    den = sum(p for _, p in cond)
    num = sum(p for w, p in cond if event(w))
    if den == 0:
        raise ValueError("условие given не выполняется ни в одном исходе")
    r = num / den
    if show:
        print(f"P = {r}  ~ {float(r):.6f}   (исходов в условии: {len(cond)})")
    return r


def expect(outcomes, f, weights=None, show=True):
    """Матожидание E[f(исход)] точно, дробью."""
    if weights is None:
        weights = [Fraction(1, len(outcomes))] * len(outcomes)
    else:
        weights = [Fraction(w) for w in weights]
    r = sum(Fraction(f(w)) * p for w, p in zip(outcomes, weights)) / sum(weights)
    if show:
        print(f"E = {r}  ~ {float(r):.6f}")
    return r


if __name__ == "__main__":
    S = space(range(1, 7), repeat=2)
    prob(S, lambda w: sum(w) == 7)                                  # 1/6
    prob(S, lambda w: sum(w) == 7, given=lambda w: 6 in w)          # 2/11
    expect(S, lambda w: max(w))                                     # 161/36
    urn = ["Б"] * 3 + ["Ч"] * 2
    prob(draws(urn, 2), lambda w: w.count("Б") == 1)                # 3/5
