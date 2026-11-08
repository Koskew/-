#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СХЕМА СВЕЧИ ДЛЯ РАЗГОВОРА О ТС2.1 — «как она выглядит».

    python3 research/shema_svechi.py > research/out/shema_svechi.svg

Заведена 08.11.2026 по его слову: «можешь ещё сделать схему свечи, 1, с
разными размерами тела, штрих-пунктиром с обозначением, чтобы я тебе
написал, как нужно отобрать».

Рисует три блока:
  А — анатомия одной свечи, все три меры подписаны;
  Б — ТЕЛО: семь свечей Т1-Т7, фитили РОВНЫЕ, тело от 0 до 90%;
  В — ФИТИЛИ: пять свечей С1-С5, тело одно, разница фитилей 0-70 п.п.
"""
W, H = 1180, 1000
out = []
def t(x, y, s, sz=15, col='#333', anchor='start', w='400', st=''):
    out.append(u'<text x="%g" y="%g" font-family="system-ui,Segoe UI,Arial" font-size="%g" fill="%s" text-anchor="%s" font-weight="%s" %s>%s</text>' % (x, y, sz, col, anchor, w, st, s))
def line(x1,y1,x2,y2,col='#999',w=1,dash=''):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    out.append(u'<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"%s/>' % (x1,y1,x2,y2,col,w,d))
def rect(x,y,w_,h_,fill,stroke='#222'):
    out.append(u'<rect x="%g" y="%g" width="%g" height="%g" fill="%s" stroke="%s" stroke-width="1.5"/>' % (x,y,w_,h_,fill,stroke))

def svecha(cx, top, hgt, body_pct, up_pct, bw=34, fill='#2b2b2b'):
    """рисует свечу: сверху top, высота hgt, доли в процентах высоты"""
    bh = hgt * body_pct / 100.0
    uh = hgt * up_pct / 100.0
    line(cx, top, cx, top + hgt, '#222', 1.5)
    rect(cx - bw/2.0, top + uh, bw, max(bh, 1.5), fill)
    return top + uh, top + uh + bh

out.append(u'<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W,H,W,H))
out.append(u'<rect width="%d" height="%d" fill="#ffffff"/>' % (W,H))

t(40, 46, u'ТРИГГЕРНАЯ СВЕЧА — из чего считается и что выбрать', 26, '#111', w='700')
t(40, 74, u'Схема к вопросу ТС2.1 «как она выглядит». Пиши номерами: «Т3 да, Т6 нет».', 15, '#666')

# ───────── А · АНАТОМИЯ ─────────
t(40, 126, u'А · АНАТОМИЯ. Все доли считаются от ВЫСОТЫ свечи и в сумме дают 100', 18, '#111', w='700')
ax, atop, ahgt = 150, 160, 300
by1, by2 = svecha(ax, atop, ahgt, 40, 30, bw=56)
for yy, lab in ((atop, u'максимум'), (by1, u'верх тела'), (by2, u'низ тела'), (atop+ahgt, u'минимум')):
    line(ax+40, yy, 760, yy, '#bbb', 1, '7 5')
    t(766, yy+5, lab, 13, '#888')
def mera(x, y1, y2, col, lab, val):
    line(x, y1, x, y2, col, 2)
    line(x-7, y1, x+7, y1, col, 2); line(x-7, y2, x+7, y2, col, 2)
    t(x+12, (y1+y2)/2.0 - 2, lab, 14, col, w='600')
    t(x+12, (y1+y2)/2.0 + 16, val, 13, '#777')
mera(260, atop, by1, '#c2410c', u'верхний фитиль', u'30% высоты')
mera(430, by1, by2, '#1d4ed8', u'ТЕЛО', u'40% высоты')
mera(600, by2, atop+ahgt, '#15803d', u'нижний фитиль', u'30% высоты')
line(96, atop, 96, atop+ahgt, '#111', 2)
line(89, atop, 103, atop, '#111', 2); line(89, atop+ahgt, 103, atop+ahgt, '#111', 2)
t(44, (atop+atop+ahgt)/2.0 - 2, u'ВЫСОТА', 14, '#111', w='700')
t(44, (atop+atop+ahgt)/2.0+16, u'= 100%', 13, '#777')

bx = 880
t(bx, 168, u'ТРИ УСЛОВИЯ ОТБОРА', 15, '#111', w='700')
for i,(nm, sub) in enumerate([
    (u'① ФОРМА', u'|верхний − нижний| ≤ 8 п.п.'),
    (u'② РАЗМЕР', u'высота ≤ 2× средней по 20'),
    (u'③ ПОТОЛОК', u'высота ≤ 0.40% цены')]):
    y = 202 + i*62
    t(bx, y, nm, 14, '#111', w='700'); t(bx, y+20, sub, 13, '#555')
t(bx, 392, u'ТЕЛО В ОТБОРЕ НЕ УЧАСТВУЕТ', 14, '#b91c1c', w='700')
t(bx, 412, u'ваше слово 03.11: тело ЛЮБОЕ', 13, '#777')
t(bx, 432, u'— это и есть то, что решаем', 13, '#777')

# ───────── Б · ТЕЛО ─────────
y0 = 540
t(40, y0-26, u'Б · ТЕЛО. У всех фитили РОВНЫЕ — разница 0, форма проходит у каждой', 18, '#111', w='700')
tela = [0, 10, 25, 40, 55, 70, 90]
hgt = 185
for i, b in enumerate(tela):
    cx = 118 + i*150
    up = (100 - b)/2.0
    svecha(cx, y0, hgt, b, up)
    t(cx, y0+hgt+30, u'Т%d' % (i+1), 20, '#111', 'middle', '700')
    t(cx, y0+hgt+52, u'тело %d%%' % b, 14, '#444', 'middle')
    t(cx, y0+hgt+72, u'фитили %g / %g' % (up, up), 13, '#888', 'middle')
line(40, y0-10, 1140, y0-10, '#ddd', 1, '7 5')
line(40, y0+hgt+10, 1140, y0+hgt+10, '#ddd', 1, '7 5')
t(1146, y0-6, u'', 12)

# ───────── В · ФИТИЛИ ─────────
y1 = 840
t(40, y1-26, u'В · ФИТИЛИ. Тело у всех одно, меняется только РАЗНИЦА. Порог сейчас 8 п.п.', 18, '#111', w='700')
razn = [0, 8, 20, 40, 70]
hg2 = 110
for i, r in enumerate(razn):
    cx = 118 + i*150
    up = (100 - 30)/2.0 + r/2.0
    svecha(cx, y1, hg2, 30, up)
    ok = r <= 8
    t(cx, y1+hg2+28, u'С%d' % (i+1), 20, '#111', 'middle', '700')
    t(cx, y1+hg2+50, u'разница %d' % r, 14, '#444', 'middle')
    t(cx, y1+hg2+70, u'проходит' if ok else u'НЕ проходит', 13,
      '#15803d' if ok else '#b91c1c', 'middle', '600')
line(40, y1-10, 1140, y1-10, '#ddd', 1, '7 5')

out.append(u'</svg>')
import io, sys
sys.stdout.write(u'\n'.join(out))
