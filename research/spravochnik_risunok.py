# -*- coding: utf-8 -*-
import io
PAT=["LH·HL·HH·HL·HH","LH·HL·HH·HL·LH","HH·HL·HH·HL·HH","HH·HL·HH·HL·LH","HH·HL·LH·HL·HH","LH·HL·LH·HL·HH","HH·HL·LH·HL·LH","LH·HL·LH·HL·LH"]
PNM=["П1","П5","П6","П12","П16","П20","П25","П29"]
SNM=["С1","С5","С6","С12","С16","С20","С25","С29"]
PFR=[151,95,66,56,58,65,25,25, 18,11,35,46,22,10,6,0]
SFR=[140,98,60,52,72,65,25,26, 17,8,14,23,22,2,9,3]
UP="#1a9850"; DN="#d73027"; INK="#222"; GR="#777"; BG="#ffffff"
W=1280; CW=300; CH=300; X0=30; Y0=380
out=[]
def t(x,y,s,size=14,fill=INK,w="normal",anchor="start"):
    s=s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{w}" text-anchor="{anchor}" font-family="Arial, sans-serif">{s}</text>')
H=Y0+2*CH+40+260
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
t(30,40,"Справочник последовательностей · слой 2/2 · metki_2x2 v3.43",24,INK,"bold")
t(30,64,"Строка табло «посл-ть». Индикатор не предсказывает — он узнаёт форму счёта и называет её номером, как шаблон свечи.",14,GR)
lines=[
"КАК ИНДИКАТОР ПОДБИРАЕТ",
"1.  Берёт метку (0) тренда — LL у рождения, HL у продолжения — и до пяти меток после неё: (1)…(5).",
"2.  В восходящем каждый низ обязан быть HL, иначе это не восходящий. Свободны только вершины (1), (3), (5) — HH или LH.",
"      Отсюда ровно 2 × 2 × 2 = 8 форм. Других не бывает.",
"3.  Пока счёт не дошёл до (5), ищет все формы, которые НАЧИНАЮТСЯ так же, как уже нарисованное:",
"      подошли 1–3 формы → пишет их имена, например  П16/П25",
"      подошло больше трёх → пишет число, например  4 вар.",
"      не подошла ни одна → «вне справ.» оранжевым: значит, какой-то низ вышел LL, а не HL. Это та же «манипуляция», что в строке «за тренд» (Н39).",
"4.  На (5) остаётся одна форма — пишет её имя цветом тренда.",
"5.  Нисходящий — точное зеркало: имена С1…С29, метки меняются HH↔LL, HL↔LH. Колонка вершин становится колонкой низов.",
"На рисунках: серый пунктир — вершина ДО (0). По ней (1) называется HH (выше неё) или LH (ниже). Красным — LH, вершина ниже предыдущей.",
]
y=100
for i,l in enumerate(lines):
    t(30,y,l,15 if i else 16,INK,"bold" if i==0 else "normal"); y+=24
t(30,y+6,"Частоты — перепись 9 лет часовика, посчитана 07.10.2026 на СТАРОМ движке, до октябрьских правок счёта. Как подпись к формам годятся, как замер нынешнего движка — нет.",13,DN)

for k,(p,nm) in enumerate(zip(PAT,PNM)):
    col=k%4; row=k//4
    cx=X0+col*CW; cy=Y0+row*CH
    out.append(f'<rect x="{cx}" y="{cy}" width="{CW-16}" height="{CH-16}" rx="10" fill="#f7f7f7" stroke="#ddd"/>')
    lab=p.split("·")
    # высоты
    y1=7 if lab[0]=="HH" else 5
    y2=2.0
    y3=y1+1.6 if lab[2]=="HH" else y1-0.8
    y4=2.8
    y5=y3+1.6 if lab[4]=="HH" else y3-0.8
    ys=[6,0,y1,y2,y3,y4,y5]
    ymax=10.6; ymin=0
    px=lambda i: cx+28+i*36
    py=lambda v: cy+222-(v-ymin)/(ymax-ymin)*150
    # предыдущая вершина пунктиром
    out.append(f'<line x1="{px(0)}" y1="{py(6)}" x2="{px(1)}" y2="{py(0)}" stroke="#bbb" stroke-dasharray="4,3" stroke-width="2"/>')
    out.append(f'<line x1="{px(0)-6}" y1="{py(6)}" x2="{px(6)+10}" y2="{py(6)}" stroke="#ccc" stroke-dasharray="2,4"/>')
    pts=" ".join(f"{px(i)},{py(v)}" for i,v in enumerate(ys) if i>=1)
    out.append(f'<polyline points="{pts}" fill="none" stroke="{UP}" stroke-width="3"/>')
    names=["(0) LL"]+[f"({i}) {lab[i-1]}" for i in range(1,6)]
    for i in range(1,7):
        v=ys[i]; isTop=i in (2,4,6)
        out.append(f'<circle cx="{px(i)}" cy="{py(v)}" r="4" fill="{UP if isTop else INK}"/>')
        s=names[i-1]
        c = DN if ("LH" in s) else INK
        t(px(i), py(v)+(-10 if isTop else 18), s,11,c,"bold" if "LH" in s else "normal","middle")
    t(cx+14,cy+28,nm,24,UP,"bold")
    t(cx+70,cy+28,"зеркало: "+SNM[k],12,GR)
    t(cx+14,cy+48,p,12,INK)
    fb, fc = PFR[k], PFR[k+8]
    sb, sc = SFR[k], SFR[k+8]
    t(cx+14,cy+262,f"восх.: рождений {fb} · продолжений {fc}",12,INK)
    t(cx+14,cy+278,f"нисх. {SNM[k]}: рождений {sb} · продолжений {sc}",12,GR)

yb=Y0+2*CH+10
t(30,yb,"КАК ЧИТАТЬ СТРОКУ «посл-ть» В ТАБЛО",16,INK,"bold")
rows=[
("П16/П25","счёт идёт, нарисовано HH·HL·LH — подходят две формы",GR),
("4 вар.","нарисована только (1), подходят четыре формы и больше",GR),
("П20","счёт дошёл до (5) — форма одна, имя цветом тренда",UP),
("вне справ.","низ вышел LL — ни одна из восьми не подходит; это «манипуляция»",'#e08214'),
("—","тренд не жив и не в архиве — показывать нечего",GR),
]
y=yb+30
for a,b,c in rows:
    t(50,y,a,15,c,"bold"); t(200,y,b,14,INK); y+=26
t(30,y+14,"Справочник лежит в коде: PAT (формы), PNM / SNM (имена), PFR / SFR (частоты). Почему номера именно 1, 5, 6, 12, 16, 20, 25, 29 — в коде не записано, достались от прежней нумерации.",12,GR)
out.append('</svg>')
io.open('/home/user/-/research/out/spravochnik_posl.svg','w',encoding='utf-8').write('\n'.join(out))
print('ok')
