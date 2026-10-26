# -*- coding: utf-8 -*-
"""ОБЁРТКА ЦЕПОЧКИ — честный признак. Приборы, а не правила.

ПОВОД — запись Н49. Хвост счёта читается из ГОТОВОЙ цепочки колен, а
колено имеет право переехать (Н40) и записано своей ОКОНЧАТЕЛЬНОЙ
ценой, подписью и баром подтверждения. У счёта, умершего рано, часть
хвоста дописана ПОСЛЕ его смерти.

ЧТО ЗАПИСЫВАЕТСЯ при появлении КАЖДОГО нового колена:
  FP   — цена при первом подтверждении;
  FL   — подпись при первом подтверждении, против предыдущего колена
         той же стороны, КАКИМ ОНО БЫЛО В ТОТ МОМЕНТ;
  FC   — бар первого подтверждения;
  HIST — [(бар, цена)] на каждом переезде, начиная с первого.

ДВИЖОК НЕ ТРОГАЕТСЯ: _orig вызывается как есть, все поля движок не
читает. Проверяется функцией sverit() — прогон с обёрткой и без обязаны
дать тождественные цепочки, подписи и историю счётов.

ПОЧЕМУ ОТДЕЛЬНЫМ ФАЙЛОМ. У `v28_chestno.py` и `n47_chestno.py` лежит
своя копия той же обёртки — их числа записаны против их же кода, и
править их нельзя по тому же правилу, по какому не правится старая
реплика. Новые замеры берут обёртку отсюда.
"""
import dvizhok2 as D

_orig = D.Chain.push


def _push(self, price, bar, isHi, conf):
    if not hasattr(self, 'FP'):
        self.FP, self.FL, self.FC, self.HIST = [], [], [], []
    same = bool(self.P) and self.H[-1] == isHi
    before = self.P[-1] if self.P else None
    prev = None
    if not same:
        for j in range(len(self.P) - 1, -1, -1):
            if self.H[j] == isHi:
                prev = self.P[j]
                break
    r = _orig(self, price, bar, isHi, conf)
    if r:
        self.FP.append(price)
        self.FL.append(D.lab(isHi, price, prev))
        self.FC.append(conf)
        self.HIST.append([(conf, price)])
    elif same and self.P and self.P[-1] != before:
        if self.HIST:
            self.HIST[-1].append((conf, self.P[-1]))
    return r


def patch(on=True):
    D.Chain.push = _push if on else _orig


def cena(hist, i):
    """Цена колена, какой она была НА БАР i. None — колена ещё нет."""
    p = None
    for cb, pr in hist:
        if cb <= i:
            p = pr
        else:
            break
    return p


def sverit(rows, **kw):
    """Прогон с обёрткой и без. Печатает итог, возвращает (ok, res)."""
    patch(False)
    a = D.run_all(rows, **kw)
    patch(True)
    b = D.run_all(rows, **kw)
    ok = True
    for li in range(3):
        for fld in ('P', 'B', 'H', 'C', 'L'):
            if getattr(a['C'][li], fld) != getattr(b['C'][li], fld):
                print('  РАСХОЖДЕНИЕ: слой %d, поле %s' % (li, fld)); ok = False
        if len(b['C'][li].HIST) != len(b['C'][li].P):
            print('  РАСХОЖДЕНИЕ: слой %d, длина истории' % li); ok = False
        if a['T'][li].counts != b['T'][li].counts:
            print('  РАСХОЖДЕНИЕ: слой %d, история счётов' % li); ok = False
    if ok:
        print('  цепочки, подписи и история счётов ТОЖДЕСТВЕННЫ на всех трёх слоях')
    return ok, b
