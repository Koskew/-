# -*- coding: utf-8 -*-
"""СЛЕПОК ЭТАЛОНА — страховка для реплики.

Зачем. С 10.10.2026 рабочий пайн — `indicator/metki_2x2.pine`, один слой
2/2, а реплика `dvizhok2.py` повторяет трёхслойный эталон. Сегодня они
совпадают: слой 2/2 в реплике считается без донора, и движок в пайн
скопирован дословно. Но правила будут меняться, и каждое новое правило
войдёт в реплику РУЧКОЙ, у которой значение по умолчанию обязано в
точности воспроизводить эталон.

Самопроверка `dvizhok2.py` ловит зеркало и инварианты, но НЕ ловит, что
поведение ПО УМОЛЧАНИЮ сдвинулось. Этот скрипт ловит.

    python3 research/slepok.py --snap     снять слепок (один раз)
    python3 research/slepok.py            сверить с ним. Код 1 при расхождении

Что в слепке: для каждого набора данных × направления × слоя —
отпечаток ВСЕЙ цепочки колен (бары, цены, стороны, подписи), число
колен, вставок, счётов, дошедших до (5) и каждого из концов, плюс
скользящее среднее колено. Сдвинь любое правило — отпечаток изменится.
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collections
import dvizhok2 as D
from core import load

SLEPOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'slepok.json')
NABOR = (('data/XAUUSD_1h_2y.csv', 'часовик 2 года'),
         ('data/XAUUSD_1h_9y.csv', 'часовик 9 лет'),
         ('data/XAUUSD_5m.csv',    'пятиминутка'))
SLOI = ('5/5', '3/3', '2/2')


def otpechatok(C):
    """Отпечаток цепочки: бары, цены, стороны, подписи. Цена округляется
    до шестого знака — иначе отпечаток ловил бы шум float, а не правило."""
    h = hashlib.md5()
    for k in range(len(C.P)):
        h.update(('%d|%.6f|%d|%s;' % (C.B[k], C.P[k], 1 if C.H[k] else 0, C.L[k])).encode())
    return h.hexdigest()[:16]


def snyat():
    out = {}
    for path, nm in NABOR:
        if not os.path.exists(path):
            print('нет файла, пропущен:', path)
            continue
        rows = load(path)
        for flip, dnm in ((False, 'восходящий'), (True, 'нисходящий')):
            # ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ И НИКАКИХ ДРУГИХ: слепок про эталон
            res = D.run_all(rows, flip=flip)
            for li in range(3):
                C, T = res['C'][li], res['T'][li]
                cn = collections.Counter(ct['how'] for ct in T.counts)
                out['%s|%s|%s' % (nm, dnm, SLOI[li])] = {
                    'отпечаток': otpechatok(C),
                    'колен':     len(C.P),
                    'вставок':   res['ins'][li],
                    'счётов':    len(T.counts),
                    'до5':       sum(1 for ct in T.counts if ct['mx'] >= 5),
                    'умер':      cn['умер'],
                    'архив':     cn['архив'],
                    'не было':   cn['не было'],
                    'не свой':   cn['не свой'],
                    'колено':    round(res['K'][li].avg_leg(), 6),
                }
    return out


def main():
    now = snyat()
    if '--snap' in sys.argv:
        os.makedirs(os.path.dirname(SLEPOK), exist_ok=True)
        with open(SLEPOK, 'w', encoding='utf-8') as f:
            json.dump(now, f, ensure_ascii=False, indent=1, sort_keys=True)
        print('СЛЕПОК СНЯТ: %d клеток → %s' % (len(now), SLEPOK))
        for k in sorted(now):
            v = now[k]
            print('  %-34s %s  колен %6d  счётов %5d  до(5) %5d' %
                  (k, v['отпечаток'], v['колен'], v['счётов'], v['до5']))
        return 0

    if not os.path.exists(SLEPOK):
        print('СЛЕПКА НЕТ. Снять: python3 research/slepok.py --snap')
        return 1
    with open(SLEPOK, encoding='utf-8') as f:
        bylo = json.load(f)

    plohо = []
    for k in sorted(set(bylo) | set(now)):
        if k not in bylo:
            plohо.append((k, 'ПОЯВИЛАСЬ клетка', '', ''))
            continue
        if k not in now:
            plohо.append((k, 'ПРОПАЛА клетка', '', ''))
            continue
        for pole in sorted(bylo[k]):
            a, b = bylo[k][pole], now[k].get(pole)
            if a != b:
                plohо.append((k, pole, a, b))
    if not plohо:
        print('СЛЕПОК СОШЁЛСЯ: %d клеток, поведение по умолчанию не менялось' % len(now))
        return 0
    print('!! РАСХОЖДЕНИЙ: %d' % len(plohо))
    for k, pole, a, b in plohо:
        print('   %-34s %-12s было %s · стало %s' % (k, pole, a, b))
    print('\nЗначения ПО УМОЛЧАНИЮ обязаны воспроизводить эталон.')
    print('Разошлись — значит правка реплики сломала эталон, а не добавила правило.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
