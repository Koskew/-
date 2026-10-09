# -*- coding: utf-8 -*-
"""Что на самом деле означает «вне справ.».

Утверждение, которое надо проверить: справочник из восьми форм покрывает
ВСЕ счёта без манипуляции, поэтому «вне справ.» — это ровно и только
«внутри был манипуляционный низ», тождество, а не корреляция."""
import sys, os, itertools
sys.path.insert(0, 'research')
from dvizhok2 import run_all
from core import load

PAT = ["LH·HL·HH·HL·HH","LH·HL·HH·HL·LH","HH·HL·HH·HL·HH","HH·HL·HH·HL·LH",
       "HH·HL·LH·HL·HH","LH·HL·LH·HL·HH","HH·HL·LH·HL·LH","LH·HL·LH·HL·LH"]
PATS = set(PAT)

# 1. АРИФМЕТИКА. Сколько вообще бывает хвостов из пяти колен,
#    если низы всегда HL
tops = ['HH','LH']
full = set('·'.join([a,'HL',b,'HL',c]) for a in tops for b in tops for c in tops)
print('хвостов без манипуляции возможно :', len(full))
print('эталонов в справочнике           :', len(PATS))
print('покрыты справочником             :', len(full & PATS), '→',
      'ВСЕ' if full <= PATS else 'НЕ ВСЕ, не хватает: %s' % (full - PATS))
print()

# 2. ДАННЫЕ. Для каждого счёта, дошедшего до (5), собрать хвост
#    и проверить: «не совпал с эталоном» == «был низ LL»
for path, title in (('data/XAUUSD_1h_2y.csv','ЧАСОВИК 2 года'),
                    ('data/XAUUSD_1h_9y.csv','ЧАСОВИК 9 лет'),
                    ('data/XAUUSD_5m.csv','ПЯТИМИНУТКА')):
    if not os.path.exists(path):
        continue
    rows = load(path)
    for flip, nm in ((False,'ВОСХОДЯЩИЙ'), (True,'НИСХОДЯЩИЙ')):
        res = run_all(rows, flip=flip)
        tot = bad = manip = both = neither = only_out = only_man = 0
        for li in range(3):
            C = res['C'][li]; T = res['T'][li]
            for ct in T.counts:
                if ct['mx'] < 5 or ct['born'] is None:
                    continue
                # хвост: пять колен после нуля
                zb = ct.get('zb')
                if zb is None:
                    continue
                zi = None
                for k in range(len(C.B)):
                    if C.B[k] >= zb and not C.H[k]:
                        zi = k; break
                if zi is None or zi + 5 >= len(C.L):
                    continue
                tail = C.L[zi+1:zi+6]
                if len(tail) < 5:
                    continue
                out = '·'.join(tail) not in PATS
                man = any(x == 'LL' for x in tail)
                tot += 1
                if out and man: both += 1
                elif out and not man: only_out += 1
                elif man and not out: only_man += 1
                else: neither += 1
        if tot:
            print('%-16s %-11s счётов до (5): %5d | вне справ. И манипуляция: %5d | вне справ. БЕЗ манипуляции: %3d | манипуляция, но в справ.: %3d | чисто: %5d'
                  % (title, nm, tot, both, only_out, only_man, neither))
