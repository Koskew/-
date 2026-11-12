# -*- coding: utf-8 -*-
# Четыре справочника последовательностей: восх / восх продолжение / нисх / нисх продолжение.
# Выписано из metki_2x2.pine v3.43: PAT, PNM, SNM, PFR, SFR.
import io, sys
PAT=["LH·HL·HH·HL·HH","LH·HL·HH·HL·LH","HH·HL·HH·HL·HH","HH·HL·HH·HL·LH","HH·HL·LH·HL·HH","LH·HL·LH·HL·HH","HH·HL·LH·HL·LH","LH·HL·LH·HL·LH"]
PNM=["П1","П5","П6","П12","П16","П20","П25","П29"]
SNM=["С1","С5","С6","С12","С16","С20","С25","С29"]
PFR=[151,95,66,56,58,65,25,25, 18,11,35,46,22,10,6,0]
SFR=[140,98,60,52,72,65,25,26, 17,8,14,23,22,2,9,3]
SW={"HH":"LL","LL":"HH","HL":"LH","LH":"HL"}
UP="#1a9850"; DN="#d73027"; WEAK="#e08214"; INK="#222"; GR="#777"
KINDS={
 "vosh":   dict(t="ВОСХОДЯЩИЙ · РОЖДЕНИЕ", z="LL", up=True,  cont=False, names=PNM, fr=PFR[:8]),
 "vosh_p": dict(t="ВОСХОДЯЩИЙ · ПРОДОЛЖЕНИЕ", z="HL", up=True,  cont=True,  names=PNM, fr=PFR[8:]),
 "nish":   dict(t="НИСХОДЯЩИЙ · РОЖДЕНИЕ", z="HH", up=False, cont=False, names=SNM, fr=SFR[:8]),
 "nish_p": dict(t="НИСХОДЯЩИЙ · ПРОДОЛЖЕНИЕ", z="LH", up=False, cont=True,  names=SNM, fr=SFR[8:]),
}
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def build(key):
    K=KINDS[key]; col=UP if K["up"] else DN
    W=1260; CW=305; CH=300; X0=24; Y0=262
    H=Y0+2*CH+20
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',f'<rect width="{W}" height="{H}" fill="#fff"/>']
    def t(x,y,s,sz=14,fill=INK,w="normal",a="start"):
        o.append(f'<text x="{x}" y="{y}" font-size="{sz}" fill="{fill}" font-weight="{w}" text-anchor="{a}" font-family="Arial, sans-serif">{esc(s)}</text>')
    total=sum(K["fr"])
    t(24,40,"Справочник последовательностей · "+K["t"],24,col,"bold")
    if K["up"]:
        z = "(0) — LL, новый низ ниже прежнего" if not K["cont"] else "(0) — HL: первый низ после (5) прошлого счёта, выше прежнего низа"
        rule="Низы (2) и (4) обязаны быть HL. Свободны вершины (1), (3), (5): HH — выше предыдущей, LH — ниже (оранжевым)."
    else:
        z = "(0) — HH, новая вершина выше прежней" if not K["cont"] else "(0) — LH: первая вершина после (5) прошлого счёта, ниже прежней вершины"
        rule="Вершины (2) и (4) обязаны быть LH. Свободны низы (1), (3), (5): LL — ниже предыдущего, HL — выше (оранжевым)."
    t(24,72,"Ноль: "+z,15)
    t(24,96,rule,15)
    t(24,120,"Отсюда ровно 2 × 2 × 2 = 8 форм — все возможные формы БЕЗ манипуляции. Девятой нет: любой другой счёт — «вне справ.».",15)
    t(24,144,"Пока счёт не дошёл до (5), в табло имена всех форм, что начинаются так же (1–3 имени) или «N вар.»; на (5) остаётся одна.",15)
    pz = "серый пунктир — " + ("вершина до (0)" if (K["up"] and not K["cont"]) else "(5) прошлого счёта" if K["up"] else "низ до (0)" if not K["cont"] else "(5) прошлого счёта") + "; по нему (1) получает свою подпись."
    if K["cont"]: pz += ("  Тонкая линия под нулём — прежний низ: ноль продолжения его не пробивает." if K["up"] else "  Тонкая линия над нулём — прежняя вершина: ноль продолжения её не пробивает.")
    t(24,168,"На рисунках: "+pz,14,GR)
    t(24,196,f"Всего {total} счётов этого вида за 9 лет часовика. Частоты посчитаны 07.10.2026 на СТАРОМ движке, до октябрьских правок счёта.",13,DN)
    t(24,216,"⚠ Н50, 25.10.2026: на честном признаке (каким счёт был виден в момент) форма НЕ предсказывает, дойдёт ли счёт до (5) — разрыв +1…+4 пп, в шуме.",13,DN)
    t(24,236,"Справочник честно ОПИСЫВАЕТ форму. «Вне справ.» ⟺ «была манипуляция» — тождество (Н39), а не предсказание.",13,GR)
    for k,(p,nm) in enumerate(zip(PAT,K["names"])):
        cx=X0+(k%4)*CW; cy=Y0+(k//4)*CH
        o.append(f'<rect x="{cx}" y="{cy}" width="{CW-14}" height="{CH-14}" rx="10" fill="#f7f7f7" stroke="#ddd"/>')
        lab=p.split("·")
        y1=7 if lab[0]=="HH" else 5
        y3=y1+1.6 if lab[2]=="HH" else y1-0.8
        y5=y3+1.6 if lab[4]=="HH" else y3-0.8
        ys=[6,0,y1,2.0,y3,2.8,y5]
        if not K["up"]: ys=[-v for v in ys]
        lo,hi=(-0.8,10.6) if K["up"] else (-10.6,0.8)
        px=lambda i: cx+30+i*36
        py=lambda v: cy+222-(v-lo)/(hi-lo)*150
        o.append(f'<line x1="{px(0)}" y1="{py(ys[0])}" x2="{px(1)}" y2="{py(ys[1])}" stroke="#bbb" stroke-dasharray="4,3" stroke-width="2"/>')
        o.append(f'<line x1="{px(0)-6}" y1="{py(ys[0])}" x2="{px(6)+10}" y2="{py(ys[0])}" stroke="#ccc" stroke-dasharray="2,4"/>')
        if K["cont"]:
            pl = -0.6 if K["up"] else 0.6
            o.append(f'<line x1="{px(0)-6}" y1="{py(pl)}" x2="{px(1)-22}" y2="{py(pl)}" stroke="#999" stroke-width="1.5"/>')
        pts=" ".join(f"{px(i)},{py(v)}" for i,v in enumerate(ys) if i>=1)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>')
        labs = lab if K["up"] else [SW[x] for x in lab]
        names=[f"(0) {K['z']}"]+[f"({i}) {labs[i-1]}" for i in range(1,6)]
        for i in range(1,7):
            v=ys[i]; ext = i in (2,4,6)
            o.append(f'<circle cx="{px(i)}" cy="{py(v)}" r="4" fill="{col if ext else INK}"/>')
            s=names[i-1]; weak = ("LH" in s) if K["up"] else ("HL" in s)
            weak = weak and ext
            above = (ext and K["up"]) or ((not ext) and not K["up"])
            t(px(i), py(v)+(-10 if above else 18), s,11,WEAK if weak else INK,"bold" if weak else "normal","middle")
        t(cx+14,cy+28,nm,24,col,"bold")
        t(cx+14,cy+48," · ".join(labs),12,INK)
        f=K["fr"][k]; pc=100.0*f/total if total else 0
        t(cx+14,cy+268,f"{f} счётов · {pc:.0f}% этого вида",13,INK,"bold" if pc>=15 else "normal")
    o.append('</svg>')
    return "\n".join(o)
if __name__=="__main__":
    for key in KINDS:
        io.open(f"/home/user/-/research/out/spravochnik_{key}.svg","w",encoding="utf-8").write(build(key))
    print("ok")
