# рисует свечи заданной формы в SVG. Доли: тело / верхняя тень / нижняя тень
W,H=1180,1010
CW,CH=224,218           # клетка
X0,Y0=40,112
BODY_W=54
CAND_H=132              # весь диапазон свечи в пикселях

RYADY=[
 ("A · САМЫЕ ЧАСТЫЕ В ВАШЕЙ БИБЛИОТЕКЕ", [
   ("1",49.3,21.5,29.2),("2",41.9,22.0,36.0),("3",54.2,21.6,24.2),("4",40.6,36.7,22.6),("5",35.2,35.7,29.1)]),
 ("B · САМЫЕ СИММЕТРИЧНЫЕ В ВАШЕЙ БИБЛИОТЕКЕ", [
   ("6",32.2,33.6,34.2),("7",25.9,37.4,36.7),("8",10.8,44.1,45.1),("9",27.9,35.3,36.8),("10",4.1,40.4,55.5)]),
 ("C · СИММЕТРИЧНЫЕ, НО ФИТИЛИ КОРОТКИЕ — их библиотека НЕ ЛОВИТ НИКОГДА", [
   ("11",60.0,20.0,20.0),("12",70.0,15.0,15.0),("13",80.0,10.0,10.0),("14",90.0,5.0,5.0),("15",96.0,2.0,2.0)]),
 ("D · КРИВЫЕ — тоже из вашей библиотеки, фитили РАЗНЫЕ", [
   ("16",14.0,27.5,58.5),("17",20.2,29.4,50.4),("18",12.6,33.7,53.7),("19",27.9,26.2,46.0),("20",24.5,28.4,47.1)]),
]

p=[]
p.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'%(W,H,W,H))
p.append('<rect width="%d" height="%d" fill="#ffffff"/>'%(W,H))
p.append('<text x="40" y="44" font-family="Helvetica,Arial" font-size="26" font-weight="700" fill="#111">Какие из этих свечей вы называете триггерными?</text>')
p.append('<text x="40" y="76" font-family="Helvetica,Arial" font-size="18" fill="#555">Формы настоящие. Ряды A, B и D взяты из ваших 40 шаблонов. Ряд C библиотека не ловит ни разу.</text>')

for ri,(zag,svechi) in enumerate(RYADY):
    ytop=Y0+ri*CH
    p.append('<text x="40" y="%d" font-family="Helvetica,Arial" font-size="17" font-weight="700" fill="#222">%s</text>'%(ytop+16,zag))
    p.append('<line x1="40" y1="%d" x2="%d" y2="%d" stroke="#e2e2e2" stroke-width="1"/>'%(ytop+26,W-40,ytop+26))
    for ci,(nom,b,u,l) in enumerate(svechi):
        cx=X0+ci*CW+BODY_W/2+42
        top=ytop+46
        hi=top
        lo=top+CAND_H
        by0=top+CAND_H*u/100.0
        by1=by0+CAND_H*b/100.0
        if by1-by0<2.0: by1=by0+2.0
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#111" stroke-width="3"/>'%(cx,hi,cx,lo))
        p.append('<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="#111"/>'%(cx-BODY_W/2,by0,BODY_W,by1-by0))
        p.append('<text x="%.1f" y="%.1f" font-family="Helvetica,Arial" font-size="22" font-weight="700" fill="#c00" text-anchor="middle">%s</text>'%(cx,lo+30,nom))
        p.append('<text x="%.1f" y="%.1f" font-family="Helvetica,Arial" font-size="13" fill="#666" text-anchor="middle">тело %.0f%%</text>'%(cx,lo+48,b))
p.append('</svg>')
open('/home/user/-/research/out/svechi_vopros.svg','w',encoding='utf-8').write('\n'.join(p))
print("нарисовано 20 свечей, 4 ряда")
