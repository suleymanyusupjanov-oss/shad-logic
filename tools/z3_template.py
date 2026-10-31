"""z3 — решатель ограничений. Хорош для расстановок, расписаний, целочисленных
уравнений, «кто где живёт», когда полный перебор слишком большой.
Установка: pip install z3-solver   (если не ставится — используй brute.py)

Главное: all_solutions() считает ВСЕ решения. Одно — задача решена однозначно.
"""
import sys
try:  # Windows: не падать на символах, которых нет в кодировке консоли
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

from z3 import Int, Bool, Solver, Distinct, And, Or, Not, Implies, If, Sum, sat


def all_solutions(solver, variables, limit=50):
    """Перебирает решения, каждый раз запрещая уже найденное."""
    sols = []
    while solver.check() == sat and len(sols) < limit:
        m = solver.model()
        sol = {str(v): m.eval(v, model_completion=True) for v in variables}
        sols.append(sol)
        solver.add(Or([v != m.eval(v, model_completion=True) for v in variables]))
    print(f"Решений: {len(sols)}{' (дошли до лимита)' if len(sols) == limit else ''}")
    for s in sols[:20]:
        print("  ", s)
    return sols


if __name__ == "__main__":
    # Пример: 4 студента сдавали экзамен по очереди (места 1..4).
    # Аня сдавала раньше Бори; Витя не первый и не последний; Галя сразу после Вити.
    names = ["Аня", "Боря", "Витя", "Галя"]
    pos = {n: Int(n) for n in names}
    s = Solver()
    s.add([And(p >= 1, p <= 4) for p in pos.values()])
    s.add(Distinct(*pos.values()))
    s.add(pos["Аня"] < pos["Боря"])
    s.add(pos["Витя"] != 1, pos["Витя"] != 4)
    s.add(pos["Галя"] == pos["Витя"] + 1)
    all_solutions(s, list(pos.values()))
