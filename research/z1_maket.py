# -*- coding: utf-8 -*-
"""МАКЕТ З1 — как будет выглядеть бледная метка на перепрыгнутом дне.

Заведён 29.10.2026 по его слову «покажи схематически как будет
выглядеть». Рисует SVG из НАСТОЯЩИХ свечей его случая 12 янв 2026,
два состояния друг под другом: как сейчас и как станет.

Цвета и форма метки взяты ИЗ КОДА пайна, не придуманы: цвет низа слоя
`c2L` #4fc3f7, точечная линия на 3 бара вправо, прозрачность 50 — всё
как у поглощённых меток, функция `f_drawAbs` строка 2799.

Его ответ: «да, делаем бледную метку».
"""
import os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, 'research'))
from core import load
import dvizhok2 as D

rows = load(os.path.join(root, 'data/XAUUSD_1h_2y.csv'))
H, L = D.pivots_by_bar(rows, 2)
A, B = 8284, 8302                     # окно показа
seg = list(range(A, B + 1))

C2H, C2L = '#7e57c2', '#4fc3f7'       # цвета слоя из пайна
CTR = '#00c853'
BG, FG, GRID = '#131722', '#d1d4dc', '#2a2e39'

W, PH = 1180, 258                      # ширина, высота одной панели
PADL, PADR, PADT, PADB = 64, 320, 42, 26
GAPY = 26
cw = (W - PADL - PADR) / len(seg)     # шаг бара
bw = cw * 0.56                        # ширина тела

lo = min(rows[i][3] for i in seg)
hi = max(rows[i][2] for i in seg)
m = (hi - lo) * 0.10
lo, hi = lo - m, hi + m

def X(i):
    return PADL + (i - A + 0.5) * cw

def Y(p, top):
    return top + PADT + (hi - p) / (hi - lo) * (PH - PADT - PADB)

out = []
def e(s):
    out.append(s)

def panel(top, title, novoe):
    e('<text x="%d" y="%d" class="t ttl">%s</text>' % (PADL, top + 22, title))
    # сетка
    for k in range(5):
        p = lo + (hi - lo) * k / 4
        y = Y(p, top)
        e('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" class="g"/>'
          % (PADL - 8, y, W - PADR + 6, y))
        e('<text x="%d" y="%.1f" class="t ax">%.0f</text>' % (6, y + 4, p))
    # свечи
    for i in seg:
        o, h, l, c = rows[i][1], rows[i][2], rows[i][3], rows[i][4]
        up = c >= o
        col = '#26a69a' if up else '#ef5350'
        x = X(i)
        e('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.2"/>'
          % (x, Y(h, top), x, Y(l, top), col))
        y1, y2 = Y(max(o, c), top), Y(min(o, c), top)
        e('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>'
          % (x - bw / 2, y1, bw, max(1.2, y2 - y1), col))
    # зиг-заг 2/2: вершина 8287 -> низ 8299 -> вершина 8303(вне окна)
    e('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2"/>'
      % (X(8287), Y(H[8287], top), X(8299), Y(L[8299], top), CTR))
    # метки колен
    e('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"/>' % (X(8287), Y(H[8287], top), C2H))
    e('<text x="%.1f" y="%.1f" class="t lb" fill="%s" text-anchor="middle">(5) HH %.3f</text>'
      % (X(8287), Y(H[8287], top) - 10, C2H, H[8287]))
    e('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"/>' % (X(8299), Y(L[8299], top), C2L))
    e('<text x="%.1f" y="%.1f" class="t lb" fill="%s" text-anchor="middle">HL %.3f</text>'
      % (X(8299), Y(L[8299], top) + 15, C2L, L[8299]))
    # где настоящее дно
    xd, yd = X(8289), Y(rows[8289][3], top)
    if novoe:
        # точечная линия на 3 бара вправо + бледная метка — как у поглощённых
        e('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1" '
          'stroke-dasharray="2 3" opacity="0.5"/>' % (xd, yd, X(8292), yd, C2L))
        e('<text x="%.1f" y="%.1f" class="t lb" fill="%s" opacity="0.5" '
          'text-anchor="middle">%.3f</text>' % (xd, yd + 15, C2L, rows[8289][3]))
        e('<text x="%d" y="%.1f" class="t nt" fill="%s">НОВОЕ: бледная метка на настоящем дне.</text>'
          % (W - PADR + 12, top + PADT + 54, C2L))
        e('<text x="%d" y="%.1f" class="t nt2">Точечная линия 3 бара,</text>'
          % (W - PADR + 12, top + PADT + 72))
        e('<text x="%d" y="%.1f" class="t nt2">фон прозрачный, цвет низа</text>'
          % (W - PADR + 12, top + PADT + 88))
        e('<text x="%d" y="%.1f" class="t nt2">на 50%% — как у поглощённых.</text>'
          % (W - PADR + 12, top + PADT + 104))
        e('<text x="%d" y="%.1f" class="t nt2">Зиг-заг, счёт, уровень,</text>'
          % (W - PADR + 12, top + PADT + 128))
        e('<text x="%d" y="%.1f" class="t nt2">смерть — НЕ меняются.</text>'
          % (W - PADR + 12, top + PADT + 144))
    else:
        e('<circle cx="%.1f" cy="%.1f" r="11" fill="none" stroke="#ef5350" '
          'stroke-width="1.8" stroke-dasharray="3 2"/>' % (xd, yd))
        e('<text x="%d" y="%.1f" class="t nt" fill="#ef5350">Настоящее дно коррекции</text>'
          % (W - PADR + 12, top + PADT + 54))
        e('<text x="%d" y="%.1f" class="t nt2">4561.935 — на графике</text>'
          % (W - PADR + 12, top + PADT + 72))
        e('<text x="%d" y="%.1f" class="t nt2">НИЧЕМ не отмечено.</text>'
          % (W - PADR + 12, top + PADT + 88))
        e('<text x="%d" y="%.1f" class="t nt2">Ниже колена на 16.550,</text>'
          % (W - PADR + 12, top + PADT + 112))
        e('<text x="%d" y="%.1f" class="t nt2">раньше на 10 баров.</text>'
          % (W - PADR + 12, top + PADT + 128))
    # подписи времени
    for i in (8287, 8289, 8299):
        e('<text x="%.1f" y="%d" class="t ax" text-anchor="middle">%s</text>'
          % (X(i), top + PH - 6, rows[i][0][11:16]))

HT = PH * 2 + GAPY + 44
e('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
  % (W, HT, W, HT))
e('<style>'
  '.t{font-family:-apple-system,Segoe UI,Roboto,sans-serif}'
  '.ttl{font-size:15px;font-weight:700;fill:%s}'
  '.ax{font-size:10px;fill:#787b86}'
  '.lb{font-size:11.5px;font-weight:600}'
  '.nt{font-size:12px;font-weight:700}'
  '.nt2{font-size:11.5px;fill:#9598a1}'
  '.g{stroke:%s;stroke-width:1}'
  '.cap{font-size:12.5px;fill:#9598a1}'
  '</style>' % (FG, GRID))
e('<rect width="100%%" height="100%%" fill="%s"/>' % BG)
panel(0, 'СЕЙЧАС  ·  XAUUSD 1H  ·  12 янв 2026  ·  слой 2/2', False)
panel(PH + GAPY, 'СТАНЕТ, если скажешь «делаем»', True)
e('<text x="%d" y="%d" class="t cap">Свечи настоящие, из data/XAUUSD_1h_2y.csv, бары 8284-8302. '
  'Цвета и форма метки взяты из кода: c2L #4fc3f7, точечная линия 3 бара, прозрачность 50.</text>'
  % (PADL, HT - 16))
e('</svg>')

p = os.path.join(root, 'research', 'out', 'z1-maket.svg')
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, 'w', encoding='utf-8').write('\n'.join(out))
print('готово:', p)
