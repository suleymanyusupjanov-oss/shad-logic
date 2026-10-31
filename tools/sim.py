"""Симуляция Монте-Карло: прогоняем опыт много раз и усредняем (ЗБЧ).
95%-интервал по ЦПТ: среднее ± 1,96·σ/√n.

Это ПРОВЕРКА ответа, а не точный ответ: если точное значение (из exact.py или
рассуждения) не попадает в интервал — где-то ошибка.

    from sim import mc
    import random
    def trial(rng):              # один опыт; вернуть число (1/0 для события)
        return int(rng.randint(1, 6) + rng.randint(1, 6) == 7)
    mc(trial)                    # ≈ 0.1667 ± 0.0016
"""
import math
import random


def mc(trial, n=200_000, seed=12345, show=True):
    rng = random.Random(seed)
    s = s2 = 0.0
    for _ in range(n):
        x = float(trial(rng))
        s += x
        s2 += x * x
    mean = s / n
    var = max(s2 / n - mean * mean, 0.0)
    half = 1.96 * math.sqrt(var / n)
    if show:
        print(f"Среднее = {mean:.5f}, 95%-интервал [{mean - half:.5f}; {mean + half:.5f}]  (n = {n})")
    return mean, (mean - half, mean + half)


def check(exact_value, interval):
    lo, hi = interval
    ok = lo <= float(exact_value) <= hi
    print(f"Точное {float(exact_value):.5f} {'ВНУТРИ' if ok else 'ВНЕ'} интервала симуляции")
    return ok


if __name__ == "__main__":
    # Монти Холл: 3 двери, приз за одной; ведущий открывает пустую, НЕ выбранную игроком.
    def switch_wins(rng):
        prize, pick = rng.randrange(3), rng.randrange(3)
        opened = rng.choice([d for d in range(3) if d != pick and d != prize])
        new = next(d for d in range(3) if d != pick and d != opened)
        return int(new == prize)
    m, ci = mc(switch_wins)
    check(2 / 3, ci)
