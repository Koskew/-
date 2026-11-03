# -*- coding: utf-8 -*-
"""Статическая проверка пайна. Скомпилировать ассистент не может, поэтому
ловим то, что ловится глазами машины: скобки, кавычки, += и -=, которых
в пайне НЕТ, объявления после использования, размер блоков if."""
import sys, re

p=sys.argv[1]
t=open(p,encoding='utf-8').read()
L=t.split('\n')
bed=0

def ruga(s):
    global bed
    bed+=1
    print("  !! "+s)

print("="*66)
print("СТАТИКА: %s — %d строк, %d знаков" % (p,len(L),len(t)))
print()

# 1 · скобки и кавычки по строкам (вне комментариев)
print("1 · СКОБКИ И КАВЫЧКИ")
for i,s in enumerate(L,1):
    bez=re.sub(r'//.*$','',s)
    if bez.count('"')%2: ruga("строка %d: непарная кавычка" % i)
    d=bez.count('(')-bez.count(')')
    if d!=0 and not bez.rstrip().endswith(','): ruga("строка %d: скобки %+d  %s" % (i,d,bez.strip()[:60]))
    d=bez.count('[')-bez.count(']')
    if d!=0: ruga("строка %d: квадратные скобки %+d" % (i,d))
if not bed: print("  сошлись")

# 2 · операторов += и -= в пайне нет
print()
print("2 · ОПЕРАТОРЫ, КОТОРЫХ В ПАЙНЕ НЕТ")
b0=bed
for i,s in enumerate(L,1):
    bez=re.sub(r'//.*$','',s)
    for op in ('+=','-=','*=','/=','++','--'):
        if op in bez: ruga("строка %d: оператор %s — в пайне его НЕТ, нужно :=" % (i,op))
if bed==b0: print("  чисто")

# 3 · = против := для уже объявленных имён
print()
print("3 · ПЕРЕОБЪЯВЛЕНИЕ ВМЕСТО ПРИСВОЕНИЯ")
b0=bed
obj={}
for i,s in enumerate(L,1):
    bez=re.sub(r'//.*$','',s).rstrip()
    m=re.match(r'^(\s*)(?:var\s+)?(?:float|int|bool|string|color|line|label|table|box)\s+(\w+)\s*=',bez)
    if m: obj[m.group(2)]=i; continue
    m=re.match(r'^(\s*)(\w+)\s*=[^=]',bez)
    if m:
        nm=m.group(2)
        if nm in obj: ruga("строка %d: %s уже объявлено на %d — нужно := " % (i,nm,obj[nm]))
        else: obj[nm]=i
if bed==b0: print("  чисто")

# 4 · использование до объявления
print()
print("4 · ИСПОЛЬЗОВАНИЕ ДО ОБЪЯВЛЕНИЯ")
b0=bed
for nm,ln in obj.items():
    if len(nm)<3: continue
    for i,s in enumerate(L[:ln-1],1):
        bez=re.sub(r'//.*$','',s)
        if re.search(r'\b'+re.escape(nm)+r'\b',bez):
            ruga("строка %d: %s использовано, а объявлено на %d" % (i,nm,ln)); break
if bed==b0: print("  чисто")

# 5 · размер блоков if — предел TradingView, З46
print()
print("5 · БЛОКИ if — предел длины, З46")
blok=[]
for i,s in enumerate(L):
    m=re.match(r'^if\s+(.+)$',s)
    if m: blok.append((i,m.group(1)))
for st,usl in blok:
    j=st+1; kod=0; zn=0
    while j<len(L) and (L[j].startswith(' ') or L[j].startswith('\t') or L[j].strip()==''):
        if L[j].strip() and not L[j].strip().startswith('//'):
            kod+=1; zn+=len(L[j])
        j+=1
    pom = "  <== БЛИЗКО К ПРЕДЕЛУ" if kod>260 or zn>40000 else ""
    print("  строка %-4d  %-34s кода %3d строк, %6d знаков%s" % (st+1,usl[:34],kod,zn,pom))

# 6 · текст строковых литералов — предел 80 000 токенов на файл
print()
print("6 · ТЕКСТ СТРОК — предел 80 000 токенов на файл")
lit=re.findall(r'"([^"\n]*)"',t)
zn=sum(len(x) for x in lit)
print("  строковых литералов %d, знаков в них %d  ≈ %d токенов" % (len(lit),zn,zn//14))
print("  всего знаков в файле %d" % len(t))

print()
print("="*66)
print(("ВСЁ ЧИСТО" if bed==0 else "ПРОБЛЕМ: %d" % bed))
sys.exit(1 if bed else 0)
