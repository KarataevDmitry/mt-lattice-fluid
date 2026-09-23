#!/usr/bin/env python3
from pathlib import Path

BOOK = Path(r"D:/Experiments/PersonalCursorFolder/open/mt-lattice-fluid/book/chapters")

FIXES = {
    "causally": "причинно",
    "ad hoc": "произвольно",
    "leapfrog": "«лягушка''",
    "энtropия": "энтропия",
    "энtropии": "энтропии",
    "Изotropия": "Изотropия",
    "изotropia": "изотropia",
    "симmetрии": "симmetрии",
    "симmetрия": "симmetрия",
    "симmetрий": "симmetрий",
    "эпistemology": "отношение наблюдателя",
    "косmологического": "косmологического",
    "косmологической": "косmологической",
    "M→T": r"$M\to T$",
    "M-тик": r"такт~$M$",
    "readout": "осреднение",
    "macro-": "макро-",
    "micro-": "микро-",
    "Macro-": "Макро-",
    "Micro-": "Микро-",
    "product локальных unitary-операторов": "произведение локальных унитарных операторов",
    "product unitaries": "произведение унитарных операторов",
    "SU(2)-gate": "SU(2)-вращатель",
    "фазовый gate": "фазовый вращатель",
    "Saturating gate": "Насыщающий вращатель",
    "fitted knobs": "подгоняемых параметров",
    "coupling'и": "константы связи",
    "soliton": "солитон",
    "postulate": "постулат",
    "RNG": "генератор случайных чисел",
    "global fixed points": "глобальные неподвижные точки",
    "binomial-усреднение": "биномиальное осреднение",
    "macro-readout": "макроосреднение",
    "Macro-readout": "Макроосреднение",
    "soft-readout": "мягкое осреднение",
    "Soft readout": "Мягкое осреднение",
    "Bit budget": "Информационный бюджет",
    "Congruence ladder": "Лестница согласованности",
    "knob": "параметр",
    "knobs": "параметров",
    "check": "проверка",
    "verify": "проверка",
    "DEVLOG.md": "",
    "model/": "приложении",
    "ansatz": "допущение",
    "coarse-grain": "макроосреднение",
    "STREAM": "течение",
    "COLLISION": "столкновение",
    "spin-1/2": "спин~$1/2$",
    "Spin-1/2": "Спин~$1/2$",
    "spin-$1/2$": "спин~$1/2$",
}

# Cyrillic fixes for mixed script
CYR = [
    ("\u0418\u0437otrop\u0438\u044f", "\u0418\u0437\u043e\u0442\u0440\u043e\u043f\u0438\u044f"),  # Изotropия -> Изотropия
    ("\u0441\u0438\u043cmetri\u0438", "\u0441\u0438\u043c\u043c\u0435\u0442\u0440\u0438\u0438"),
    ("\u0441\u0438\u043cmetri\u044f", "\u0441\u0438\u043c\u043c\u0435\u0442\u0440\u0438\u044f"),
    ("\u0441\u0438\u043cmetri\u0439", "\u0441\u0438\u043c\u043c\u0435\u0442\u0440\u0438\u0439"),
    ("\u044d\u043fistemology", "\u044d\u043f\u0438\u0441\u0442\u0435\u043c\u043e\u043b\u043e\u0433\u0438\u0438"),
    ("\u043a\u043e\u0441molog\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e", "\u043a\u043e\u0441\u043c\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e"),
    ("\u043a\u043e\u0441molog\u0438\u0447\u0435\u0441\u043a\u043e\u0439", "\u043a\u043e\u0441\u043c\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u043e\u0439"),
    ("\u041a\u043b\u043ein--Gordon", "Кlein--Gordon"),
    ("\u0411loch", "Бloch"),
    ("\u0411rillouin", "Бrillouin"),
]

for path in sorted(BOOK.glob("*.tex")):
    t = path.read_text(encoding="utf-8")
    for old, new in FIXES.items():
        if old:
            t = t.replace(old, new)
    for old, new in CYR:
        t = t.replace(old, new)
    # clean double spaces from removed DEVLOG
    while "  " in t:
        t = t.replace("  ", " ")
    path.write_text(t, encoding="utf-8", newline="\n")
    print(path.name)
