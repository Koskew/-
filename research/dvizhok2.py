# -*- coding: utf-8 -*-
"""ДВИЖОК v2.0 — реплика indicator/metki_prosto_v2.pine. 07.10.2026.

Это НЕ ещё одна копия логики рядом со старой, а СЛЕДУЮЩАЯ ВЕРСИЯ.
Старый движок живёт в zerkalo.py и остаётся рабочим: по нему посчитаны
все Н до 07.10.2026, и переписывать их нельзя — они верны для своего
движка, и это записано в подписи «Движок:» у каждой записи.

ЧТО ЗДЕСЬ ДРУГОЕ ПРОТИВ zerkalo.Trend — четырнадцать правил, принятых
владельцем 05–07.10.2026:

  1. РОЖДЕНИЕ объявляет (1): любая первая вершина после LL, HH или LH
     всё равно. Поиск нуля назад (BACK = 3) убран как ненужный;
  2. СЧЁТ берёт предварительное колено живого края — отдельным слотом,
     не цепочкой. Уровень и подтверждение ждут своего слоя (З31);
  3. ДОЗА вставок по слоям: 2 у 5/5, 1 у 3/3;
  4. ДОНОР только СОСЕД: 5/5 у 3/3, 3/3 у 2/2. Запасного нет;
  5. ОТКАЗ слоя: понадобилась лишняя чужая метка — слой перестаёт
     считать этот тренд (§33);
  6. УРОВЕНЬ считается ОТ НУЛЯ заново на каждом колене. Отсюда У1, У2,
     У3, У9, У10 и возврат по З0 — одной функцией;
  7. СМЕРТЬ ОДНА: тело ниже `уровень − depth × скользящее колено`;
  8. СКОЛЬЗЯЩЕЕ СРЕДНЕЕ КОЛЕНО слоя, окно 20;
  9. ЗАПАСНОЕ ПОДТВЕРЖДЕНИЕ У7 от перебитой вершины;
 10. ЧЕТЫРЕ КОНЦА: ОТМЕНА, ОТКАЗ, СМЕРТЬ, АРХИВ;
 11. АРХИВ после (5) при низе LL;
 12. ПРОДОЛЖЕНИЕ только с (5), только у живого, только на ПЕРВОМ новом
     колене после (5);
 13. (показ, реплике не нужен);
 14. ПОЧИНКА ЗЕРКАЛА З36 — у вершины `>`, у низа `>=`.

ПОЧЕМУ ВСЕ ТРИ СЛОЯ СЧИТАЮТСЯ ОДНИМ ПРОХОДОМ. Слой 5/5 занимает колена
у 3/3, а 3/3 у 2/2, и предварительное колено живого края тоже берётся из
цепочки соседа. Считать слои по отдельности больше нельзя — пайн их и не
считает по отдельности.

    python3 research/dvizhok2.py          — самопроверка
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load

MAXK = 100          # как в пайне: цепочка обрезается сверху
LEGWIN = 20         # окно скользящего среднего колена
NBAR = 4            # закрытий подряд для варианта «4 закрытия выше вершины»

# состояния, один в один с пайном
ST_NO, ST_MAY, ST_LIVE, ST_REF, ST_ARC, ST_CAN, ST_DEAD = 0, 1, 2, 3, 4, 5, 6
ST_NAME = {ST_NO: 'нет', ST_MAY: 'возможен', ST_LIVE: 'жив', ST_REF: 'не свой',
           ST_ARC: 'архив', ST_CAN: 'не было', ST_DEAD: 'умер'}

BRK_LEG = 'выше вершины на 0.20 колена'
BRK_BAR = '4 закрытия выше вершины'


def lab(hi, cur, prev):
    """f_lab. Ничья у ВЕРШИНЫ — не перебила (LH); ничья у НИЗА —
    удержал (HL). Оператор зависит от СТОРОНЫ, а сторона переворачивается
    вместе с зеркалом, поэтому правило зеркалится само (З36)."""
    if prev is None:
        return '?'
    if hi:
        return 'HH' if cur > prev else 'LH'
    return 'HL' if cur >= prev else 'LL'


class Knees:
    """f_push + f_relabel. Обрезается до MAXK, как массив в пайне."""

    def __init__(self, cap=MAXK):
        self.P, self.B, self.H, self.L = [], [], [], []
        self.cap = cap

    def relabel(self):
        self.L = []
        for i in range(len(self.P)):
            h = self.H[i]
            prev = None
            for j in range(i - 1, -1, -1):
                if self.H[j] == h:
                    prev = self.P[j]
                    break
            self.L.append(lab(h, self.P[i], prev))

    def push(self, price, bar, isHi):
        same = bool(self.P) and self.H[-1] == isHi
        if same:
            better = price > self.P[-1] if isHi else price < self.P[-1]
            if better:
                self.P[-1] = price
                self.B[-1] = bar
        else:
            self.P.append(price)
            self.B.append(bar)
            self.H.append(isHi)
            if self.cap and len(self.P) > self.cap:
                self.P.pop(0); self.B.pop(0); self.H.pop(0)
        self.relabel()
        return not same

    def alt_ok(self, isHi):
        """f_altOk: вставка той же стороны, что последнее колено, не
        добавится, а ПОГЛОТИТСЯ — в счёт она не идёт (З22)."""
        return (not self.H) or self.H[-1] != isHi

    def avg_leg(self):
        """f_avgLeg. Средняя длина последних LEGWIN ног. Берётся МОДУЛЬ
        разницы, поэтому у перевёрнутых цен величина та же — зеркало цело."""
        n = len(self.P)
        if n < 2:
            return 0.0
        frm = max(1, n - LEGWIN)
        s = sum(abs(self.P[i] - self.P[i - 1]) for i in range(frm, n))
        return s / (n - frm)

    def pre_knee(self, donor):
        """f_preOne. Индекс колена ДОНОРА после последнего нашего колена,
        чередующегося с ним. -1, если нет."""
        if not self.B or donor is None:
            return -1
        xt, stt = self.B[-1], self.H[-1]
        for k in range(len(donor.B)):
            if donor.B[k] > xt and donor.H[k] != stt:
                return k
        return -1


class Chain:
    """Необрезанная копия цепочки: нужна, чтобы после прогона достать
    хвост любого счёта. Правило слияния и подписи — те же, поэтому
    последний элемент всегда совпадает с Knees."""

    def __init__(self):
        self.P, self.B, self.H, self.C, self.L = [], [], [], [], []

    def push(self, price, bar, isHi, conf):
        same = bool(self.P) and self.H[-1] == isHi
        if same:
            better = price > self.P[-1] if isHi else price < self.P[-1]
            if better:
                self.P[-1] = price; self.B[-1] = bar; self.C[-1] = conf
            return False
        self.P.append(price); self.B.append(bar); self.H.append(isHi); self.C.append(conf)
        return True

    def relabel(self):
        self.L = []
        for i in range(len(self.P)):
            h = self.H[i]
            prev = None
            for j in range(i - 1, -1, -1):
                if self.H[j] == h:
                    prev = self.P[j]
                    break
            self.L.append(lab(h, self.P[i], prev))


def lvl_from(K, zb, only_hl=False):
    """f_lvlSet. Уровень = ПОСЛЕДНИЙ НИЗ в цепочке, начиная с нуля.

    РАЗВИЛКА А, решение владельца 07.10.2026: «пусть съезжает на
    манипуляционный низ». Уровень переезжает на низ ЛЮБОЙ подписи, а не
    только на HL. Буквальное чтение его же правила М3 от 06.10:
    «манипуляционное колено ДЕРЖИТ, отличие не в силе, а в ЛИНИИ».

    Отличие в линии и остаётся: `real` говорит, настоящий это HL или нет,
    и по нему рисуется сплошная или штрих-пунктирная.

    ЦЕНА ЭТОГО РЕШЕНИЯ, названа владельцу: уровень поедет НИЖЕ, запас
    вырастет, тренд проживёт дольше. И штрих-пунктирная линия имеет право
    исчезнуть — тогда уровень прыгнет обратно вверх.

    only_hl=True воспроизводит прежнее поведение (развилка Б).

    Возвращает (цена, бар, настоящий_ли_HL, стоит_ли_на_НУЛЕ,
    стоит_ли_на_нуле_ПРОДОЛЖЕНИЯ).

    Пятое значение добавлено 28.10.2026 под ручку `cont_touch` (З50).
    Нового вычисления не потребовалось: это вторая половина того же
    разбора. Ноль рождения — LL, значит real=False; ноль продолжения —
    HL, значит real=True. Отсюда два взаимоисключающих случая:
        on_zero   = (not found) and (not real)   → рубит касание, «не было»
        cont_zero = (not found) and real         → рубит касание, «умер»."""
    zi = -1
    for k in range(len(K.P)):
        if K.B[k] >= zb and not K.H[k]:
            zi = k
            break
    if zi < 0:
        return None, -1, False, False, False
    lp, lx, real = K.P[zi], K.B[zi], K.L[zi] == 'HL'
    found = False
    for k in range(zi, len(K.P)):
        if not K.H[k]:
            if k == zi:
                continue
            if only_hl and K.L[k] != 'HL':
                continue
            lp, lx, real = K.P[k], K.B[k], K.L[k] == 'HL'
            found = True
    # Строгая ступень — только пока линия ШТРИХ-ПУНКТИРНАЯ, то есть пока
    # уровень стоит на нуле И этот ноль не настоящий HL. У продолжения
    # ноль настоящий (У10), и строгой ступени у него быть не должно:
    # тренд, трижды прошедший путь до (5), не может «не состояться».
    return lp, lx, real, (not found) and (not real), (not found) and real


class Trend:
    """f_trend. Состояние одного слоя одного направления.

    ПОРЯДОК ВНУТРИ БАРА ЗАДАН НАРОЧНО И ПОВТОРЯЕТ ПАЙН:
       отказ → смерть и отмена → запасное подтверждение → колена.
    Смерть проверяется ДО колен, поэтому ничья «смерть или архив на одном
    баре» разрешается в пользу смерти — §36, правило детерминированное."""

    def __init__(self):
        self.st = ST_NO
        self.zb = -1; self.zp = None; self.zl = ''
        self.pzb = -1
        self.lvl = None; self.lvb = -1; self.lhl = False
        self.on_zero = True     # уровень всё ещё стоит на НУЛЕ → строгая ступень
        self.cont_zero = False  # З50: уровень стоит на нуле ПРОДОЛЖЕНИЯ
        self.cnt = -1; self.mx = -1
        self.rst = 0            # полных счётов: сколько раз дошёл до (5) и продолжился
        self.ll = False         # в счёте был низ LL — разбудил запасное подтверждение
        self.bp = None          # перебитая вершина
        self.bab = 0
        self.born = -1
        self.eb = -1
        self.alive_bars = 0
        # история: по одной записи на КОНЕЦ счёта
        # {'zb','zl','born','end','mx','how','rst'}
        self.counts = []
        self._cur = None

    # ── служебное: открыть и закрыть запись о счёте ──
    def _open(self, bar):
        self._cur = {'zb': self.zb, 'zl': self.zl, 'born': bar, 'mx': self.cnt,
                     'end': None, 'how': None, 'rst': self.rst}

    def _close(self, bar, how):
        if self._cur is not None:
            self._cur['end'] = bar
            self._cur['how'] = how
            self.counts.append(self._cur)
            self._cur = None

    def finish(self, bar):
        """Хвост истории на последнем баре: счёт не кончился, но прогон да."""
        self._close(bar, 'идёт')

    def step(self, bar, o, h, l, c, K, nw, fr, leg, ref, depth, brk,
             cancel='касание', only_hl=False,
             nwn=None, knee_seq=False, zguard=False, wlows=None,
             birth_lvl=False, cont_touch=False):
        """РУЧКИ, значения по умолчанию в точности воспроизводят эталон:

        knee_seq — З41. False: колено разбирается ОДНО за бар, последнее,
            и счёт двигается на единицу, сколько бы колен ни пришло.
            True: колена разбираются ПО ОЧЕРЕДИ, по одному проходу на
            каждое новое, в порядке цепочки. Трогает только бары, где
            колен пришло ДВА, — свеча-накрышка.
        zguard — З40. False: рождение смотрит только вперёд. True: при
            рождении проверяется каждая свеча от бара ПОСЛЕ нуля до
            текущей включительно, и касание нуля рождение отменяет.
            Нужен wlows — «низ свечи» этого мира по барам.
        cont_touch — З50, слово владельца 28.10.2026. False: ноль
            ПРОДОЛЖЕНИЯ рубится только глубиной по телу — это У10 и
            поведение всех версий до v3.33, на нём посчитаны все прежние Н.
            True: касание нуля продолжения тоже рубит, и ИСХОДОМ СМЕРТЬ,
            а не отменой. Его прямое слово «да, умер вместо не было»:
            «не было» стирает разметку, и ровно против этого ярлыка
            возражала У10, а «умер» оставляет номера и чёрточку.
            В пайне v3.33 это галочка ⑦, по умолчанию ВКЛЮЧЕННАЯ.
        birth_lvl — З42. False: уровень пересчитывается и на баре
            рождения тоже, значит низ того же бара успевает снять строгую
            ступень. True: на баре рождения уровень НЕ трогается, он
            остаётся на нуле, ступень остаётся строгой. Имеет смысл
            только вместе с knee_seq: без него колено за бар одно.
        nwn — СКОЛЬКО новых колен на баре. None = вывести из nw."""
        if nwn is None:
            nwn = 1 if nw else 0
        if self.st in (ST_MAY, ST_LIVE):
            self.alive_bars += 1

        # ── 0. ОТКАЗ, §33 ──
        if ref:
            # АРХИВ отказом НЕ перезаписывается: у отработавшего счёта
            # считать больше нечего
            if self.st in (ST_MAY, ST_LIVE):
                self.st = ST_REF
                self.eb = bar
                self.cnt = -1
                self.lvl = None
                self.rst = 0
                self.ll = False
                self._close(bar, 'не свой')
        else:
            if self.st == ST_REF:
                self.st = ST_NO

        # ── 1. СМЕРТЬ и ОТМЕНА, каждый бар ──
        # ДВЕ СТУПЕНИ, и граница между ними проходит СРАЗУ ПОСЛЕ НОЛЯ —
        # §31, «Прочтение 1», подтверждено владельцем 06.10.2026:
        #
        #   (0)        касание рубит, без всякого запаса  → «тренда не было»
        #   (2), (4)   манипуляция прощается, убивает глубина → СМЕРТЬ
        #
        # Ступень выбирается НЕ по подтверждению, а по тому, где стоит
        # уровень: пока он на нуле — строго; съехал на низ счёта —
        # мягко. Это буквально «граница терпения проходит сразу после
        # ноля», а не «после подтверждения» и не «после (3)».
        if self.st in (ST_MAY, ST_LIVE) and self.lvl is not None:
            if self.on_zero:
                # строгая ступень: КАСАНИЕ сторожа ноля. Тренда не было
                touched = (l <= self.lvl) if cancel == 'касание' else (c < self.lvl)
                if touched:
                    self.st = ST_CAN
                    self.eb = bar
                    self.cnt = -1
                    self.lvl = None
                    self.rst = 0
                    self.ll = False
                    self._close(bar, 'не было')
            else:
                # мягкая ступень: тело ниже уровня на долю колена.
                # З50: при cont_touch касание нуля ПРОДОЛЖЕНИЯ рубит здесь
                # же, исходом СМЕРТЬ, — не в строгой ветке, потому что та
                # ставит «тренда не было» и стирает разметку
                cdie = cont_touch and self.cont_zero and l <= self.lvl
                # 28.10.2026: ТОЛЬКО ПОМЕТКА, поведение не меняет.
                # Нужна, чтобы отличать смерть ОТ КАСАНИЯ нуля продолжения
                # от смерти по глубине, — владелец попросил адреса случаев,
                # чтобы отмотать симулятор туда и проверить v3.33 глазом
                if cdie and self._cur is not None:
                    self._cur['cdie'] = True
                    self._cur['czp'] = self.lvl
                if min(o, c) < self.lvl - depth * leg or cdie:
                    self.st = ST_DEAD
                    self.eb = bar
                    self.cnt = -1
                    self.lvl = None
                    self.bab = 0
                    self.rst = 0
                    self.ll = False
                    self._close(bar, 'умер')

        # ── 2. ЗАПАСНОЕ ПОДТВЕРЖДЕНИЕ У7 ──
        # СПИТ, пока в счёте не появился низ LL
        if self.st == ST_MAY and self.ll and self.bp is not None:
            self.bab = self.bab + 1 if c > self.bp else 0
            okA = max(o, c) > self.bp + depth * leg
            okB = self.bab >= NBAR
            if (brk == BRK_LEG and okA) or (brk == BRK_BAR and okB):
                self.st = ST_LIVE

        # ── 3. НОВОЕ КОЛЕНО ──
        n = len(K.P)
        if fr and n >= 2:
            if knee_seq:
                kFirst = n - nwn if nwn >= 1 else n - 1
                for k in range(kFirst, n):
                    self._knee(bar, K, k, nwn >= 1 and k >= n - nwn,
                               leg, depth, brk, cancel, only_hl,
                               zguard, wlows, birth_lvl)
            else:
                self._knee(bar, K, n - 1, nw,
                           leg, depth, brk, cancel, only_hl,
                           zguard, wlows, birth_lvl)

    # ВТОРОЙ КОПИИ МЕХАНИКИ ЗДЕСЬ НЕТ. Блок колена ОДИН, вынесен в метод
    # ровно для того, чтобы обе ручки гоняли один и тот же код: при
    # knee_seq=False он зовётся один раз по последнему колену — это
    # эталон, байт в байт по поведению
    def _knee(self, bar, K, k, nw, leg, depth, brk, cancel, only_hl,
              zguard=False, wlows=None, birth_lvl=False):
            n = len(K.P)
            jb = k - 1 if k >= 1 else k
            lb, hiK, prK, bbK = K.L[k], K.H[k], K.P[k], K.B[k]
            if self.st in (ST_MAY, ST_LIVE):
                cnt = self.cnt
                if nw and cnt >= 5 and not hiK:
                    # ПОСЛЕ (5) решает ПЕРВЫЙ новый низ, и только он
                    if lb == 'HL':
                        # ПРОДОЛЖЕНИЕ
                        self._close(bar, 'продолжение')
                        self.pzb = self.zb
                        self.zb = bbK; self.zp = prK; self.zl = lb
                        self.cnt = 0; self.mx = 0
                        self.rst += 1
                        self.ll = False
                        self.st = ST_LIVE
                        # У10: ноль продолжения — настоящий HL, значит
                        # уровень настоящий, и строгой ступени здесь нет:
                        # касанием такой тренд не рубится
                        self.lvl = prK; self.lvb = bbK; self.lhl = True
                        self.on_zero = False
                        # З50: ноль продолжения помечен. Ручка cont_touch
                        # решает, рубит ли его касание исходом СМЕРТЬ
                        self.cont_zero = True
                        self._open(bar)
                    else:
                        # АРХИВ
                        self.st = ST_ARC
                        self.eb = bar
                        self.lvl = None
                        self._close(bar, 'архив')
                else:
                    if nw and cnt < 5:
                        self.cnt += 1
                        self.mx = max(self.mx, self.cnt)
                        if self._cur is not None:
                            self._cur['mx'] = max(self._cur['mx'], self.cnt)
                    if nw and not hiK:
                        if lb == 'HL':
                            if self.st == ST_MAY:
                                self.st = ST_LIVE
                        else:
                            self.ll = True
                # уровень пересчитывается ОТ НУЛЯ, но не у архива и — по
                # ручке birth_lvl, З42 — не на баре рождения: там он обязан
                # остаться на нуле, иначе строгая ступень не живёт ни одного
                # бара. Продолжения не касается: born пишется только рождением
                just_born = birth_lvl and self.born == bar
                if self.st in (ST_MAY, ST_LIVE) and not just_born:
                    lp, lx, real, onz, czo = lvl_from(K, self.zb, only_hl)
                    if lp is not None:
                        self.lvl, self.lvb, self.lhl, self.on_zero = lp, lx, real, onz
                        self.cont_zero = czo
            elif self.st in (ST_NO, ST_DEAD, ST_CAN, ST_ARC):
                # ── РОЖДЕНИЕ ОБЪЯВЛЯЕТ (1) ──
                if nw and hiK and k >= 1 and (not K.H[jb]) and K.L[jb] == 'LL':
                    j = jb
                    # ── РУЧКА zguard, З40 ──
                    # Сторож нуля смотрит и НАЗАД: каждая свеча от бара
                    # ПОСЛЕ нуля до текущей включительно. Коснулась нуля
                    # или ушла ниже — тренд НЕ РОЖДАЕТСЯ. Сам бар нуля не
                    # проверяется: его низ и ЕСТЬ цена нуля
                    zBroke = False
                    if zguard and wlows is not None:
                        for q in range(K.B[j] + 1, bar + 1):
                            if wlows[q] <= K.P[j]:
                                zBroke = True
                                break
                    if not zBroke:
                        self.st = ST_MAY
                        self.born = bar
                        self.zb = K.B[j]; self.zp = K.P[j]; self.zl = K.L[j]
                        self.cnt = 1; self.mx = 1
                        self.pzb = -1
                        self.rst = 0
                        self.ll = False
                        # У2: ноль — ВРЕМЕННАЯ опора, помечена честно
                        self.lvl = K.P[j]; self.lvb = K.B[j]; self.lhl = False
                        self.on_zero = True
                        self.cont_zero = False   # у рождения ноль это LL
                        # перебитая вершина — от неё считается У7
                        v = j - 1
                        while v >= 0 and not K.H[v]:
                            v -= 1
                        self.bp = K.P[v] if v >= 0 else None
                        self.bab = 0
                        self._open(bar)


# ════════════════════════════════════════════════════════════════════
#                     СЛОМЫ: ЖИВЫЕ УРОВНИ СЛОЯ
# ════════════════════════════════════════════════════════════════════
# Перенесено из metki_2x2.pine v3.26 23.10.2026 по слову владельца
# «параметры норм». Это НЕ правило тренда: слом в пайне не кормит
# движок, он пишет только свои счётчики для табло. Поэтому порт не может
# сдвинуть ни один прежний Н, и это проверяется слепком.
#
# ПОРТИРУЮТСЯ ЧЕТЫРЕ КУСКА, дословно:
#   f_lvPush   — сырой пивот попадает в список живых уровней
#   f_slom     — сломы ЭТОГО бара по ПРОШЛЫМ уровням
#   f_purgeL   — пробитый уровень вычёркивается совсем
#   f_nearest  — ближайший НЕПРОБИТЫЙ сверху и снизу от close
#
# ПОРЯДОК ВНУТРИ БАРА ВАЖЕН И ВЗЯТ ИЗ ПАЙНА (строки 2307–2314):
#   сломы → добавить сегодняшние пивоты → вычеркнуть пробитые
# Поэтому пивот, появившийся и тронутый на одном баре, сломом НЕ
# считается, но из списка уходит. Так считался и замер Н14.
#
# ДВЕ ТОНКОСТИ, обе воспроизведены НАРОЧНО и чинить их тут нельзя —
# иначе получим числа другого индикатора:
#   · пивот на ТОЧНОЙ НИЧЬЕЙ с предыдущим того же типа в список НЕ
#     попадает. В пайне это следствие hh2/lh2: оба условия ложны.
#     Замерено: 0 случаев за два года часовика, 5 за девять лет, 3 на
#     пятиминутке;
#   · САМЫЙ ПЕРВЫЙ пивот каждой стороны тоже не попадает: valuewhen(…, 1)
#     отдаёт na, сравнение с na ложно.
#
# Касание считается ТЕНЬЮ: high >= уровня, low <= уровня.
# Список НЕ ОБРЕЗАЕТСЯ — в пайне у него нет предела, только вычёркивание.


class Levels:
    """V2P/V2H пайна: живые уровни слоя в НАСТОЯЩИХ ценах.

    Слом не зеркалится: в пайне f_slom вызывается один раз, индексом 0,
    на настоящих ценах. Поэтому flip на этот класс не влияет вовсе.
    """

    def __init__(self):
        self.P = []            # цена уровня
        self.hi = []           # True — вершина, False — низ
        self._prev_hi = None   # цена предыдущего СЫРОГО пивота-вершины
        self._prev_lo = None   # то же для низа

    # ── f_lvPush плюс подпись сырого пивота ──
    def offer(self, price, isHi):
        """Сырой пивот. Возвращает True, если он попал в список."""
        if isHi:
            prev, self._prev_hi = self._prev_hi, price
        else:
            prev, self._prev_lo = self._prev_lo, price
        if prev is None or prev == price:
            return False       # первый своей стороны или точная ничья
        self.P.append(price)
        self.hi.append(isHi)
        return True

    # ── f_slom ──
    def slomy(self, h, l):
        """Сломы ЭТОГО бара по уровням, какие есть СЕЙЧАС.

        Возвращает (bu, bd): ближайший пробитый сверху и снизу, как в
        пайне — min среди вершин и max среди низов.
        """
        bu = bd = None
        for pr, isHi in zip(self.P, self.hi):
            if isHi:
                if h >= pr and (bu is None or pr < bu):
                    bu = pr
            else:
                if l <= pr and (bd is None or pr > bd):
                    bd = pr
        return bu, bd

    # ── f_purgeL ──
    def purge(self, h, l):
        keepP, keepH = [], []
        for pr, isHi in zip(self.P, self.hi):
            dead = (h >= pr) if isHi else (l <= pr)
            if not dead:
                keepP.append(pr)
                keepH.append(isHi)
        self.P, self.hi = keepP, keepH

    # ── f_nearest ──
    def nearest(self, close):
        up = dn = None
        for pr, isHi in zip(self.P, self.hi):
            if isHi:
                if pr > close and (up is None or pr < up):
                    up = pr
            else:
                if pr < close and (dn is None or pr > dn):
                    dn = pr
        return up, dn


# ════════════════════════════════════════════════════════════════════
#                            ПРОГОН
# ════════════════════════════════════════════════════════════════════

def pivots_by_bar(rows, d):
    """ta.pivothigh / ta.pivotlow глубины d: слева >=, справа >.
    Ключ — БАР ПИВОТА, а не бар подтверждения: в пайне вставка берётся
    как ph3[2] при лаге 5, то есть ровно с того же бара, что и ph5."""
    hi = [r[2] for r in rows]
    lo = [r[3] for r in rows]
    H, L = {}, {}
    for i in range(d, len(rows) - d):
        if all(hi[i - k] <= hi[i] for k in range(1, d + 1)) and \
           all(hi[i + k] < hi[i] for k in range(1, d + 1)):
            H[i] = hi[i]
        if all(lo[i - k] >= lo[i] for k in range(1, d + 1)) and \
           all(lo[i + k] > lo[i] for k in range(1, d + 1)):
            L[i] = lo[i]
    return H, L


def run_all(rows, flip=False, dose5=2, dose3=2, depth=0.20, brk=BRK_LEG,
            cancel='касание', only_hl=False, trace=False,
            zguard=False, knee_seq=False, birth_lvl=False, slom=False,
            cont_touch=False):
    """Все три слоя ОДНИМ проходом, как в пайне.

    rows — ВСЕГДА настоящие свечи. flip=True считает нисходящий: цена
    меняет знак, сторона переворачивается. Пивоты при этом ищутся по
    НАСТОЯЩИМ ценам и отдаются в НАСТОЯЩЕМ порядке — сперва вершина,
    потом низ. Зеркало меняет знак и сторону, но НЕ переставляет события
    во времени; на этом реплика уже обжигалась 23.09.2026.

    Возвращает dict: K, C, T (списки по слоям 0=5/5, 1=3/3, 2=2/2),
    pre (индексы предварительных колен), ins (сколько вставок стало
    коленом), ref_bars (на скольких барах слой был в отказе)."""
    sg = -1.0 if flip else 1.0
    sH = not flip          # сторона НАСТОЯЩЕЙ вершины в этом мире
    sL = flip              # сторона НАСТОЯЩЕГО низа
    px = (lambda v: -v) if flip else (lambda v: v)

    H5, L5 = pivots_by_bar(rows, 5)
    H3, L3 = pivots_by_bar(rows, 3)
    H2, L2 = pivots_by_bar(rows, 2)

    K = [Knees(), Knees(), Knees()]
    C = [Chain(), Chain(), Chain()]
    T = [Trend(), Trend(), Trend()]
    vcn = [0, 0, 0]
    # СКОЛЬКО новых колен пришло на этом баре — 0, 1 или 2. Ручка
    # knee_seq (З41) читает это число; при knee_seq=False оно не
    # используется вовсе, и поведение ровно эталонное
    nwc = [0, 0, 0]
    # «низ свечи» ЭТОГО мира по барам: ручке zguard (З40) надо смотреть
    # назад, а зеркало меняет знак и сторону
    wlows = [(-r[2] if flip else r[3]) for r in rows]
    vref = [False, False, False]
    ins = [0, 0, 0]
    ref_bars = [0, 0, 0]
    # ПРИБОР, а не правило: по-барный снимок уровня и состояния. Нужен
    # замерам, которые спрашивают «что было на баре», — например
    # «прыгает ли уровень вверх и не умирает ли тренд сразу после».
    # На сам движок не влияет никак
    tr = [[], [], []] if trace else None
    # ── СЛОМЫ, ручка slom. ПРИБОР, а не правило ──
    # По умолчанию False: тогда ничего не считается и прогон до символа
    # прежний. Слом живёт в НАСТОЯЩИХ ценах и не зеркалится — в пайне
    # f_slom вызывается один раз, индексом 0
    LV = Levels() if slom else None
    # по барам: (ближайший непробитый СВЕРХУ, СНИЗУ) после push и purge
    sl_near = [] if slom else None
    # события: (бар, направление 1/-1, цена пробитого уровня)
    sl_events = [] if slom else None
    # колено слоя 2/2 НА ЭТОМ БАРЕ, в той же точке, где его берёт пайн:
    # после push колен, до шага тренда
    sl_leg = [] if slom else None
    # по барам: (zb, born) слоя 2/2 ПОСЛЕ шага тренда.
    # zb — бар нуля ТЕКУЩЕГО счёта, продолжение его переписывает.
    # born — бар РОЖДЕНИЯ, продолжением НЕ переписывается, поэтому по
    # нему узнаётся, где тренд начался. Ноль ВСЕГО тренда (tZB0 пайна)
    # восстанавливается как zb на первом баре с этим же born.
    # Нужно замеру В27: серия сломов, обрезанная нулём тренда
    sl_zb = [] if slom else None
    pre_last = [-1, -1, -1]
    dose = [dose5, dose3, 0]

    def own(li, price, bar, isHi):
        nw = K[li].push(px(price), bar, isHi)
        C[li].push(px(price), bar, isHi, bar + (5, 3, 2)[li])
        vcn[li] = 0
        vref[li] = False
        if nw:
            nwc[li] += 1
        return nw

    def donor(li, price, bar, isHi):
        """Вставка. Возвращает (было_новое_колено, сорвался_ли_в_отказ)."""
        if not K[li].alt_ok(isHi):
            return False, False          # З22: поглощается, в счёт не идёт
        if vcn[li] >= dose[li]:
            return False, True           # §33: понадобилась ЛИШНЯЯ чужая метка
        nw = K[li].push(px(price), bar, isHi)
        C[li].push(px(price), bar, isHi, bar + (5, 3, 2)[li])
        vcn[li] += 1
        if nw:
            ins[li] += 1
            nwc[li] += 1
        return nw, False

    n = len(rows)
    for i in range(n):
        _, o, h, l, c = rows[i]
        nw = [False, False, False]
        fr = [False, False, False]
        nwc[0] = 0; nwc[1] = 0; nwc[2] = 0

        # ── слой 2/2: только свои, соседа снизу нет ──
        p = i - 2
        if p >= 0:
            if p in H2:
                nw[2] = own(2, H2[p], p, sH) or nw[2]; fr[2] = True
            if p in L2:
                nw[2] = own(2, L2[p], p, sL) or nw[2]; fr[2] = True

        # ── слой 3/3: свои пивоты плюс вставки с 2/2 ──
        p = i - 3
        if p >= 0:
            if p in H3:
                nw[1] = own(1, H3[p], p, sH) or nw[1]; fr[1] = True
            elif p in H2:
                fr[1] = True
                a, b = donor(1, H2[p], p, sH)
                nw[1] = a or nw[1]
                if b:
                    vref[1] = True
            if p in L3:
                nw[1] = own(1, L3[p], p, sL) or nw[1]; fr[1] = True
            elif p in L2:
                fr[1] = True
                a, b = donor(1, L2[p], p, sL)
                nw[1] = a or nw[1]
                if b:
                    vref[1] = True

        # ── слой 5/5: свои пивоты плюс вставки с 3/3 ──
        p = i - 5
        if p >= 0:
            if p in H5:
                nw[0] = own(0, H5[p], p, sH) or nw[0]; fr[0] = True
            elif p in H3:
                fr[0] = True
                a, b = donor(0, H3[p], p, sH)
                nw[0] = a or nw[0]
                if b:
                    vref[0] = True
            if p in L5:
                nw[0] = own(0, L5[p], p, sL) or nw[0]; fr[0] = True
            elif p in L3:
                fr[0] = True
                a, b = donor(0, L3[p], p, sL)
                nw[0] = a or nw[0]
                if b:
                    vref[0] = True

        # ── предварительное колено живого края, З31 ──
        pre_last[0] = K[0].pre_knee(K[1])
        pre_last[1] = K[1].pre_knee(K[2])
        pre_last[2] = -1

        # ── СЛОМЫ. Порядок как в пайне, строки 2307–2314:
        # сломы по ПРОШЛЫМ уровням → добавить сегодняшние → вычеркнуть
        if LV is not None:
            bu, bd = LV.slomy(h, l)
            if bu is not None:
                sl_events.append((i, 1, bu))
            if bd is not None:
                sl_events.append((i, -1, bd))
            pp = i - 2
            if pp >= 0:
                if pp in H2:
                    LV.offer(H2[pp], True)
                if pp in L2:
                    LV.offer(L2[pp], False)
            LV.purge(h, l)
            sl_near.append(LV.nearest(c))
            sl_leg.append(K[2].avg_leg())

        # ── шаг движка ──
        # В перевёрнутом мире «верх свечи» — это минус настоящий минимум,
        # а «низ» — минус настоящий максимум. Зеркало меняет знак и
        # сторону, но не переставляет события: поэтому пересчёт здесь, а
        # не в f_trend
        wh = -l if flip else h
        wl = -h if flip else l
        for li in range(3):
            if vref[li]:
                ref_bars[li] += 1
            T[li].step(i, sg * o, wh, wl, sg * c, K[li], nw[li], fr[li],
                       K[li].avg_leg(), vref[li], depth, brk, cancel, only_hl,
                       nwn=nwc[li], knee_seq=knee_seq, zguard=zguard,
                       wlows=wlows, birth_lvl=birth_lvl, cont_touch=cont_touch)
            if tr is not None:
                tr[li].append((T[li].lvl, T[li].st, T[li].on_zero))
        if LV is not None:
            sl_zb.append((T[2].zb, T[2].born))

    for li in range(3):
        C[li].relabel()
        T[li].finish(n - 1)
    return {'K': K, 'C': C, 'T': T, 'pre': pre_last, 'ins': ins,
            'ref_bars': ref_bars, 'trace': tr,
            'sl_near': sl_near, 'sl_events': sl_events,
            'sl_leg': sl_leg, 'sl_zb': sl_zb}


# ════════════════════════════════════════════════════════════════════
#                          САМОПРОВЕРКА
# ════════════════════════════════════════════════════════════════════

def check_mirror(rows, **kw):
    """Зеркало как ТОЖДЕСТВО: цепочка перевёрнутого мира обязана быть
    цепочкой настоящего с перевёрнутыми ценами и сторонами.

    Проверяются бары, цены, стороны, ПОДПИСИ и скользящее колено. Это и
    есть тот прогон, который 07.10.2026 нашёл З36."""
    up = run_all(rows, flip=False, **kw)
    dn = run_all(rows, flip=True, **kw)
    swap = {'HH': 'LL', 'LL': 'HH', 'HL': 'LH', 'LH': 'HL', '?': '?'}
    bad = []
    for li, nm in enumerate(('5/5', '3/3', '2/2')):
        a, b = up['C'][li], dn['C'][li]
        if len(a.P) != len(b.P):
            bad.append((nm, 'разная длина', len(a.P), len(b.P)))
            continue
        for k in range(len(a.P)):
            if a.B[k] != b.B[k]:
                bad.append((nm, k, 'бар', a.B[k], b.B[k]))
            if abs(a.P[k] + b.P[k]) > 1e-9:
                bad.append((nm, k, 'цена', a.P[k], b.P[k]))
            if a.H[k] == b.H[k]:
                bad.append((nm, k, 'сторона', a.H[k], b.H[k]))
            if swap[a.L[k]] != b.L[k]:
                bad.append((nm, k, 'подпись', a.L[k], b.L[k]))
        if abs(up['K'][li].avg_leg() - dn['K'][li].avg_leg()) > 1e-9:
            bad.append((nm, 'колено', up['K'][li].avg_leg(), dn['K'][li].avg_leg()))
    return bad


def check_invariants(res):
    """Инварианты, которые движок обязан держать при любых данных."""
    bad = []
    for li, nm in enumerate(('5/5', '3/3', '2/2')):
        T = res['T'][li]
        for ct in T.counts:
            if ct['mx'] > 5:
                bad.append((nm, 'счёт выше потолка', ct['mx']))
            if ct['how'] == 'архив' and ct['mx'] < 5:
                bad.append((nm, 'архив без (5)', ct['mx']))
            if ct['how'] == 'продолжение' and ct['mx'] < 5:
                bad.append((nm, 'продолжение без (5)', ct['mx']))
            if ct['end'] is not None and ct['born'] is not None and ct['end'] < ct['born']:
                bad.append((nm, 'конец раньше начала', ct['born'], ct['end']))
        if li == 2 and res['ref_bars'][2] != 0:
            bad.append((nm, 'у 2/2 не может быть отказа', res['ref_bars'][2]))
        if li == 2 and res['ins'][2] != 0:
            bad.append((nm, 'у 2/2 не может быть вставок', res['ins'][2]))
    return bad


def main():
    import collections
    for path, title in (('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК, два года'),
                        ('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК, девять лет'),
                        ('data/XAUUSD_5m.csv', 'ПЯТИМИНУТКА, 3.5 месяца')):
        rows = load(path)
        print('=' * 68)
        print('%s — %d баров' % (title, len(rows)))
        print('=' * 68)
        for flip, nm in ((False, 'ВОСХОДЯЩИЙ'), (True, 'НИСХОДЯЩИЙ')):
            res = run_all(rows, flip=flip)
            print('  %s' % nm)
            print('    %-5s %7s %7s %7s %7s %7s %7s %7s %7s' %
                  ('слой', 'колен', 'вставок', 'счётов', 'до(5)', 'умер', 'архив', 'не было', 'не свой'))
            for li, lname in enumerate(('5/5', '3/3', '2/2')):
                T = res['T'][li]
                cn = collections.Counter(ct['how'] for ct in T.counts)
                do5 = sum(1 for ct in T.counts if ct['mx'] >= 5)
                print('    %-5s %7d %7d %7d %7d %7d %7d %7d %7d' %
                      (lname, len(res['C'][li].P), res['ins'][li], len(T.counts), do5,
                       cn['умер'], cn['архив'], cn['не было'], cn['не свой']))
            bad = check_invariants(res)
            print('    инварианты: %s' % ('ЧИСТО' if not bad else bad[:5]))
        mir = check_mirror(rows)
        print('  ЗЕРКАЛО: %s' % ('ЦЕЛО, расхождений 0' if not mir else 'РАСХОЖДЕНИЙ %d: %s' % (len(mir), mir[:5])))
        print()


if __name__ == '__main__':
    main()
