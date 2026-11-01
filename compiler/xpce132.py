#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xpce132.py — X+ Compiler Experimental 13.2 (язык: X+13.2 Experimental).

Два режима, выбираются первой содержательной строкой программы:

1) Inject SysMode — системный режим (X+13.2 Experimental).
   Цель: 16-битный реальный режим x86, ДВУХСТУПЕНЧАТАЯ ЗАГРУЗКА —
   кернел больше не зажат в один сектор:
     boot.asm          — ступень 1: загрузочный сектор (512 байт,
                         0xAA55). Читает кернел с дискеты через INT 0x13
                         (сектора 2..N) в 0x0000:0x7E00 и передаёт ему
                         управление (far jmp 0x0000:0x7E00);
     myfirstsystem.asm — ступень 2: кернел (программа + рантайм),
                         грузится по 0x7E00, лимит 32 КБ;
     boot.bin, myfirstsystem.bin — бинарники ступеней;
     <имя>.img         — образ дискеты 1.44 МБ (boot + кернел).
   Сборка: as --32 + objcopy -O binary — БЕЗ ld (одинаково на Linux
   и Windows/MinGW). Запуск: qemu-system-i386 -fda <имя>.img
   Команды: using, vidwrite, vidread, memw, memr, wfkey, wfkeyinp, call.
   НОВОЕ В 13.2 — переменные, условия и циклы:
     var num "x"          — переменная-слово 0..65535; область 0x7000-
                            0x71FF, глобальная, объявляется на верхнем
                            уровне (до/между блоками);
     set x = выражение    — присваивание; выражения: + - * / % и скобки
                            (беззнаковые слова, деление на 0 даёт 0);
     if A == B ... else   — ветвление; сравнения = == != < > <= >=
                            (беззнаковые), есть else if;
     do 10                — счётный цикл (N повторов);
     do true              — бесконечный цикл;
     do i < 10            — цикл с условием (повторять, пока верно).
   ЦИКЛ while ОТСУТСТВУЕТ — его роль играет do с условием.
   ЭНДОВ В СИСТЕМНОМ РЕЖИМЕ НЕТ: тело if/do — это строки с одной
   ЛИШНЕЙ табуляцией (1 таб = 1 уровень); конструкция заканчивается,
   когда отступ возвращается назад. else стоит на уровне своего if.
   СРАВНЕНИЯ И ЧИСЛА: 0x-шестнадцатеричное — это ЧТЕНИЕ ЯЧЕЙКИ памяти
   (слово), поэтому if 0x3000 == 0x5000 сравнивает две ячейки;
   десятичное число — это ЗНАЧЕНИЕ (0..65535). Формы чтения памяти:
   0xADDR — слово, byte 0xADDR — байт (код клавиши: if byte 0x7418 == 97),
   word 0xADDR — слово явно. В условиях — один операнд на сторону
   (выражения — только в set: вынеси во временную переменную).
   БЛОЧНОСТЬ: каждый блок начинается строкой using name "X" (точка
   входа — using name "X" main, ровно одна); блоки разделяются тремя
   пустыми строками, после строки Inject SysMode тоже нужны 3 пустые
   строки (конец файла тоже закрывает блок). Блок ВИДИТ только блоки,
   определённые ВЫШЕ него по файлу (help-блоки пишутся выше main) и
   вызывается командой call X; в конце блока компилятор сам ставит ret.
   УСТРОЙСТВА: using device ps2keyb (только в main-блоке) включает
   wfkey/wfkeyinp. wfkey — ждать нажатия клавиши (ASCII — в байт 0x7418).
   wfkeyinp ADDR [dyn] — ждать ввода строки. Текст пока НЕ записан: он
   лежит в буфере ввода и ждёт подтверждения — следующая строка
   memw ADDR (тот же адрес) записывает текст в память. Слово dyn
   включает живое эхо: печатаемое сразу видно (Backspace стирает, Enter
   сносит набранную строку: эхо затирается без артефактов, курсор
   возвращается к началу ввода — дальше memw и vidwrite сами печатают
   текст на место ввода).
   КУРСОР И \n: у текстового вывода есть курсор (слово 0x741A), поэтому
   текст не наслаивается. \n в строке — снос на начало следующей строки;
   если экран кончился — текст пролистывается вверх целиком
   (vidwrite 0xB8000 cls сбрасывает курсор в угол).
   Синтаксис vidwrite (АДРЕС ОБЯЗАТЕЛЕН — в будущих версиях могут быть
   svga/xga): vidwrite DST "текст" | vidwrite SRC DST | vidwrite DST cls.
   Правило адреса: голый 0xB8000 — это «экран»: печать идёт С КУРСОРА и
   не наслаивается; 0xB8000+офсет (например 0xB80A0 — вторая строка) —
   печать по точному адресу.
   vidread/memr кладут прочитанное в буфер 0x7300 (до 255 символов);
   буфер ввода wfkeyinp — 0x7200-0x72FF; переменные num и счётчики do —
   0x7000-0x71FF. Пользовательские данные — свободная память НИЖЕ 0x7E00
   (например 0x3000): с 0x7E00 живёт кернел, запись туда ловится на
   этапе компиляции. Смешивать SysMode с X+ библиотекой пока нельзя.
   Комментарии: // и #.

2) Inject X+ — классический режим, полностью совместим с X+12
   (включая программы в стиле X+10: одиночные нижние end игнорируются).

Запуск:
    python xpce132.py program.xp            # компиляция (+ запуск в X+ режиме)
    python xpce132.py program.xp --no-run   # только компиляция
    python xpce132.py program.xp --target win|linux   # цель классики

Пример SysMode (переменные, do, if/else/else if; showtext ВЫШЕ main).
Отступы в языке — ТОЛЬКО табы (в этом примере они настоящие):

        Inject SysMode



	using name "showtext"
	vidwrite 0x3000 0xB8000
	vidwrite 0xB8000 "\n"



	var num "quit"
	using name "demo132" main
	using enc [ascii]
	using device ps2keyb
	vidwrite 0xB8000 cls
	vidwrite 0xB8000 "h=help q=quit\n"
	set quit = 0
	do quit == 0
		wfkey
		if byte 0x7418 == 104
			call showtext
		else if byte 0x7418 == 113
			set quit = 1
		else
			vidwrite 0xB8000 "?\n"
	vidwrite 0xB8000 "bye\n"

Пример классической программы:

    Inject X+

    block "main"
        printstr "hello world"
        end

"""

import os
import re
import subprocess
import sys

NUM_MAX = 2 ** 63 - 1      # числа — 64-битные целые со знаком
STR_BUF = 128              # размер строковой переменной в байтах

KEYWORDS = {
    'var', 'num', 'str', 'int', 'text', 'func', 'block', 'end', 'if',
    'else', 'do', 'set', 'printstr', 'printext', 'inputnum', 'inputstr',
    'exit', 'true',
}

# =, == — равенство; != ; < ; > ; <= ; >=
COND_OPS = {'=': 'eq', '==': 'eq', '!=': 'ne', '<': 'lt', '>': 'gt',
            '<=': 'le', '>=': 'ge'}

# прыжок, когда условие ЛОЖНО (cmp flags == test eax,eax flags)
JCC_FALSE = {'eq': 'jne', 'ne': 'je', 'lt': 'jge', 'gt': 'jle',
             'le': 'jg', 'ge': 'jl'}


class XPlusError(Exception):
    def __init__(self, fname, line, msg):
        super().__init__(msg)
        self.fname = fname
        self.line = line
        self.msg = msg

    def __str__(self):
        if self.line:
            return '%s:%d: error: %s' % (self.fname, self.line, self.msg)
        return 'xpce132: error: %s' % self.msg


class Tok(object):
    __slots__ = ('kind', 'val', 'line')

    def __init__(self, kind, val, line):
        self.kind = kind          # kw | ident | num | str | op | eof
        self.val = val
        self.line = line


def describe(t):
    if t.kind == 'eof':
        return 'end of file'
    if t.kind == 'str':
        return 'string "%s"' % t.val
    if t.kind == 'num':
        return 'number %s' % t.val
    return '"%s"' % t.val


# --------------------------------------------------------------------------
# Лексер
# --------------------------------------------------------------------------

def lex(src, fname):
    """Разбивает исходник на токены. Первую содержательную строку,
    начинающуюся со слова Inject, пропускаем (служебный заголовок)."""
    lines = src.split('\n')
    toks = []
    first_content_seen = False
    for ln, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if not first_content_seen:
            first_content_seen = True
            if re.match(r'Inject\b', stripped):
                continue
        i, n = 0, len(raw)
        while i < n:
            c = raw[i]
            if c in ' \t\r':
                i += 1
                continue
            if c == '#':                      # комментарий до конца строки
                break
            if c == '/' and raw[i:i + 2] == '//':
                break                         # комментарий X+13 до конца строки
            if c == '"':
                j = i + 1
                while j < n and raw[j] != '"':
                    j += 1
                if j >= n:
                    raise XPlusError(fname, ln, 'unterminated string literal')
                toks.append(Tok('str', raw[i + 1:j], ln))
                i = j + 1
                continue
            if c.isdigit():
                j = i
                if raw[i:i + 2].lower() == '0x':
                    j = i + 2
                    while j < n and raw[j] in '0123456789abcdefABCDEF':
                        j += 1
                    if j == i + 2:
                        raise XPlusError(fname, ln,
                                         'bad hex number %r' % raw[i:i + 4])
                    val = int(raw[i:j], 16)
                else:
                    while j < n and raw[j].isdigit():
                        j += 1
                    val = int(raw[i:j])
                lit = raw[i:j]
                if val > NUM_MAX:
                    raise XPlusError(fname, ln,
                                     'number too large: %s (max %d)' % (lit, NUM_MAX))
                toks.append(Tok('num', str(val), ln))   # hex нормализуем в 10-е
                i = j
                continue
            if c.isalpha() or c == '_':
                j = i
                while j < n and (raw[j].isalnum() or raw[j] == '_'):
                    j += 1
                w = raw[i:j]
                toks.append(Tok('kw' if w in KEYWORDS else 'ident', w, ln))
                i = j
                continue
            two = raw[i:i + 2]
            if two in ('==', '!=', '<=', '>='):
                toks.append(Tok('op', two, ln))
                i += 2
                continue
            if c in '=<>+-*/()':
                toks.append(Tok('op', c, ln))
                i += 1
                continue
            raise XPlusError(fname, ln, 'unexpected character %r' % c)
    toks.append(Tok('eof', '', len(lines)))
    return toks


# --------------------------------------------------------------------------
# Парсер
# --------------------------------------------------------------------------

class Program(object):
    def __init__(self):
        self.vars = {}          # имя -> 'num' | 'str'
        self.var_order = []
        self.funcs = {}         # имя -> (тело, строка определения)
        self.func_order = []
        self.main = None        # тело block "main"
        self.main_line = 0


class Parser(object):
    def __init__(self, toks, fname):
        self.toks = toks
        self.i = 0
        self.fname = fname
        self.prog = Program()

    # --- служебные -----------------------------------------------------

    def peek(self, k=0):
        j = self.i + k
        if j >= len(self.toks):
            j = len(self.toks) - 1
        return self.toks[j]

    def advance(self):
        t = self.toks[self.i]
        if t.kind != 'eof':
            self.i += 1
        return t

    def err(self, msg, tok=None):
        raise XPlusError(self.fname, (tok or self.peek()).line, msg)

    def at_kw(self, val, k=0):
        t = self.peek(k)
        return t.kind == 'kw' and t.val == val

    def expect_kw(self, val, what=None):
        if not self.at_kw(val):
            self.err('expected %s, got %s'
                     % (what or '"%s"' % val, describe(self.peek())))
        return self.advance()

    def expect_kind(self, kind, what):
        if self.peek().kind != kind:
            self.err('expected %s, got %s' % (what, describe(self.peek())))
        return self.advance()

    def expect_op(self, val):
        t = self.peek()
        if t.kind != 'op' or t.val != val:
            self.err('expected "%s", got %s' % (val, describe(t)))
        return self.advance()

    # --- верхний уровень -----------------------------------------------

    def parse_program(self):
        while True:
            t = self.peek()
            if t.kind == 'eof':
                break
            if t.kind == 'kw' and t.val == 'var':
                self.parse_var()
            elif t.kind == 'kw' and t.val == 'func' and self.peek(1).kind == 'str':
                self.parse_funcdef()
            elif t.kind == 'kw' and t.val == 'block':
                self.parse_block()
            elif t.kind == 'kw' and t.val == 'end':
                self.advance()      # закрывать нечего: нижний end (стиль X+10)
            elif t.kind == 'kw' and t.val == 'func':
                self.err('function call is not allowed at top level '
                         '(a definition looks like: func "name")')
            else:
                self.err('expected var, func or block declaration, got %s'
                         % describe(t))
        if self.prog.main is None:
            raise XPlusError(self.fname, self.peek().line,
                             'no block "main": program has no entry point')
        return self.prog

    def parse_var(self):
        t = self.advance()                              # var
        ty = self.expect_kind('kw', 'variable type (num or str)')
        if ty.val in ('int', 'text'):
            self.err('type "%s" is not supported yet (use num or str)' % ty.val, ty)
        if ty.val not in ('num', 'str'):
            self.err('expected variable type num or str, got %s' % describe(ty), ty)
        name_t = self.expect_kind('str', 'variable name in quotes')
        name = name_t.val
        if not name:
            self.err('empty variable name', name_t)
        if name in self.prog.vars:
            self.err('duplicate variable "%s"' % name, name_t)
        self.prog.vars[name] = ty.val
        self.prog.var_order.append(name)

    def parse_funcdef(self):
        t = self.advance()                              # func
        name_t = self.expect_kind('str', 'function name in quotes')
        name = name_t.val
        if not name:
            self.err('empty function name', name_t)
        if name == 'main':
            self.err('function cannot be named "main"', name_t)
        if name in self.prog.funcs:
            self.err('duplicate function "%s"' % name, name_t)
        body = self.parse_body('function "%s"' % name, t.line, in_if=False)
        self.expect_kw('end', "closing 'end' for function")
        self.prog.funcs[name] = (body, t.line)
        self.prog.func_order.append(name)

    def parse_block(self):
        t = self.advance()                              # block
        name_t = self.expect_kind('str', 'block name in quotes')
        name = name_t.val
        if name != 'main':
            self.err('unknown block "%s": only block "main" is allowed' % name,
                     name_t)
        if self.prog.main is not None:
            self.err('duplicate block "main"', name_t)
        body = self.parse_body('block "main"', t.line, in_if=False)
        self.expect_kw('end', "closing 'end' for block")
        self.prog.main = body
        self.prog.main_line = t.line
        # после main: нижние end'ы (стиль X+10) игнорируем, остальное — ошибка
        while True:
            nt = self.peek()
            if nt.kind == 'eof':
                return
            if nt.kind == 'kw' and nt.val == 'end':
                self.advance()
                continue
            if nt.kind == 'kw' and nt.val == 'block':
                if self.peek(1).kind == 'str' and self.peek(1).val == 'main':
                    self.err('duplicate block "main"', nt)
                self.err('unexpected block after block "main" — '
                         'only one block "main" is allowed', nt)
            self.err('unexpected %s after block "main" — program must end here'
                     % describe(nt), nt)

    # --- тела блоков/функций/циклов -------------------------------------

    def parse_body(self, what, opened_line, in_if):
        """Читает инструкции до терминатора. Останавливается на 'end'
        (для if — только на 'end' с 'if' следом) или на 'else' (в if),
        сам терминатор НЕ съедает."""
        stmts = []
        while True:
            t = self.peek()
            if t.kind == 'eof':
                self.err('unexpected end of file: unclosed %s (opened at line %d)'
                         % (what, opened_line))
            if t.kind == 'kw' and t.val == 'end':
                if in_if:
                    if self.at_kw('if', 1):
                        return stmts
                    self.err("expected 'end if' — bare 'end' cannot close an if", t)
                return stmts
            if t.kind == 'kw' and t.val == 'else':
                if in_if:
                    return stmts
                self.err("'else' without if", t)
            stmts.append(self.parse_statement())

    def parse_statement(self):
        t = self.peek()
        if t.kind != 'kw':
            self.err('expected a statement, got %s' % describe(t))
        v = t.val
        if v == 'printstr':
            self.advance()
            s = self.expect_kind('str', 'string literal to print')
            return ('printstr', s.val, s.line)
        if v == 'printext':
            self.advance()
            items = []
            while True:
                p = self.peek()
                if p.kind == 'str':
                    self.advance()
                    items.append(('str', p.val))
                elif p.kind == 'num' or p.kind == 'ident' \
                        or (p.kind == 'op' and p.val == '('):
                    items.append(('expr', self.parse_expr()))
                else:
                    break
            if not items:
                self.err('printext needs at least one argument', t)
            return ('printext', items, t.line)
        if v in ('inputnum', 'inputstr'):
            self.advance()
            name_t = self.expect_kind('ident', 'variable name')
            return (v, name_t.val, name_t.line)
        if v == 'set':
            self.advance()
            name_t = self.expect_kind('ident', 'variable name')
            self.expect_op('=')
            e = self.parse_expr()
            return ('set', name_t.val, e, t.line)
        if v == 'if':
            return self.parse_if()
        if v == 'do':
            return self.parse_do()
        if v == 'func':
            self.advance()
            if self.peek().kind == 'str':
                self.err('function definitions are only allowed at top level '
                         '(outside block/func)', self.peek())
            name_t = self.expect_kind('ident', 'function name to call')
            return ('call', name_t.val, name_t.line)
        if v == 'exit':
            self.advance()
            return ('exit', t.line)
        self.err('unexpected keyword "%s" here' % v)

    def parse_if(self):
        first = self.advance()                          # if
        chain = []
        while True:
            cond = self.parse_cond()
            body = self.parse_body("'if' on line %d" % first.line,
                                   first.line, in_if=True)
            chain.append((cond, body, first.line))
            if self.at_kw('end'):
                self.advance()                          # end
                self.expect_kw('if', "'if' after 'end' (i.e. 'end if')")
                return ('if', chain, first.line)
            self.advance()                              # else
            if self.at_kw('if'):
                first = self.advance()
                continue
            self.err("expected 'else if' or 'end if' — bare 'else' is not supported")

    def parse_cond(self):
        lhs = self.parse_operand()
        t = self.peek()
        if t.kind != 'op' or t.val not in COND_OPS:
            self.err('expected comparison operator (=, ==, !=, <, >, <=, >=), '
                     'got %s' % describe(t))
        self.advance()
        rhs = self.parse_operand()
        return (lhs, COND_OPS[t.val], rhs)

    def parse_operand(self):
        t = self.peek()
        if t.kind == 'num':
            self.advance()
            return ('num', int(t.val), t.line)
        if t.kind == 'str':
            self.advance()
            return ('str', t.val, t.line)
        if t.kind == 'ident':
            self.advance()
            return ('var', t.val, t.line)
        self.err('expected number, string or variable, got %s' % describe(t))

    def parse_do(self):
        t = self.advance()                              # do
        p = self.peek()
        if p.kind == 'num':
            self.advance()
            count = ('n', int(p.val))
        elif p.kind == 'kw' and p.val == 'true':
            self.advance()
            count = ('true',)
        else:
            self.err('expected number or true after do, got %s' % describe(p))
        body = self.parse_body("'do' on line %d" % t.line, t.line, in_if=False)
        self.expect_kw('end', "closing 'end' for do")
        return ('do', count, body, t.line)

    # --- выражения ------------------------------------------------------

    def parse_expr(self):
        node = self.parse_term()
        while self.peek().kind == 'op' and self.peek().val in ('+', '-'):
            op = self.advance().val
            node = ('bin', op, node, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek().kind == 'op' and self.peek().val in ('*', '/'):
            op = self.advance().val
            node = ('bin', op, node, self.parse_factor())
        return node

    def parse_factor(self):
        t = self.peek()
        if t.kind == 'num':
            self.advance()
            return ('num', int(t.val), t.line)
        if t.kind == 'ident':
            self.advance()
            return ('var', t.val, t.line)
        if t.kind == 'op' and t.val == '(':
            self.advance()
            e = self.parse_expr()
            self.expect_op(')')
            return e
        if t.kind == 'op' and t.val == '-':
            self.err('unary minus is not supported: write "0 - 5" instead of "-5"', t)
        self.err('unexpected %s in expression' % describe(t))


# --------------------------------------------------------------------------
# Семантическая проверка
# --------------------------------------------------------------------------

def validate(prog, fname):
    def vexpr(e):
        if e[0] == 'var':
            name = e[1]
            if name not in prog.vars:
                raise XPlusError(fname, e[2], 'unknown variable "%s"' % name)
            if prog.vars[name] != 'num':
                raise XPlusError(fname, e[2],
                                 'string variable "%s" cannot be used '
                                 'in a numeric expression' % name)
        elif e[0] == 'bin':
            vexpr(e[2])
            vexpr(e[3])

    def voperand(op):
        if op[0] == 'num':
            return 'num'
        if op[0] == 'str':
            return 'str'
        name = op[1]
        if name not in prog.vars:
            raise XPlusError(fname, op[2], 'unknown variable "%s"' % name)
        return prog.vars[name]

    def vstmts(stmts):
        for st in stmts:
            k = st[0]
            if k == 'printext':
                for it in st[1]:
                    if it[0] == 'expr':
                        e = it[1]
                        if e[0] == 'var':
                            # одиночная переменная — можно печатать и str
                            if e[1] not in prog.vars:
                                raise XPlusError(fname, e[2],
                                                 'unknown variable "%s"' % e[1])
                        else:
                            vexpr(e)
            elif k in ('inputnum', 'inputstr'):
                name = st[1]
                want = 'num' if k == 'inputnum' else 'str'
                if name not in prog.vars:
                    raise XPlusError(fname, st[2], 'unknown variable "%s"' % name)
                if prog.vars[name] != want:
                    raise XPlusError(fname, st[2],
                                     '%s needs a %s variable, but "%s" is %s'
                                     % (k, want, name, prog.vars[name]))
            elif k == 'set':
                name = st[1]
                if name not in prog.vars:
                    raise XPlusError(fname, st[3], 'unknown variable "%s"' % name)
                if prog.vars[name] != 'num':
                    raise XPlusError(fname, st[3],
                                     'set works only with num variables, '
                                     'but "%s" is %s' % (name, prog.vars[name]))
                vexpr(st[2])
            elif k == 'if':
                for cond, body, ln in st[1]:
                    lk = voperand(cond[0])
                    rk = voperand(cond[2])
                    if lk != rk:
                        raise XPlusError(fname, ln,
                                         'type mismatch in condition: '
                                         'cannot compare %s with %s' % (lk, rk))
                    vstmts(body)
            elif k == 'do':
                vstmts(st[2])
            elif k == 'call':
                name = st[1]
                if name == 'main':
                    raise XPlusError(fname, st[2], 'calling "main" is not allowed')
                if name not in prog.funcs:
                    raise XPlusError(fname, st[2], 'unknown function "%s"' % name)

    vstmts(prog.main)
    for name in prog.func_order:
        vstmts(prog.funcs[name][0])


# --------------------------------------------------------------------------
# Кодогенерация
# --------------------------------------------------------------------------

RT_PRINT_WIN = """\
rt_print:
    sub     rsp, 0x38
    mov     [rsp+0x20], rcx
    mov     [rsp+0x28], rdx
    mov     ecx, -11
    call    GetStdHandle
    mov     rcx, rax
    mov     rdx, [rsp+0x20]
    mov     r8d, [rsp+0x28]
    lea     r9, [rsp+0x30]
    mov     qword ptr [rsp+0x30], 0
    mov     qword ptr [rsp+0x20], 0
    call    WriteFile
    add     rsp, 0x38
    ret
"""

RT_PRINT_LINUX = """\
rt_print:
    mov     rsi, rcx
    mov     rax, 1
    mov     rdi, 1
    syscall
    ret
"""

RT_PRINT_STR_WIN = """\
rt_print_str:
    sub     rsp, 0x38
    mov     [rsp+0x20], rcx
    call    lstrlenA
    mov     rcx, [rsp+0x20]
    mov     edx, eax
    call    rt_print
    add     rsp, 0x38
    ret
"""

RT_PRINT_STR_LINUX = """\
rt_print_str:
    mov     rsi, rcx
    xor     rdx, rdx
.Lps1:
    cmp     byte ptr [rsi+rdx], 0
    je      .Lps2
    inc     rdx
    jmp     .Lps1
.Lps2:
    mov     rax, 1
    mov     rdi, 1
    syscall
    ret
"""

RT_CRLF = """\
rt_crlf:
    sub     rsp, 0x28
    lea     rcx, [rip+__crlf]
    mov     rdx, 2
    call    rt_print
    add     rsp, 0x28
    ret
"""

RT_PRINT_INT = """\
rt_print_int:
    sub     rsp, 0x38
    lea     r8, [rip+__ibuf+31]
    mov     byte ptr [r8], 0
    mov     rax, rcx
    xor     r9d, r9d
    test    rax, rax
    jns     .Lpi1
    mov     r9d, 1
    neg     rax
.Lpi1:
    xor     r10d, r10d
.Lpi2:
    xor     edx, edx
    mov     rcx, 10
    div     rcx
    add     dl, 48
    dec     r8
    mov     [r8], dl
    inc     r10d
    test    rax, rax
    jnz     .Lpi2
    test    r9d, r9d
    jz      .Lpi3
    dec     r8
    mov     byte ptr [r8], 45
    inc     r10d
.Lpi3:
    mov     rcx, r8
    mov     rdx, r10
    call    rt_print
    add     rsp, 0x38
    ret
"""

RT_INPUT_STR_WIN = """\
rt_input_str:
    # in: rcx = dest, rdx = capacity. Reads ONE line (up to LF).
    # Buffered: leftover input waits for the next call
    # (__inbuf/__inpos/__inlen) so chained inputs work on pipes/files.
    sub     rsp, 0x58
    mov     [rsp+0x30], rcx
    mov     [rsp+0x38], rdx
    mov     qword ptr [rsp+0x40], 0
.Lis_fill:
    mov     rax, [rip+__inpos]
    cmp     rax, [rip+__inlen]
    jb      .Lis_drain
    mov     ecx, -10
    call    GetStdHandle
    mov     rcx, rax
    lea     rdx, [rip+__inbuf]
    mov     r8d, 4096
    lea     r9, [rip+__inlen]
    mov     qword ptr [rip+__inlen], 0
    mov     qword ptr [rip+__inpos], 0
    mov     qword ptr [rsp+0x20], 0
    call    ReadFile
    cmp     dword ptr [rip+__inlen], 0
    je      .Lis_flush
.Lis_drain:
    mov     rax, [rip+__inpos]
    cmp     rax, [rip+__inlen]
    jae     .Lis_fill
    lea     rsi, [rip+__inbuf]
    movzx   r9d, byte ptr [rsi+rax]
    cmp     r9b, 10
    je      .Lis_eol
    cmp     r9b, 13
    je      .Lis_eat
    mov     rax, [rsp+0x40]
    cmp     rax, [rsp+0x38]
    jae     .Lis_eatc
    mov     rcx, [rsp+0x30]
    mov     [rcx+rax], r9b
    inc     rax
    mov     [rsp+0x40], rax
.Lis_eatc:
    inc     qword ptr [rip+__inpos]
    jmp     .Lis_drain
.Lis_eat:
    inc     qword ptr [rip+__inpos]
    jmp     .Lis_drain
.Lis_eol:
    inc     qword ptr [rip+__inpos]
.Lis_flush:
    mov     rax, [rsp+0x40]
    mov     rcx, [rsp+0x30]
    mov     byte ptr [rcx+rax], 0
    add     rsp, 0x58
    ret
"""

RT_INPUT_STR_LINUX = """\
rt_input_str:
    # in: rcx = dest, rdx = capacity. Reads ONE line (up to LF),
    # buffered (see WIN version). r12-r14 are saved/restored here.
    push    r12
    push    r13
    push    r14
    mov     r12, rcx
    mov     r13, rdx
    xor     r14d, r14d
.Lis_fill:
    mov     rax, [rip+__inpos]
    cmp     rax, [rip+__inlen]
    jb      .Lis_drain
    xor     edi, edi
    lea     rsi, [rip+__inbuf]
    mov     edx, 4096
    xor     eax, eax
    syscall
    test    rax, rax
    jns     .Lis_rok
    xor     eax, eax
.Lis_rok:
    mov     [rip+__inlen], rax
    mov     qword ptr [rip+__inpos], 0
    test    rax, rax
    jz      .Lis_flush
.Lis_drain:
    mov     rax, [rip+__inpos]
    cmp     rax, [rip+__inlen]
    jae     .Lis_fill
    lea     rsi, [rip+__inbuf]
    movzx   r9d, byte ptr [rsi+rax]
    cmp     r9b, 10
    je      .Lis_eol
    cmp     r9b, 13
    je      .Lis_eat
    cmp     r14, r13
    jae     .Lis_eatc
    mov     [r12+r14], r9b
    inc     r14
.Lis_eatc:
    inc     qword ptr [rip+__inpos]
    jmp     .Lis_drain
.Lis_eat:
    inc     qword ptr [rip+__inpos]
    jmp     .Lis_drain
.Lis_eol:
    inc     qword ptr [rip+__inpos]
.Lis_flush:
    mov     byte ptr [r12+r14], 0
    pop     r14
    pop     r13
    pop     r12
    ret
"""

RT_INPUT_NUM = """\
rt_input_num:
    sub     rsp, 0x38
    mov     [rsp+0x30], rcx
    lea     rcx, [rip+__tbuf]
    mov     rdx, 159
    call    rt_input_str
    lea     r10, [rip+__tbuf]
.Lin_skip:
    movzx   eax, byte ptr [r10]
    cmp     al, 32
    je      .Lin_adv
    cmp     al, 9
    je      .Lin_adv
    jmp     .Lin_sign
.Lin_adv:
    inc     r10
    jmp     .Lin_skip
.Lin_sign:
    xor     r11d, r11d
    cmp     byte ptr [r10], 45
    jne     .Lin_plus
    mov     r11d, 1
    inc     r10
    jmp     .Lin_digits
.Lin_plus:
    cmp     byte ptr [r10], 43
    jne     .Lin_digits
    inc     r10
.Lin_digits:
    xor     rax, rax
.Lin_dloop:
    movzx   edx, byte ptr [r10]
    sub     edx, 48
    cmp     edx, 9
    ja      .Lin_apply
    imul    rax, rax, 10
    add     rax, rdx
    inc     r10
    jmp     .Lin_dloop
.Lin_apply:
    test    r11d, r11d
    jz      .Lin_store
    neg     rax
.Lin_store:
    mov     rcx, [rsp+0x30]
    mov     [rcx], rax
    add     rsp, 0x38
    ret
"""

RT_STRCMP_WIN = """\
rt_strcmp:
    jmp     lstrcmpA
"""

RT_STRCMP_LINUX = """\
rt_strcmp:
    xor     eax, eax
.Lsc1:
    movzx   r8d, byte ptr [rcx+rax]
    movzx   r9d, byte ptr [rdx+rax]
    cmp     r8b, r9b
    jne     .Lsc2
    test    r8b, r8b
    jz      .Lsc3
    inc     rax
    jmp     .Lsc1
.Lsc2:
    mov     eax, r8d
    sub     eax, r9d
    ret
.Lsc3:
    xor     eax, eax
    ret
"""


class Codegen(object):
    def __init__(self, prog, target, codec):
        self.prog = prog
        self.target = target
        self.codec = codec
        self.out = []
        self.lit_id = 0
        self.lits = {}            # текст -> (метка, байты с NUL)
        self.loop_id = 0
        self.loop_slots = []
        self.lbl_id = 0
        self.vlabels = {}         # переменная -> метка данных
        self.flabels = {}         # функция -> метка кода

    def emit(self, s=''):
        self.out.append(s)

    def new_label(self, base):
        self.lbl_id += 1
        return '.L%s%d' % (base, self.lbl_id)

    def get_lit(self, s):
        if s not in self.lits:
            b = s.encode(self.codec) + b'\x00'
            self.lit_id += 1
            self.lits[s] = ('.LSTR%d' % self.lit_id, b)
        return self.lits[s][0]

    def lit_len(self, s):
        return len(s.encode(self.codec))

    # ----- сборка файла --------------------------------------------------

    def generate(self):
        p = self.prog
        for idx, name in enumerate(p.var_order):
            self.vlabels[name] = 'v%d' % idx if p.vars[name] == 'num' else 's%d' % idx
        for idx, name in enumerate(p.func_order):
            self.flabels[name] = 'f%d' % idx

        self.emit('.intel_syntax noprefix')
        self.emit('.text')
        if self.target == 'win':
            self.emit('.globl main')
            for ext in ('GetStdHandle', 'WriteFile', 'ReadFile',
                        'ExitProcess', 'lstrlenA', 'lstrcmpA'):
                self.emit('.extern %s' % ext)
        else:
            self.emit('.globl _start')
        self.emit()
        if self.target == 'win':
            self.emit(RT_PRINT_WIN)
            self.emit(RT_PRINT_STR_WIN)
            self.emit(RT_CRLF)
            self.emit(RT_PRINT_INT)
            self.emit(RT_INPUT_STR_WIN)
            self.emit(RT_INPUT_NUM)
            self.emit(RT_STRCMP_WIN)
        else:
            self.emit(RT_PRINT_LINUX)
            self.emit(RT_PRINT_STR_LINUX)
            self.emit(RT_CRLF)
            self.emit(RT_PRINT_INT)
            self.emit(RT_INPUT_STR_LINUX)
            self.emit(RT_INPUT_NUM)
            self.emit(RT_STRCMP_LINUX)
        self.emit()
        for name in p.func_order:
            self.gen_func(name)
        self.gen_main()
        self.emit_data()
        return '\n'.join(self.out) + '\n'

    # ----- функции и main -------------------------------------------------

    def gen_func(self, name):
        lbl = self.flabels[name]
        body, line = self.prog.funcs[name]
        end_lbl = '.L%s_end' % lbl
        self.emit('# func "%s" (line %d)' % (name, line))
        self.emit('%s:' % lbl)
        self.emit('    sub     rsp, 0x28')
        self.gen_stmts(body, end_lbl)
        self.emit('%s:' % end_lbl)
        self.emit('    add     rsp, 0x28')
        self.emit('    ret')
        self.emit()

    def gen_main(self):
        if self.target == 'win':
            self.emit('# block "main" - entry point')
            self.emit('main:')
            self.emit('    and     rsp, -16')
            self.emit('    sub     rsp, 0x20')
            self.gen_stmts(self.prog.main, '.Lmain_end')
            self.emit('.Lmain_end:')
            self.emit('    xor     ecx, ecx')
            self.emit('    call    ExitProcess')
        else:
            self.emit('_start:')
            self.emit('    call    xplus_main')
            self.emit('    mov     edi, 0')
            self.emit('    mov     eax, 60')
            self.emit('    syscall')
            self.emit('xplus_main:')
            self.emit('    sub     rsp, 0x28')
            self.gen_stmts(self.prog.main, '.Lmain_end')
            self.emit('.Lmain_end:')
            self.emit('    xor     edi, edi')
            self.emit('    mov     eax, 60')
            self.emit('    syscall')
        self.emit()

    # ----- инструкции ------------------------------------------------------

    def gen_stmts(self, stmts, epilogue):
        for i, st in enumerate(stmts):
            k = st[0]
            suppress = False
            if k in ('printstr', 'printext') and i + 1 < len(stmts):
                if stmts[i + 1][0] in ('inputnum', 'inputstr'):
                    suppress = True     # перед вводом \n не ставим
            if k == 'printstr':
                lbl = self.get_lit(st[1])
                self.emit('    lea     rcx, [rip+%s]' % lbl)
                self.emit('    mov     rdx, %d' % self.lit_len(st[1]))
                self.emit('    call    rt_print')
                if not suppress:
                    self.emit('    call    rt_crlf')
            elif k == 'printext':
                for it in st[1]:
                    if it[0] == 'str':
                        lbl = self.get_lit(it[1])
                        self.emit('    lea     rcx, [rip+%s]' % lbl)
                        self.emit('    mov     rdx, %d' % self.lit_len(it[1]))
                        self.emit('    call    rt_print')
                    else:
                        e = it[1]
                        if e[0] == 'var' and self.prog.vars.get(e[1]) == 'str':
                            self.emit('    lea     rcx, [rip+%s]'
                                      % self.vlabels[e[1]])
                            self.emit('    call    rt_print_str')
                        else:
                            self.gen_expr(e)
                            self.emit('    mov     rcx, rax')
                            self.emit('    call    rt_print_int')
                if not suppress:
                    self.emit('    call    rt_crlf')
            elif k == 'inputnum':
                self.emit('    lea     rcx, [rip+%s]' % self.vlabels[st[1]])
                self.emit('    call    rt_input_num')
            elif k == 'inputstr':
                self.emit('    lea     rcx, [rip+%s]' % self.vlabels[st[1]])
                self.emit('    mov     rdx, %d' % (STR_BUF - 1))
                self.emit('    call    rt_input_str')
            elif k == 'set':
                self.gen_expr(st[2])
                self.emit('    mov     [rip+%s], rax' % self.vlabels[st[1]])
            elif k == 'if':
                self.gen_if(st, epilogue)
            elif k == 'do':
                self.gen_do(st, epilogue)
            elif k == 'call':
                self.emit('    call    %s' % self.flabels[st[1]])
            elif k == 'exit':
                self.emit('    jmp     %s' % epilogue)

    def gen_if(self, st, epilogue):
        chain = st[1]
        end_lbl = self.new_label('ifend')
        next_lbl = None
        for i, (cond, body, ln) in enumerate(chain):
            if next_lbl is not None:
                self.emit('%s:' % next_lbl)
                next_lbl = None
            if i == len(chain) - 1:
                self.gen_cond_jump(cond, end_lbl)
            else:
                next_lbl = self.new_label('ifelse')
                self.gen_cond_jump(cond, next_lbl)
            self.gen_stmts(body, epilogue)
            self.emit('    jmp     %s' % end_lbl)
        self.emit('%s:' % end_lbl)

    def operand_kind(self, op):
        if op[0] == 'num':
            return 'num'
        if op[0] == 'str':
            return 'str'
        return self.prog.vars[op[1]]

    def gen_operand(self, op, reg):
        if op[0] == 'num':
            self.emit('    mov     %s, %d' % (reg, op[1]))
        elif op[0] == 'str':
            self.emit('    lea     %s, [rip+%s]' % (reg, self.get_lit(op[1])))
        else:
            if self.prog.vars[op[1]] == 'num':
                self.emit('    mov     %s, [rip+%s]' % (reg, self.vlabels[op[1]]))
            else:
                self.emit('    lea     %s, [rip+%s]' % (reg, self.vlabels[op[1]]))

    def gen_cond_jump(self, cond, false_lbl):
        lhs, op, rhs = cond
        self.gen_operand(lhs, 'rcx')
        self.gen_operand(rhs, 'rdx')
        if self.operand_kind(lhs) == 'num':
            self.emit('    cmp     rcx, rdx')
        else:
            self.emit('    call    rt_strcmp')
            self.emit('    test    eax, eax')
        self.emit('    %s     %s' % (JCC_FALSE[op], false_lbl))

    def gen_do(self, st, epilogue):
        count, body = st[1], st[2]
        top = self.new_label('dotop')
        end = self.new_label('doend')
        finite = (count[0] == 'n')
        slot = None
        if finite:
            slot = '__loop_%d' % self.loop_id
            self.loop_id += 1
            self.loop_slots.append(slot)
            self.emit('    mov     rax, %d' % count[1])
            self.emit('    mov     [rip+%s], rax' % slot)
        self.emit('%s:' % top)
        if finite:
            self.emit('    mov     rax, [rip+%s]' % slot)
            self.emit('    test    rax, rax')
            self.emit('    jz      %s' % end)
        self.gen_stmts(body, epilogue)
        if finite:
            self.emit('    dec     qword ptr [rip+%s]' % slot)
        self.emit('    jmp     %s' % top)
        self.emit('%s:' % end)

    def gen_expr(self, e):
        k = e[0]
        if k == 'num':
            self.emit('    mov     rax, %d' % e[1])
        elif k == 'var':
            self.emit('    mov     rax, [rip+%s]' % self.vlabels[e[1]])
        else:  # bin
            self.gen_expr(e[2])
            self.emit('    push    rax')
            self.gen_expr(e[3])
            self.emit('    mov     rcx, rax')
            self.emit('    pop     rax')
            op = e[1]
            if op == '+':
                self.emit('    add     rax, rcx')
            elif op == '-':
                self.emit('    sub     rax, rcx')
            elif op == '*':
                self.emit('    imul    rax, rcx')
            else:
                self.emit('    cqo')
                self.emit('    idiv    rcx')

    # ----- данные -----------------------------------------------------------

    def emit_data(self):
        if self.lits:
            self.emit('.section %s'
                      % ('.rdata' if self.target == 'win' else '.rodata'))
            for text, (lbl, b) in self.lits.items():
                self.emit('%s:' % lbl)
                self.emit('    .byte %s' % ', '.join(str(x) for x in b))
            self.emit()
        self.emit('.data')
        self.emit('__crlf:')
        self.emit('    .byte 13, 10')
        self.emit('__ibuf:')
        self.emit('    .zero 32')
        self.emit('__tbuf:')
        self.emit('    .zero 160')
        self.emit('__inbuf:')
        self.emit('    .zero 4096')
        self.emit('__inpos:')
        self.emit('    .zero 8')
        self.emit('__inlen:')
        self.emit('    .zero 8')
        for name in self.prog.var_order:
            self.emit('%s:' % self.vlabels[name])
            if self.prog.vars[name] == 'num':
                self.emit('    .zero 8')
            else:
                self.emit('    .zero %d' % STR_BUF)
        for slot in self.loop_slots:
            self.emit('%s:' % slot)
            self.emit('    .zero 8')


# --------------------------------------------------------------------------
# X+13 Experimental: SysMode — 16-битный реальный режим (boot-сектор)
# --------------------------------------------------------------------------

SYS_CMDS = ('vidwrite', 'vidread', 'memw', 'memr')
SYS_CMDS_NEW = ('wfkey', 'wfkeyinp', 'call')
SYS_DEVICES = ('ps2keyb',)
BLOCK_SEP_BLANKS = 3       # блоки (и отступ после Inject) — 3 пустые строки
NAME_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
VIDEO_BASE = 0xB8000
VIDEO_LIMIT = 0xC0000       # окно текстовой видеопамяти 0xB8000-0xBFFFF
KERNEL_BASE = 0x7E00        # boot.asm грузит кернел в 0x0000:0x7E00
KERNEL_MAX = 0x8000         # предел размера кернела: 32 КБ (0x7E00..0xFE00)
SCRATCH = 0x7300            # куда пишут vidread/memr (свободная память
                            # ниже кернела)
SCRATCH_MAX = 255           # максимум символов за одну операцию чтения
CONV_LIMIT = KERNEL_BASE    # mem-адреса: сегмент 0, ниже кернела (0-0x7DFF)
# Рабочая область X+13.1 (сегмент 0, обычная свободная память):
STAGE_BUF = 0x7200          # буфер ввода wfkeyinp: до 254 символов + NUL
STAGE_LEN = 0x72FF          # длина введённой строки (байт)
LASTKEY = 0x7418            # ASCII последней клавиши wfkey (байт)
DYNF = 0x7419               # флаг dyn: показывать ввод wfkeyinp на экране (байт)
CURSOR = 0x741A             # текстовый курсор: смещение в странице 0xB8000,
                            # 0..3999 (слово). Любая запись текста двигает его,
                            # поэтому текст не наслаивается. \n — снос строки.
GL_START = 0x741C           # начало эха ввода wfkeyinp dyn (слово): куда
                            # вернуть курсор при сносе по Enter
VAR_BASE = 0x7000           # переменные num (слова) и счётчики do
VAR_LIMIT = 0x7200          # верх области переменных: ниже буфера 0x7200
WORD_MAX = 0xFFFF           # значения — 16-битные слова (0..65535)
# сравнения if/do (X+13.2): БЕЗЗНАКОВЫЕ, слова 0..65535
SYS_COND_OPS = {'=': 'eq', '==': 'eq', '!=': 'ne', '<': 'lt', '>': 'gt',
                '<=': 'le', '>=': 'ge'}
# прыжок, когда условие ЛОЖНО (беззнаковые: lt -> jae, gt -> jbe, ...)
SYS_JCC_FALSE = {'eq': 'jne', 'ne': 'je', 'lt': 'jae', 'gt': 'jbe',
                 'le': 'ja', 'ge': 'jb'}
# имена переменных не могут совпадать с командами и ключевыми словами
SYS_RESERVED = set(SYS_CMDS) | set(SYS_CMDS_NEW) | {
    'if', 'else', 'while', 'do', 'set', 'var', 'using', 'name', 'enc',
    'device', 'main', 'byte', 'word', 'cls', 'dyn', 'true', 'ps2keyb',
}


def sys_strip_comment(raw):
    """Убирает комментарий (# или // вне строкового литерала)."""
    out = []
    i, n = 0, len(raw)
    while i < n:
        c = raw[i]
        if c == '"':
            out.append(c)
            i += 1
            while i < n and raw[i] != '"':
                out.append(raw[i])
                i += 1
            if i < n:
                out.append('"')
                i += 1
            continue
        if c == '#' or (c == '/' and i + 1 < n and raw[i + 1] == '/'):
            break
        out.append(c)
        i += 1
    return ''.join(out)


def sys_tokens(code, fname, ln):
    """('w', слово) | ('s', строка) | ('n', значение, исходник) | ('b', '['/']')"""
    toks = []
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if c in ' \t\r':
            i += 1
            continue
        if c == '"':
            j = i + 1
            buf = []
            while j < n and code[j] != '"':
                # \n — перенос строки (байт 10). Всё остальное — как есть.
                if code[j] == '\\' and j + 1 < n and code[j + 1] == 'n':
                    buf.append('\n')
                    j += 2
                    continue
                buf.append(code[j])
                j += 1
            if j >= n:
                raise XPlusError(fname, ln, 'unterminated string literal')
            sval = ''.join(buf)
            toks.append(('s', sval, sval))
            i = j + 1
            continue
        if c in '[]':
            toks.append(('b', c, c))
            i += 1
            continue
        two = code[i:i + 2]
        if two in ('==', '!=', '<=', '>='):
            toks.append(('op', two, two))
            i += 2
            continue
        if c in '=<>+-*/%()':
            toks.append(('op', c, c))
            i += 1
            continue
        if c.isdigit():
            j = i
            if code[i:i + 2].lower() == '0x':
                j = i + 2
                while j < n and code[j] in '0123456789abcdefABCDEF':
                    j += 1
                if j == i + 2:
                    raise XPlusError(fname, ln,
                                     'bad hex number %r' % code[i:i + 4])
            else:
                while j < n and code[j].isdigit():
                    j += 1
            toks.append(('n', int(code[i:j], 0), code[i:j]))
            i = j
            continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (code[j].isalnum() or code[j] == '_'):
                j += 1
            toks.append(('w', code[i:j], code[i:j]))
            i = j
            continue
        raise XPlusError(fname, ln,
                         'unexpected character %r in SysMode program' % c)
    return toks


def sys_check_str(s, fname, ln):
    for ch in s:
        o = ord(ch)
        # 10 разрешён: это \n — перенос строки
        if o >= 128 or (o < 32 and o != 9 and o != 10):
            raise XPlusError(fname, ln,
                             'only printable ascii is supported in strings '
                             '(using enc [ascii])')
    return s


def sys_check_video(a, fname, ln):
    if not (VIDEO_BASE <= a < VIDEO_LIMIT):
        raise XPlusError(fname, ln,
                         'video address 0x%X out of range (0xB8000-0xBFFFF)' % a)
    return a


def sys_check_mem(a, fname, ln):
    if not (0 <= a < KERNEL_BASE):
        if a < 0x10000:
            raise XPlusError(fname, ln,
                             'memory address 0x%X is inside the kernel '
                             'area (boot.asm loads the kernel at 0x7E00): '
                             'use an address below 0x7E00, e.g. 0x3000' % a)
        raise XPlusError(fname, ln,
                         'memory address 0x%X out of range (0-0x%X, '
                         'real mode segment 0 below the kernel at 0x7E00)'
                         % (a, KERNEL_BASE - 1))
    return a


def sys_parse(src, fname):
    """X+13.2-программа -> структура блоков:
       {'entry': str, 'devices': set, 'blocks': [блок, ...],
        'vars': {имя: адрес слова}}
       Каждый блок начинается строкой using name "X" [main]; ровно один
       блок помечен main — точка входа (выполняется сразу после
       загрузки), остальные — подпрограммы, вызываются через call X.
       Блок видит только блоки, определённые ВЫШЕ (раньше по файлу):
       help-блоки пишутся выше main. Блоки разделяются тремя пустыми
       строками; после Inject SysMode тоже нужны 3 пустые строки; конец
       файла тоже закрывает. Строки-комментарии пустыми не считаются.
       X+13.2: ЭНДОВ НЕТ — тела if/do строятся табуляцией
       (1 таб = 1 уровень; тело на 1 таб глубже заголовка; конструкция
       заканчивается, когда отступ возвращается; else — на уровне if).
         var num "x"        — переменная-слово (0x7000+, глобальная);
         set x = выражение  — присваивание (+ - * / %, скобки);
         if/else/else if    — сравнения == != < > <= >= (беззнаковые);
         do N               — счётный цикл (N повторов);
         do true            — бесконечный цикл;
         do A == B          — цикл с условием (пока верно).
       Числа: 0x... — ЧТЕНИЕ ЯЧЕЙКИ (слово), десятичное — ЗНАЧЕНИЕ.
       Формы чтения: 0xADDR (слово), byte 0xADDR (байт), word 0xADDR.
       Элементы (вложенность — телами конструкций):
       ('enc', 'ascii', line) | ('dev', name, line)
       ('stmt', op, args, line)  # vidwrite/vidread/memw/memr/wfkey/
                                 # wfkeyinp/call/set
       ('if', [(cond, body, line), ...], else_body|None, line)
       ('do', ('n', N, cell)|('true',)|('cond', cond), body, line)
       cond: (lhs, op, rhs); операнд: ('num',v)|('cell',a)|('byte',a)
             |('var',name); выражение — то же плюс ('bin',op,l,r)"""
    lines = src.split('\n')
    devices = set()
    blocks = []                 # уже закрытые блоки
    cur = None                  # открытый блок
    pending = None              # (addr, ln): wfkeyinp ждёт подтверждения memw
    named = {}                  # имя блока -> строка определения
    entry = None                # имя main-блока (точка входа)
    entry_ln = 0
    inject_gap = False          # ждём 3 пустые строки после Inject SysMode
    blanks = 0
    first = True
    stack = []                  # открытые конструкции if/do
    var_addr = {}               # имя переменной -> адрес слова
    var_next = [VAR_BASE]       # аллокатор слов (переменные и счётчики do)

    def alloc_word(what, ln):
        if var_next[0] + 2 > VAR_LIMIT:
            raise XPlusError(
                fname, ln,
                '%s: variable area 0x%X-0x%X is full (too many variables '
                'and do-loops)' % (what, VAR_BASE, VAR_LIMIT - 1))
        a = var_next[0]
        var_next[0] += 2
        return a

    def flush():
        nonlocal cur
        if cur is not None:
            blocks.append(cur)
            cur = None

    def finish_construct():
        """Закрывает верхнюю конструкцию и дописывает её узел родителю."""
        c = stack.pop()
        parent = stack[-1]['cur'] if stack else cur['items']
        if c['kind'] == 'if':
            for _cond, body, bln in c['chain']:
                if not body:
                    raise XPlusError(
                        fname, bln,
                        "empty 'if' body: indent the statements with one "
                        'more tab')
            if c['else_body'] is not None and not c['else_body']:
                raise XPlusError(
                    fname, c['else_ln'],
                    "empty 'else' body: indent the statements with one "
                    'more tab')
            parent.append(('if', c['chain'], c['else_body'], c['line']))
        else:
            if not c['cur']:
                raise XPlusError(
                    fname, c['line'],
                    "empty 'do' body: indent the statements with one more "
                    'tab')
            parent.append(('do', c['count'], c['cur'], c['line']))

    # ---------- операнды, условия, выражения ----------

    def parse_operand(toks, i, ln):
        """Один операнд сравнения/выражения -> (узел, след. индекс).
        0x-число = чтение ячейки (слово), десятичное = значение."""
        t = toks[i]
        if t[0] == 'n':
            if t[2].lower().startswith('0x'):
                a = sys_check_mem(t[1], fname, ln)
                return ('cell', a, ln), i + 1
            if t[1] > WORD_MAX:
                raise XPlusError(
                    fname, ln,
                    'value %d does not fit in 16 bits (0..65535): values '
                    'are decimal, memory cells are 0x-hex' % t[1])
            return ('num', t[1], ln), i + 1
        if t[0] == 'w' and t[1] in ('byte', 'word'):
            width = t[1]
            j = i + 1
            if j >= len(toks) or toks[j][0] != 'n' \
                    or not toks[j][2].lower().startswith('0x'):
                raise XPlusError(
                    fname, ln,
                    "'%s' needs a hex address: %s 0xADDRESS (reads one %s "
                    'from memory)'
                    % (width, width,
                       'byte' if width == 'byte' else 'word'))
            a = sys_check_mem(toks[j][1], fname, ln)
            node = ('byte', a, ln) if width == 'byte' else ('cell', a, ln)
            return node, j + 1
        if t[0] == 'w':
            if t[1] not in var_addr:
                raise XPlusError(
                    fname, ln,
                    "unknown variable '%s' (declare it at the top level: "
                    'var num "%s")' % (t[1], t[1]))
            return ('var', t[1], ln), i + 1
        if t[0] == 's':
            raise XPlusError(
                fname, ln,
                'conditions and expressions work with numbers only '
                '(decimal values, variables, 0xADDR or byte 0xADDR); '
                'strings are printed with vidwrite')
        raise XPlusError(
            fname, ln,
            'expected a value (decimal, variable, 0xADDR or byte 0xADDR), '
            'got %r' % (t[1],))

    def parse_cond(toks, i, ln):
        """условие: операнд, сравнение, операнд -> (cond, след. индекс)"""
        lhs, i = parse_operand(toks, i, ln)
        if i >= len(toks) or toks[i][0] != 'op' \
                or toks[i][1] not in SYS_COND_OPS:
            got = 'end of line' if i >= len(toks) else repr(toks[i][1])
            raise XPlusError(
                fname, ln,
                'expected a comparison operator (== != < > <= >=), got %s'
                % got)
        op = SYS_COND_OPS[toks[i][1]]
        rhs, i = parse_operand(toks, i + 1, ln)
        if i < len(toks):
            raise XPlusError(fname, ln,
                             'extra tokens after the comparison: %r'
                             % (toks[i][1],))
        return (lhs, op, rhs), i

    def parse_expr(toks, i, ln):
        """выражение с + - * / % и скобками -> (узел, след. индекс)"""
        node, i = parse_term(toks, i, ln)
        while i < len(toks) and toks[i][0] == 'op' and toks[i][1] in '+-':
            op = toks[i][1]
            rhs, i = parse_term(toks, i + 1, ln)
            node = ('bin', op, node, rhs)
        return node, i

    def parse_term(toks, i, ln):
        node, i = parse_factor(toks, i, ln)
        while i < len(toks) and toks[i][0] == 'op' and toks[i][1] in '*/%':
            op = toks[i][1]
            rhs, i = parse_factor(toks, i + 1, ln)
            node = ('bin', op, node, rhs)
        return node, i

    def parse_factor(toks, i, ln):
        if i < len(toks) and toks[i][0] == 'op' and toks[i][1] == '(':
            node, i = parse_expr(toks, i + 1, ln)
            if i >= len(toks) or toks[i] != ('op', ')', ')'):
                raise XPlusError(fname, ln, "expected ')' in expression")
            return node, i + 1
        return parse_operand(toks, i, ln)

    # ---------- конструкции ----------

    def open_construct(toks, ln, ind):
        w = toks[0][1]
        if w == 'if':
            cond, _i = parse_cond(toks, 1, ln)
            chain = [(cond, [], ln)]
            stack.append({'kind': 'if', 'indent': ind, 'line': ln,
                          'chain': chain, 'cur': chain[0][1],
                          'else_body': None, 'else_ln': 0})
        else:                                    # do: N | true | условие
            p = toks[1] if len(toks) > 1 else None
            if p is None:
                raise XPlusError(fname, ln,
                                 'do needs a repeat count, true or a '
                                 'comparison: do 10 | do true | do i < 10 '
                                 '(0x-numbers are memory cells, not counts)')
            if p[0] == 'n' and not p[2].lower().startswith('0x'):
                if p[1] > WORD_MAX:
                    raise XPlusError(fname, ln,
                                     'do %d: the count does not fit in '
                                     '16 bits' % p[1])
                cell = alloc_word('do %d' % p[1], ln)
                count = ('n', p[1], cell)
                if len(toks) > 2:
                    raise XPlusError(fname, ln,
                                     'extra tokens after do %d: %r'
                                     % (p[1], toks[2][1]))
            elif p[0] == 'w' and p[1] == 'true':
                count = ('true',)
                if len(toks) > 2:
                    raise XPlusError(fname, ln,
                                     'extra tokens after do true: %r'
                                     % (toks[2][1],))
            else:
                # do A == B — цикл с условием: повторять, пока верно
                # (проверка ПЕРЕД телом; слова while в языке нет)
                cond, _i = parse_cond(toks, 1, ln)
                count = ('cond', cond)
            stack.append({'kind': 'do', 'indent': ind, 'line': ln,
                          'count': count, 'cur': []})

    def handle_else(toks, ln):
        top = stack[-1]
        if len(toks) == 1:
            if top['else_body'] is not None:
                raise XPlusError(fname, ln,
                                 "double 'else': the if (line %d) already "
                                 'has an else branch' % top['line'])
            top['else_body'] = []
            top['cur'] = top['else_body']
            top['else_ln'] = ln
            return
        if toks[1][0] == 'w' and toks[1][1] == 'if':
            if top['else_body'] is not None:
                raise XPlusError(fname, ln,
                                 "'else if' after 'else' (the if at line %d "
                                 'already has an else branch)'
                                 % top['line'])
            cond, _i = parse_cond(toks, 2, ln)
            top['chain'].append((cond, [], ln))
            top['cur'] = top['chain'][-1][1]
            return
        raise XPlusError(fname, ln, "expected 'else if' or bare 'else'")

    def parse_var_decl(toks, ln):
        if len(toks) < 2 or toks[1][0] != 'w':
            raise XPlusError(fname, ln, 'var needs: var num "name"')
        ty = toks[1][1]
        if ty in ('int', 'text'):
            raise XPlusError(fname, ln,
                             "type '%s' is not supported yet (use num)" % ty)
        if ty != 'num':
            raise XPlusError(
                fname, ln,
                "SysMode variables are numeric: var num \"name\" (got "
                "type '%s'; strings live in memory — memw/vidwrite)" % ty)
        if len(toks) != 3 or toks[2][0] != 's':
            raise XPlusError(fname, ln,
                             'the variable name is a quoted string: '
                             'var num "x"')
        name = toks[2][1]
        if not name or not NAME_RE.match(name):
            raise XPlusError(fname, ln,
                             'variable name may contain only letters, '
                             'digits and _ (got "%s")' % name)
        if name in SYS_RESERVED:
            raise XPlusError(fname, ln,
                             "'%s' is a reserved word — pick another "
                             'variable name' % name)
        if name in var_addr:
            raise XPlusError(fname, ln, 'duplicate variable "%s"' % name)
        var_addr[name] = alloc_word('var num "%s"' % name, ln)

    # ---------- команды (в том числе внутри тел if/do) ----------

    def parse_stmt(toks, ln):
        nonlocal pending
        val = toks[0][1]
        a = toks[1:]

        def want_num(idx, what):
            if idx >= len(a) or a[idx][0] != 'n':
                raise XPlusError(fname, ln, '%s expects a number' % what)
            return a[idx][1]

        def want_str(idx):
            if idx >= len(a) or a[idx][0] != 's':
                raise XPlusError(fname, ln, 'expected a quoted string')
            return sys_check_str(a[idx][1], fname, ln)

        kinds = [t[0] for t in a]
        if val == 'set':
            if len(toks) < 2 or toks[1][0] != 'w':
                raise XPlusError(fname, ln,
                                 'set needs: set NAME = expression')
            name = toks[1][1]
            if name not in var_addr:
                raise XPlusError(
                    fname, ln,
                    "unknown variable '%s' (declare it at the top level: "
                    'var num "%s")' % (name, name))
            if len(toks) < 3 or toks[2] != ('op', '=', '='):
                raise XPlusError(fname, ln,
                                 "set: expected '=' after the variable name")
            expr, i = parse_expr(toks, 3, ln)
            if i < len(toks):
                raise XPlusError(fname, ln,
                                 'extra tokens after the expression: %r'
                                 % (toks[i][1],))
            return ('stmt', 'set', ('set', name, expr), ln)
        elif val == 'vidwrite':
            if kinds == ['n', 's']:
                return ('stmt', val,
                               ('lit', sys_check_video(want_num(0, 'vidwrite'),
                                                       fname, ln),
                                want_str(1)), ln)
            elif kinds == ['n', 'n']:
                return ('stmt', val,
                               ('copy', sys_check_mem(want_num(0, 'vidwrite'),
                                                      fname, ln),
                                sys_check_video(want_num(1, 'vidwrite'),
                                                fname, ln)), ln)
            elif kinds == ['n', 'w'] and a[1][1] == 'cls':
                return ('stmt', val,
                               ('cls', sys_check_video(want_num(0, 'vidwrite'),
                                                       fname, ln)), ln)
            else:
                # vidwrite всегда требует адрес: в будущих версиях
                # могут быть svga/xga
                raise XPlusError(fname, ln,
                                 'vidwrite needs a video address '
                                 '(svga/xga may come later): '
                                 'vidwrite VIDEO_ADDR "text" '
                                 '| vidwrite SRC VIDEO_ADDR '
                                 '| vidwrite VIDEO_ADDR cls')
        elif val == 'vidread':
            if kinds == ['n']:
                return ('stmt', val,
                               ('vid', sys_check_video(want_num(0, 'vidread'),
                                                       fname, ln)), ln)
            else:
                raise XPlusError(fname, ln,
                                 'vidread needs: vidread VIDEO_ADDR')
        elif val == 'memw':
            if kinds == ['n', 's']:
                return ('stmt', val,
                               ('lit', sys_check_mem(want_num(0, 'memw'),
                                                     fname, ln),
                                want_str(1)), ln)
            elif kinds == ['n']:
                # memw ADDR — подтверждение записи от wfkeyinp
                addr = sys_check_mem(want_num(0, 'memw'), fname, ln)
                if pending is None:
                    raise XPlusError(fname, ln,
                                     'memw 0x%X: nothing to confirm — '
                                     'first use wfkeyinp ADDR, then '
                                     'memw ADDR (same address), or write '
                                     'a string: memw ADDR "text"' % addr)
                if pending[0] != addr:
                    raise XPlusError(fname, ln,
                                     'memw 0x%X: wfkeyinp staged for '
                                     '0x%X — confirm the same address '
                                     '(memw 0x%X)'
                                     % (addr, pending[0], pending[0]))
                pending = None
                return ('stmt', val, ('commit', addr), ln)
            else:
                raise XPlusError(fname, ln,
                                 'memw needs: memw ADDR "text" '
                                 '| memw ADDR (confirm wfkeyinp)')
        elif val == 'memr':
            if kinds == ['n']:
                return ('stmt', val,
                               ('mem', sys_check_mem(want_num(0, 'memr'),
                                                     fname, ln)), ln)
            else:
                raise XPlusError(fname, ln, 'memr needs: memr ADDR')
        elif val == 'wfkey':
            # устройство проверяется после разбора: using device лежит
            # в main-блоке, а help-блоки с wfkey — ВЫШЕ него
            if a:
                raise XPlusError(fname, ln, 'wfkey takes no arguments')
            return ('stmt', val, (), ln)
        elif val == 'wfkeyinp':
            if kinds == ['n']:
                dyn = False
            elif kinds == ['n', 'w'] and a[1][1] == 'dyn':
                dyn = True
            else:
                raise XPlusError(fname, ln,
                                 'wfkeyinp needs: wfkeyinp ADDR [dyn] '
                                 '(memory 0-0xFFFF; dyn — show what '
                                 'you type)')
            addr = sys_check_mem(want_num(0, 'wfkeyinp'), fname, ln)
            if pending is not None:
                raise XPlusError(fname, ln,
                                 'wfkeyinp 0x%X: previous input (for '
                                 '0x%X) is not confirmed yet — write '
                                 'memw 0x%X first'
                                 % (addr, pending[0], pending[0]))
            pending = (addr, ln)
            return ('stmt', val, ('addr', addr, dyn), ln)
        elif val == 'call':
            if len(toks) != 2 or toks[1][0] != 'w':
                raise XPlusError(fname, ln,
                                 'call needs a block name: call showtext')
            name = toks[1][1]
            if not NAME_RE.match(name):
                raise XPlusError(fname, ln,
                                 'call: block name may contain only '
                                 'letters, digits and _ (got "%s")'
                                 % name)
            if name not in named:
                raise XPlusError(fname, ln,
                                 "call: block '%s' is not defined above — "
                                 'a block sees only blocks defined ABOVE '
                                 'it (help-blocks go above main, then '
                                 'call works)' % name)
            return ('stmt', val, ('blk', name), ln)
        elif val == 'while':
            raise XPlusError(
                fname, ln,
                "there is no 'while' in system mode: the loop is 'do' — "
                'do 10 | do true | do i < 10 (the body is indented with '
                'one tab)')
        elif val == 'end':
            raise XPlusError(fname, ln,
                             "there is no 'end' in system mode: bodies are "
                             'built with tabs (1 tab per level) and end '
                             'when the indentation returns')
        else:
            raise XPlusError(
                fname, ln,
                "unknown command '%s' — SysMode (X+13.2) supports: "
                'using (name [main] | enc | device), '
                'vidwrite VIDEO "text" | vidwrite SRC VIDEO | '
                'vidwrite VIDEO cls, vidread, memw ("text" | confirm), '
                'memr, wfkey, wfkeyinp, call, var num, set, if/else, '
                'do. SysMode cannot be combined with the X+ '
                'library yet.' % val)

    # ---------- основной проход по строкам ----------

    for ln, raw in enumerate(lines, 1):
        if not raw.strip():                       # действительно пустая строка
            blanks += 1
            # 3 пустые строки закрывают блок, но НЕ рвут открытое
            # тело if/do (там пустые строки — просто форматирование)
            if blanks >= BLOCK_SEP_BLANKS and not stack:
                flush()
            continue
        code = sys_strip_comment(raw)
        if not code.strip():                      # строка-комментарий
            continue
        # отступ: ТОЛЬКО табуляция, 1 таб = 1 уровень
        ind = 0
        j = 0
        while j < len(raw) and raw[j] == '\t':
            ind += 1
            j += 1
        if j < len(raw) and raw[j] == ' ':
            raise XPlusError(fname, ln,
                             'indentation must be TABs only: 1 tab = 1 '
                             'level (spaces are not allowed for indents)')
        code = code.strip()
        if inject_gap and blanks < BLOCK_SEP_BLANKS:
            raise XPlusError(fname, ln,
                             'leave 3 blank lines after Inject SysMode '
                             '(before the first block)')
        inject_gap = False
        blanks = 0
        if first:
            first = False
            if re.match(r'Inject\s+SysMode\b', code):
                inject_gap = True
                continue
        toks = sys_tokens(code, fname, ln)
        if not toks:
            continue
        kind0, val0 = toks[0][0], toks[0][1]
        if kind0 != 'w':
            raise XPlusError(fname, ln, 'expected a command, got %r' % (val0,))

        # ---- верхний уровень: using / var ----
        if val0 in ('using', 'var'):
            if ind != 0:
                raise XPlusError(fname, ln,
                                 '%s must start at column 1 (no tab)'
                                 % val0)
            if stack:
                c = stack[-1]
                raise XPlusError(
                    fname, ln,
                    "unclosed '%s' (opened at line %d): its body ends when "
                    'the indentation returns — close it first'
                    % (c['kind'], c['line']))
        if val0 == 'var':
            if cur is not None:
                raise XPlusError(fname, ln,
                                 'var declarations go at the top level '
                                 '(before/between blocks, after 3 blank '
                                 'lines)')
            parse_var_decl(toks, ln)
            continue
        if val0 == 'using':
            if len(toks) < 2 or toks[1][0] != 'w':
                raise XPlusError(fname, ln,
                                 "expected 'name', 'enc' or 'device' after using")
            w = toks[1][1]
            if w == 'name':
                if len(toks) < 3 or toks[2][0] != 's':
                    raise XPlusError(fname, ln,
                                     'using name needs a quoted string '
                                     '(the name is always in quotes)')
                name = toks[2][1]
                is_main = False
                if len(toks) == 4:
                    if toks[3][0] != 'w' or toks[3][1] != 'main':
                        raise XPlusError(fname, ln,
                                         "only 'main' may follow using name "
                                         '(it marks the entry point), got '
                                         "%r" % (toks[3][1],))
                    is_main = True
                elif len(toks) > 4:
                    raise XPlusError(fname, ln,
                                     'extra tokens after using name (only '
                                     'the optional word main is allowed)')
                if not NAME_RE.match(name):
                    raise XPlusError(fname, ln,
                                     'using name: block name may contain '
                                     'only letters, digits and _ '
                                     '(got "%s")' % name)
                if is_main and entry is not None:
                    raise XPlusError(fname, ln,
                                     'entry point is already set: main block '
                                     '"%s" (line %d) — only one main block '
                                     'is allowed' % (entry, entry_ln))
                if cur is not None:
                    raise XPlusError(fname, ln,
                                     'block "%s" is still open: leave 3 '
                                     'blank lines after it before using '
                                     'name "%s"' % (cur['name'], name))
                if name in named:
                    raise XPlusError(fname, ln,
                                     'duplicate block "%s" (line %d)'
                                     % (name, named[name]))
                if is_main:
                    entry = name
                    entry_ln = ln
                named[name] = ln
                cur = {'name': name, 'items': [], 'line': ln,
                       'main': is_main}
            elif w == 'enc':
                if cur is None:
                    raise XPlusError(fname, ln,
                                     'every block starts with using name "X" '
                                     '(entry point: using name "X" main)')
                if (len(toks) != 5 or toks[2][0] != 'b' or toks[2][1] != '['
                        or toks[4][0] != 'b' or toks[4][1] != ']'
                        or toks[3][0] != 'w'):
                    raise XPlusError(fname, ln,
                                     'using enc needs [name], '
                                     'e.g. using enc [ascii]')
                if toks[3][1] != 'ascii':
                    raise XPlusError(fname, ln,
                                     "encoding '%s' is not supported yet: "
                                     'only [ascii] in X+13' % toks[3][1])
                cur['items'].append(('enc', 'ascii', ln))
            elif w == 'device':
                if len(toks) != 3 or toks[2][0] != 'w':
                    raise XPlusError(fname, ln,
                                     'using device needs ps2keyb')
                dev = toks[2][1]
                if dev not in SYS_DEVICES:
                    raise XPlusError(fname, ln,
                                     "using device needs ps2keyb, got '%s'"
                                     % dev)
                if cur is None or not cur['main']:
                    raise XPlusError(fname, ln,
                                     'using device must be in the main '
                                     'block (using name "X" main)')
                if dev in devices:
                    raise XPlusError(fname, ln,
                                     'device %s is already enabled' % dev)
                devices.add(dev)
                cur['items'].append(('dev', dev, ln))
            else:
                raise XPlusError(fname, ln,
                                 "expected 'name', 'enc' or 'device' after "
                                 "using, got '%s'" % w)
            continue

        # ---- всё остальное — внутри блока ----
        if cur is None:
            raise XPlusError(fname, ln,
                             'every block starts with using name "X" '
                             '(entry point: using name "X" main)')

        # диспетчер отступов: конструкции закрываются, когда отступ
        # возвращается; 'else' цепляется к ближайшему if на СВОЁМ уровне
        while True:
            top = stack[-1] if stack else None
            if val0 == 'else':
                match = None
                for c in reversed(stack):
                    if c['indent'] < ind:
                        break
                    if c['kind'] == 'if' and c['indent'] == ind:
                        match = c
                        break
                if match is None:
                    for c in reversed(stack):
                        if c['kind'] == 'if' and c['indent'] == ind - 1:
                            raise XPlusError(
                                fname, ln,
                                "'else' is indented too deep: put it at the "
                                'same tab level as its if (line %d)'
                                % c['line'])
                    raise XPlusError(fname, ln,
                                     "'else' without if (no open if at this "
                                     'tab level)')
                while stack[-1] is not match:
                    finish_construct()
                handle_else(toks, ln)
                break
            if top is None:
                if ind != 0:
                    raise XPlusError(
                        fname, ln,
                        'unexpected indentation: statements of a block '
                        'start at column 1 (no tab)')
                if val0 in ('if', 'do'):
                    open_construct(toks, ln, 0)
                else:
                    cur['items'].append(parse_stmt(toks, ln))
                break
            if ind == top['indent'] + 1:
                if val0 in ('if', 'do'):
                    open_construct(toks, ln, ind)
                else:
                    top['cur'].append(parse_stmt(toks, ln))
                break
            if ind <= top['indent']:
                finish_construct()          # сосед на том же уровне / dedent
                continue
            raise XPlusError(
                fname, ln,
                'too much indentation: expected %d tab(s) here, got %d'
                % (top['indent'] + 1, ind))
    # конец файла закрывает конструкции так же, как блоки: дотягиваем
    # все открытые if/do до родительского уровня
    while stack:
        finish_construct()
    flush()
    if not blocks:
        raise XPlusError(fname, 1, 'empty SysMode program')
    if entry is None:
        raise XPlusError(fname, 1,
                         'no entry point: mark the start block with '
                         'using name "X" main')

    def iter_stmts(items):
        for it in items:
            if it[0] == 'stmt':
                yield it
            elif it[0] == 'if':
                for _cond, body, _ln in it[1]:
                    for x in iter_stmts(body):
                        yield x
                if it[2] is not None:
                    for x in iter_stmts(it[2]):
                        yield x
            elif it[0] == 'do':
                for x in iter_stmts(it[2]):
                    yield x

    # wfkey/wfkeyinp требуют using device ps2keyb; проверяем ПОСЛЕ
    # разбора, потому что help-блоки идут выше main с объявлением
    for blk in blocks:
        for it in iter_stmts(blk['items']):
            if (it[0] == 'stmt' and it[1] in ('wfkey', 'wfkeyinp')
                    and 'ps2keyb' not in devices):
                raise XPlusError(fname, it[3],
                                 '%s needs: using device ps2keyb '
                                 '(declare it in the main block: '
                                 'using device ps2keyb)' % it[1])
    return {'entry': entry, 'devices': devices, 'blocks': blocks,
            'vars': var_addr}

def sys_asm_escape(s):
    out = []
    for ch in s:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '\t':
            out.append('\\t')
        elif ch == '\n':
            out.append('\\n')     # GAS в .ascii понимает \n как байт 0x0A
        else:
            out.append(ch)
    return ''.join(out)


def sys_codegen(prog, fname):
    """Генерирует myfirstsystem.asm — кернел, ступень 2 (GNU as,
    .code16, 16-битный реальный режим). Кернел грузится boot.asm с
    дискеты в 0x0000:0x7E00, и туда же передаётся управление; база
    0x7E00 вшивается прямо в операнды (offset label+0x7E00), сборка —
    as --32 + objcopy -O binary, без ld.
    Вход: DS=ES=SS=0, SP=0x7C00 (boot.asm уже настроил, кернел
    подстраховывает). Выход программы — .Lhang (hlt).
    prog — структура от sys_parse: ровно один блок помечен main — это
    точка входа (выполняется сразу), остальные блоки — подпрограммы
    .Lb_<имя> ... ret, вызываются через call. Вспомогательные
    подпрограммы .Lrt_* (клавиатура, вывод) добавляются, только если
    использованы соответствующие команды."""
    # что использовано в программе — определяем ДО стартера (от этого
    # зависит инициализация курсора). Обход рекурсивный: команды могут
    # лежать в телах if/do.
    def walk(items):
        for it in items:
            k = it[0]
            if k == 'stmt':
                yield it
            elif k == 'if':
                for _cond, body, _ln in it[1]:
                    for x in walk(body):
                        yield x
                if it[2] is not None:
                    for x in walk(it[2]):
                        yield x
            elif k == 'do':
                for x in walk(it[2]):
                    yield x

    blocks = prog['blocks']
    needs = {'wfkey': False, 'getline': False,
             'puts': False, 'dyn': False}
    for blk in blocks:
        for it in walk(blk['items']):
            if it[1] == 'wfkey':
                needs['wfkey'] = True
            elif it[1] == 'wfkeyinp':
                needs['getline'] = True
                if it[2][2]:
                    needs['dyn'] = True
            elif it[1] == 'vidwrite' and it[2][0] in ('lit', 'copy'):
                needs['puts'] = True
    # курсор/скролл нужны puts (строки) и dyn (эхо ввода)
    needs['cursor'] = needs['puts'] or needs['dyn']
    out = ['/* Generated by xpce132.py (X+13.2 Experimental)',
           '   Stage 2: KERNEL (16-bit real mode).',
           '   boot.asm loads this image from floppy sectors 2..N into',
           '   0x0000:0x7E00 and far-jumps there; all absolute operands',
           '   are baked with base 0x7E00 (offset label+0x7E00). */',
           '',
           '.code16',
           '.intel_syntax noprefix',
           '.globl start',
           'start:',
           '    cli',
           '    xor     ax, ax',
           '    mov     ds, ax',
           '    mov     es, ax',
           '    mov     ss, ax',
           '    mov     sp, 0x7C00',
           '    cld',
           '    sti']
    if needs['cursor']:
        out += ['    /* text cursor: offset in video page 0xB8000 */',
                '    mov     word ptr [0x%X], 0' % CURSOR]
    lits = []
    counter = [0]
    # Сборка без ld (objcopy -O binary), база 0x7E00 (KERNEL_BASE)
    # вшивается прямо в непосредственные операнды: offset label+0x7E00.
    # ВАЖНО: в Intel-синтаксисе 'mov si, label' — это загрузка СЛОВА из
    # памяти по метке, а нам нужен АДРЕС строки, поэтому 'offset label'.
    dref = lambda lbl: 'offset %s+0x%X' % (lbl, KERNEL_BASE)

    def new_lbl(prefix):
        counter[0] += 1
        return '.L%s%d' % (prefix, counter[0])

    def lit(s):
        lbl = new_lbl('str')
        lits.append((lbl, s))
        return lbl

    def eval_expr(e):
        nonlocal out
        """Кладёт значение выражения в AX (16 бит, беззнаковое).
        Арифметика + - * / % ; деление на 0 даёт 0 (защита: в реальном
        режиме INT 0 никто не обрабатывает)."""
        k = e[0]
        if k == 'num':
            out.append('    mov     ax, 0x%X' % e[1])
        elif k == 'cell':
            out.append('    mov     ax, [0x%X]' % e[1])
        elif k == 'byte':
            out += ['    mov     al, [0x%X]' % e[1],
                    '    mov     ah, 0']
        elif k == 'var':
            out.append('    mov     ax, [0x%X]' % prog['vars'][e[1]])
        else:                                    # ('bin', op, l, r)
            eval_expr(e[2])
            out.append('    push    ax')
            eval_expr(e[3])
            out += ['    mov     bx, ax',
                    '    pop     ax']
            op = e[1]
            if op == '+':
                out.append('    add     ax, bx')
            elif op == '-':
                out.append('    sub     ax, bx')
            elif op == '*':
                out.append('    mul     bx')
            else:                                # '/' или '%'
                d1 = new_lbl('dv')
                d2 = new_lbl('dv')
                out += ['    test    bx, bx',
                        '    jnz     %s' % d1,
                        '    xor     ax, ax',
                        '    jmp     %s' % d2,
                        '%s:' % d1,
                        '    xor     dx, dx',
                        '    div     bx']
                if op == '%':
                    out.append('    mov     ax, dx')
                out.append('%s:' % d2)

    def emit_cond(cond):
        nonlocal out
        """Сравнивает операнды условия (флаги для jcc, беззнаково)."""
        eval_expr(cond[0])
        out.append('    push    ax')
        eval_expr(cond[2])
        out += ['    mov     bx, ax',
                '    pop     ax',
                '    cmp     ax, bx']

    def emit_stmt(op, args, line):
        nonlocal out
        out.append('    /* %s (line %d) */' % (op, line))
        str_lbl = None
        if op == 'vidwrite' and args[0] == 'lit':
            str_lbl = lit(args[2])
        elif op == 'memw' and args[0] == 'lit':
            str_lbl = lit(args[2])
        if op == 'vidwrite':
            if args[0] == 'cls':
                dst = args[1]
                out += ['    mov     di, 0x%X' % (dst - VIDEO_BASE),
                        '    mov     ax, 0xB800',
                        '    mov     es, ax',
                        '    xor     ax, ax',
                        '    mov     cx, 0x%X' % ((VIDEO_LIMIT - dst) // 2),
                        '    rep     stosw']
                if needs['cursor']:
                    out.append('    mov     word ptr [0x%X], 0' % CURSOR)
            elif args[0] == 'lit':
                # 0xB8000 голый = «на экран»: печать с курсора (не
                # наслаивается); 0xB8000+офсет — печать по точному адресу
                dst = args[1]
                if dst == VIDEO_BASE:
                    out.append('    mov     di, [0x%X]' % CURSOR)
                else:
                    out.append('    mov     di, 0x%X' % (dst - VIDEO_BASE))
                out += ['    mov     si, %s' % dref(str_lbl),
                        '    call    .Lrt_puts']
            else:
                # vidwrite SRC DST — строка из памяти (до нуля) на экран.
                # DST == 0xB8000 (голый адрес экрана) — печать С КУРСОРА;
                # DST 0xB8000+офсет — печать по точному адресу.
                src, dst = args[1], args[2]
                if dst == VIDEO_BASE:
                    out.append('    mov     di, [0x%X]' % CURSOR)
                else:
                    out.append('    mov     di, 0x%X' % (dst - VIDEO_BASE))
                out += ['    mov     si, 0x%X' % src,
                        '    call    .Lrt_puts']
        elif op == 'vidread':
            src = args[1]
            lp = new_lbl('vr')
            out += ['    mov     di, 0x%X' % (src - VIDEO_BASE),
                    '    mov     ax, 0xB800',
                    '    mov     es, ax',
                    '    xor     bx, bx',
                    '%s:' % lp,
                    '    mov     al, es:[di]',
                    '    test    al, al',
                    '    jz      %s_done' % lp,
                    '    mov     [bx+0x%X], al' % SCRATCH,
                    '    inc     bx',
                    '    cmp     bx, %d' % SCRATCH_MAX,
                    '    jae     %s_done' % lp,
                    '    add     di, 2',
                    '    jmp     %s' % lp,
                    '%s_done:' % lp,
                    '    mov     byte ptr [bx+0x%X], 0' % SCRATCH]
        elif op == 'memr':
            # memr ADDR — строка из памяти (до 0) в буфер 0x7300
            src = args[1]
            lp = new_lbl('mr')
            out += ['    mov     si, 0x%X' % src,
                    '    xor     bx, bx',
                    '%s:' % lp,
                    '    lodsb',
                    '    test    al, al',
                    '    jz      %s_done' % lp,
                    '    mov     [bx+0x%X], al' % SCRATCH,
                    '    inc     bx',
                    '    cmp     bx, %d' % SCRATCH_MAX,
                    '    jae     %s_done' % lp,
                    '    jmp     %s' % lp,
                    '%s_done:' % lp,
                    '    mov     byte ptr [bx+0x%X], 0' % SCRATCH]
        elif op == 'memw':
            if args[0] == 'lit':
                addr = args[1]
                out += ['    mov     di, 0x%X' % addr,
                        '    xor     ax, ax',
                        '    mov     es, ax',
                        '    mov     si, %s' % dref(str_lbl)]
                lp = new_lbl('mw')
                out += ['%s:' % lp,
                        '    lodsb',
                        '    stosb',
                        '    test    al, al',
                        '    jnz     %s' % lp]
            else:
                # ('commit', addr): подтверждение записи от wfkeyinp —
                # копируем строку (с завершающим 0) из буфера ввода в память
                addr = args[1]
                out += ['    mov     cl, [0x%X]' % STAGE_LEN,
                        '    mov     ch, 0',
                        '    inc     cx',
                        '    mov     si, 0x%X' % STAGE_BUF,
                        '    mov     di, 0x%X' % addr,
                        '    xor     ax, ax',
                        '    mov     es, ax',
                        '    rep     movsb']
        elif op == 'wfkey':
            out.append('    call    .Lrt_wfkey')
        elif op == 'wfkeyinp':
            if needs['dyn']:
                out.append('    mov     byte ptr [0x%X], %d'
                           % (DYNF, 1 if args[2] else 0))
            out.append('    call    .Lrt_getline')
        elif op == 'call':
            out.append('    call    .Lb_%s' % args[1])
        elif op == 'set':
            # set x = выражение: значение выражения — в AX (eval_expr),
            # сохраняем слово в ячейку переменной
            eval_expr(args[2])
            out.append('    mov     [0x%X], ax' % prog['vars'][args[1]])

    def emit_if(chain, else_body, line):
        nonlocal out
        """if/else if/else: беззнаковые сравнения, прыжок когда ЛОЖНО."""
        out.append('    /* if (line %d) */' % line)
        elifs = [new_lbl('elif') for _ in range(len(chain) - 1)]
        els = new_lbl('else') if else_body is not None else None
        end = new_lbl('endif')
        for idx, (cond, body, bln) in enumerate(chain):
            if idx:
                out += ['%s:' % elifs[idx - 1],
                        '    /* else if (line %d) */' % bln]
            emit_cond(cond)
            if idx < len(chain) - 1:
                tgt = elifs[idx]
            elif els is not None:
                tgt = els
            else:
                tgt = end
            out.append('    %s     %s' % (SYS_JCC_FALSE[cond[1]], tgt))
            emit_items(body)
            out.append('    jmp     %s' % end)
        if els is not None:
            out += ['%s:' % els,
                    '    /* else (line %d) */' % line]
            emit_items(else_body)
        out.append('%s:' % end)

    def emit_do(count, body, line):
        nonlocal out
        top = new_lbl('dtop')
        if count[0] == 'true':
            out += ['    /* do true (line %d) */' % line,
                    '%s:' % top]
            emit_items(body)
            out.append('    jmp     %s' % top)
            return
        if count[0] == 'cond':
            # do A == B — цикл с условием (проверка ПЕРЕД телом)
            out.append('    /* do (line %d) */' % line)
            end = new_lbl('dend')
            out.append('%s:' % top)
            emit_cond(count[1])
            out.append('    %s     %s' % (SYS_JCC_FALSE[count[1][1]], end))
            emit_items(body)
            out += ['    jmp     %s' % top,
                    '%s:' % end]
            return
        out.append('    /* do %d (line %d) */' % (count[1], line))
        end = new_lbl('dend')
        cell = count[2]
        out += ['    mov     word ptr [0x%X], 0x%X' % (cell, count[1]),
                '%s:' % top,
                '    mov     ax, [0x%X]' % cell,
                '    test    ax, ax',
                '    jz      %s' % end]
        emit_items(body)
        out += ['    mov     ax, [0x%X]' % cell,
                '    dec     ax',
                '    mov     [0x%X], ax' % cell,
                '    jmp     %s' % top,
                '%s:' % end]

    def emit_items(items):
        nonlocal out
        for it in items:
            k = it[0]
            if k == 'enc':
                out.append('    /* ---- encoding: ascii (line %d) ---- */'
                           % it[2])
                continue
            if k == 'dev':
                out.append('    /* ---- device: %s (line %d) ---- */'
                           % (it[1], it[2]))
                continue
            if k == 'if':
                emit_if(it[1], it[2], it[3])
                continue
            if k == 'do':
                emit_do(it[1], it[2], it[3])
                continue
            emit_stmt(it[1], it[2], it[3])
    # --- точка входа: main-блок, выполняется сразу после загрузки ---
    main_blk = [b for b in blocks if b['main']][0]
    out.append('    /* ---- entry point: main block "%s" (line %d) ---- */'
               % (main_blk['name'], main_blk['line']))
    emit_items(main_blk['items'])
    out += ['',
            '    /* end of program */',
            '.Lhang:',
            '    hlt',
            '    jmp     .Lhang']
    # --- остальные блоки: подпрограммы (вход только через call) ---
    for blk in blocks:
        if blk['main']:
            continue
        out += ['.Lb_%s:' % blk['name'],
                '    /* ---- block "%s" (line %d) ---- */'
                % (blk['name'], blk['line'])]
        emit_items(blk['items'])
        out += ['    ret',
                '']
    # --- вспомогательные подпрограммы ---
    # клавиатура: BIOS int 0x16 (AH=01 — есть ли клавиша, AH=00 — взять).
    # Пока клавиша не нажата, крутимся через hlt.
    if needs['wfkey']:
        out += ['.Lrt_wfkey:',
                '    push    ax',
                '.Lrt_wfkey_wait:',
                '    hlt',
                '    mov     ah, 1',
                '    int     0x16',
                '    jz      .Lrt_wfkey_wait',
                '    mov     ah, 0',
                '    int     0x16',
                '    mov     [0x%X], al' % LASTKEY,
                '    pop     ax',
                '    ret',
                '']
    if needs['getline']:
        # ввод строки: символы идут в буфер 0x7200, Enter завершает,
        # Backspace стирает; длина — байт 0x72FF, в конце записывается 0.
        # dyn=1 (байт DYNF): каждый символ тут же показывается на экране
        # в позиции курсора (Backspace стирает, Enter делает СНОС: эхо
        # затирается пробелами, курсор возвращается к началу ввода —
        # дальше memw + vidwrite сами печатают текст куда нужно).
        out += ['.Lrt_getline:',
                '    push    ax',
                '    push    cx',
                '    push    di']
        if needs['dyn']:
            out += ['    /* remember where the echo starts (for the wipe) */',
                    '    mov     ax, [0x%X]' % CURSOR,
                    '    mov     [0x%X], ax' % GL_START]
        out += ['    mov     di, 0x%X' % STAGE_BUF,
                '    xor     cx, cx',
                '.Lrt_gl_key:',
                '    hlt',
                '    mov     ah, 1',
                '    int     0x16',
                '    jz      .Lrt_gl_key',
                '    push    cx',
                '    push    di',
                '    mov     ah, 0',
                '    int     0x16',
                '    pop     di',
                '    pop     cx',
                '    cmp     al, 13',
                '    je      .Lrt_gl_done',
                '    cmp     al, 8',
                '    je      .Lrt_gl_bs',
                '    test    al, al',
                '    jz      .Lrt_gl_key',
                '    cmp     al, 0xE0',
                '    je      .Lrt_gl_key',
                '    cmp     al, 32',
                '    jb      .Lrt_gl_key',
                '    cmp     cx, 254',
                '    jae     .Lrt_gl_key',
                '    mov     [di], al',
                '    inc     di',
                '    inc     cx']
        if needs['dyn']:
            out += ['    cmp     byte ptr [0x%X], 0' % DYNF,
                    '    je      .Lrt_gl_noe',
                    '    call    .Lrt_putc',
                    '.Lrt_gl_noe:',
                    '    jmp     .Lrt_gl_key']
        else:
            out.append('    jmp     .Lrt_gl_key')
        out += ['.Lrt_gl_bs:',
                '    jcxz    .Lrt_gl_key',
                '    dec     di',
                '    dec     cx']
        if needs['dyn']:
            out += ['    cmp     byte ptr [0x%X], 0' % DYNF,
                    '    je      .Lrt_gl_nobs',
                    '    call    .Lrt_bser',
                    '.Lrt_gl_nobs:',
                    '    jmp     .Lrt_gl_key']
        else:
            out.append('    jmp     .Lrt_gl_key')
        out += ['.Lrt_gl_done:']
        if needs['dyn']:
            out += ['    /* Enter: wipe the typed line (echo) off screen */',
                    '    cmp     byte ptr [0x%X], 0' % DYNF,
                    '    je      .Lrt_gl_done1',
                    '    call    .Lrt_gl_wipe',
                    '.Lrt_gl_done1:']
        out += ['    mov     byte ptr [di], 0',
                '    mov     [0x%X], cl' % STAGE_LEN,
                '    pop     di',
                '    pop     cx',
                '    pop     ax',
                '    ret',
                '']
        if needs['dyn']:
            out += ['.Lrt_gl_wipe:',
                    '    /* wipe the typed line: GL_START..[CURSOR] filled',
                    '       with spaces, then [CURSOR] = GL_START */',
                    '    push    ax',
                    '    push    cx',
                    '    push    di',
                    '    push    es',
                    '    mov     di, [0x%X]' % GL_START,
                    '    mov     cx, [0x%X]' % CURSOR,
                    '    sub     cx, di',
                    '    jc      .Lrt_gl_wipe_out',
                    '    shr     cx, 1',
                    '    mov     ax, 0xB800',
                    '    mov     es, ax',
                    '    mov     ax, 0x0720',
                    '    rep     stosw',
                    '    mov     ax, [0x%X]' % GL_START,
                    '    mov     [0x%X], ax' % CURSOR,
                    '.Lrt_gl_wipe_out:',
                    '    pop     es',
                    '    pop     di',
                    '    pop     cx',
                    '    pop     ax',
                    '    ret',
                    '']
    if needs['cursor']:
        # ---- вывод текста с курсором: текст не наслаивается ----
        # .Lrt_puts: печатает ASCIIZ-строку, байт 10 (\n) = снос строки.
        # Вход: ds:si — строка, di — смещение старта в видеостранице
        # 0xB8000 (для печати с курсора — [CURSOR]). Выход: [CURSOR] =
        # позиция после текста. Если экран кончился — листается вверх.
        out += ['.Lrt_puts:',
                '    push    ax',
                '    push    di',
                '    push    es',
                '    mov     ax, 0xB800',
                '    mov     es, ax',
                '    mov     ah, 0x07',
                '.Lrt_puts_lp:',
                '    lodsb',
                '    test    al, al',
                '    jz      .Lrt_puts_done',
                '    cmp     al, 10',
                '    je      .Lrt_puts_nl',
                '    stosw',
                '    cmp     di, 4000',
                '    jb      .Lrt_puts_lp',
                '    jne     .Lrt_puts_lp',
                '    /* di == 4000 exactly: screen is over - scroll */',
                '    call    .Lrt_scroll',
                '    jmp     .Lrt_puts_lp',
                '.Lrt_puts_nl:',
                '    call    .Lrt_nl',
                '    jmp     .Lrt_puts_lp',
                '.Lrt_puts_done:',
                '    cmp     di, 4000',
                '    jae     .Lrt_puts_done1',
                '    mov     [0x%X], di' % CURSOR,
                '.Lrt_puts_done1:',
                '    pop     es',
                '    pop     di',
                '    pop     ax',
                '    ret',
                '',
                '.Lrt_nl:',
                '    /* \\n: di -> start of next row (stores cursor) */',
                '    push    ax',
                '    push    bx',
                '    push    dx',
                '    mov     ax, di',
                '    xor     dx, dx',
                '    mov     bx, 160',
                '    div     bx',
                '    inc     ax',
                '    mul     bx',
                '    mov     di, ax',
                '    cmp     di, 4000',
                '    jb      .Lrt_nl1',
                '    jne     .Lrt_nl2',
                '    call    .Lrt_scroll',
                '.Lrt_nl1:',
                '    mov     [0x%X], di' % CURSOR,
                '.Lrt_nl2:',
                '    pop     dx',
                '    pop     bx',
                '    pop     ax',
                '    ret',
                '',
                '.Lrt_scroll:',
                '    /* scroll screen up one row; di = 0x0F00 (bottom) */',
                '    push    ax',
                '    push    cx',
                '    push    si',
                '    push    ds',
                '    mov     ax, 0xB800',
                '    mov     ds, ax',
                '    mov     es, ax',
                '    mov     si, 160',
                '    xor     di, di',
                '    mov     cx, 1920',
                '    rep     movsw',
                '    mov     cx, 80',
                '    xor     ax, ax',
                '    rep     stosw',
                '    mov     di, 0x0F00',
                '    /* rep stosw pushed di to 4000 - back to bottom */',
                '    pop     ds',
                '    pop     si',
                '    pop     cx',
                '    pop     ax',
                '    ret',
                '']
    if needs['dyn']:
        # ---- эхо ввода wfkeyinp dyn ----
        out += ['.Lrt_putc:',
                '    /* al = char: echo it at the cursor (keeps di) */',
                '    push    ax',
                '    push    di',
                '    mov     ah, 0',
                '    push    ax          /* one-char string: char, 0 */',
                '    mov     si, sp',
                '    mov     di, [0x%X]' % CURSOR,
                '    call    .Lrt_puts',
                '    pop     ax',
                '    pop     di',
                '    pop     ax',
                '    ret',
                '',
                '.Lrt_bser:',
                '    /* on-screen Backspace: erase char left of cursor */',
                '    push    ax',
                '    push    di',
                '    push    es',
                '    mov     di, [0x%X]' % CURSOR,
                '    test    di, di',
                '    jz      .Lrt_bser_out',
                '    mov     ax, di',
                '    xor     dx, dx',
                '    mov     bx, 160',
                '    div     bx',
                '    test    dx, dx',
                '    jz      .Lrt_bser_out',
                '    sub     di, 2',
                '    mov     ax, 0xB800',
                '    mov     es, ax',
                '    mov     ax, 0x0720',
                '    stosw',
                '    sub     di, 2',
                '    mov     [0x%X], di' % CURSOR,
                '.Lrt_bser_out:',
                '    pop     es',
                '    pop     di',
                '    pop     ax',
                '    ret',
                '']
    if lits:
        out.append('')
        for lbl, s in lits:
            # .asciz — строка с нулём на конце (цикл вывода ищет 0)
            out += ['%s:' % lbl, '    .asciz "%s"' % sys_asm_escape(s)]
    return '\n'.join(out) + '\n'


# ----------------------------------------------------------------------
# Ступень 1: загрузочный сектор. Шаблон, %(sectors)d — число секторов
# кернела (ceil(размер/512)). Читает кернел с дискеты (INT 0x13,
# начиная с CHS 0/0/2, с переходами сектор->головка->цилиндр) в
# 0x0000:0x7E00 и прыгает туда. Позиционно-независим (одни относительные
# прыжки и абсолютная пара сегмент:смещение 0x0000:0x7E00).
# ----------------------------------------------------------------------
BOOT_ASM_TMPL = """\
/* Generated by xpce132.py (X+13.2 Experimental) - stage 1: BOOT. */
/* Loads the kernel (myfirstsystem.bin, %(sectors)d sector(s)) from the */
/* floppy (INT 0x13) into 0x0000:0x7E00 and jumps to it. DL = boot drive */
/* as set by the BIOS. Flat assembly: as --32 + objcopy -O binary -> */
/* 512 bytes with the 0xAA55 signature. */
.code16
.intel_syntax noprefix
.globl start
start:
    cli
    xor     ax, ax
    mov     ds, ax
    mov     es, ax
    mov     ss, ax
    mov     sp, 0x7C00
    cld
    sti
    /* load %(sectors)d sector(s); DL = boot drive (from BIOS) */
    mov     si, %(sectors)d
    mov     bx, 0x7E00              /* ES:BX -> kernel load address */
    mov     cx, 0x0002              /* CH=cylinder 0, CL=sector 2 */
    mov     dh, 0                   /* DH=head 0 */
.Lload:
    mov     ax, 0x0201              /* AH=2: read, AL=1 sector */
    int     0x13
    jnc     .Lok
    xor     ax, ax                  /* AH=0: reset disk, retry */
    int     0x13
    jmp     .Lload
.Lok:
    add     bx, 512
    inc     cl
    cmp     cl, 19                  /* sectors are 1..18 */
    jb      .Lnext
    mov     cl, 1
    inc     dh
    cmp     dh, 2                   /* heads are 0..1 */
    jb      .Lnext
    mov     dh, 0
    inc     ch                      /* next cylinder */
.Lnext:
    dec     si
    jnz     .Lload
    /* kernel is in place: transfer control to 0x0000:0x7E00 */
    jmp     0x0000:0x7E00
.Lhang:
    hlt
    jmp     .Lhang
    /* pad to 510 and write the 0xAA55 boot signature */
    .org 510
    .word 0xAA55
"""


def check_image(bin_path):
    """(ok, size): ok == образ ровно 512 байт с подписью 0xAA55 в конце."""
    try:
        with open(bin_path, 'rb') as f:
            data = f.read()
    except OSError:
        return False, -1
    ok = len(data) == 512 and data[510:512] == b'\x55\xaa'
    return ok, len(data)


def sys_build(src_path, out_dir, kasm_path, img_path):
    """Собирает двухступенчатый образ дискеты. Порядок важен:
    1) кернел: myfirstsystem.asm -> as --32 -> objcopy -O binary ->
       myfirstsystem.bin (проверка размера: 0 < размер <= 32 КБ, кернел
       грузится в 0x7E00..0xFE00);
    2) boot.asm генерируется из BOOT_ASM_TMPL с числом секторов кернела
       -> boot.bin (ровно 512 байт, подпись 0xAA55 на 510-м);
    3) <имя>.img = boot.bin + myfirstsystem.bin + паддинг до 1.44 МБ.
    Сборка везде одинаковая: as + objcopy -O binary, БЕЗ ld — один и тот
    же путь на Linux и Windows/MinGW. Возвращает (размер_кернела,
    число_секторов)."""
    import shutil
    import tempfile
    tmpd = tempfile.mkdtemp(prefix='xpce132_')
    errors = []
    try:
        def run_tool(cmd):
            try:
                return subprocess.run(cmd, capture_output=True, text=True)
            except FileNotFoundError:
                return None

        def assemble(src_asm, o_path, what):
            r = run_tool(['as', '--32', src_asm, '-o', o_path])
            if r is None:
                errors.append('as: not found (install gcc/binutils, '
                              'on Windows: MinGW-w64)')
                return False
            if r.returncode != 0:
                errors.append('as (%s) failed:\n%s'
                              % (what, (r.stderr or '').strip()))
                return False
            return True

        def to_binary(o_path, bin_path, what, ok_check):
            for extra in (['-j', '.text'], []):
                r = run_tool(['objcopy', '-O', 'binary'] + extra
                             + [o_path, bin_path])
                if r is None:
                    errors.append('objcopy: not found (install binutils — '
                                  'входит в MinGW-w64)')
                    return False
                if r.returncode != 0:
                    errors.append('objcopy (%s) failed:\n%s'
                                  % (what, (r.stderr or '').strip()))
                    continue
                if ok_check(bin_path):
                    return True
            return False

        # ---- 1) кернел (ступень 2) ----
        k_o = os.path.join(tmpd, 'myfirstsystem.o')
        k_bin = os.path.join(out_dir, 'myfirstsystem.bin')
        if not assemble(kasm_path, k_o, 'kernel'):
            raise XPlusError(src_path, 0,
                             'cannot build the kernel:\n%s'
                             % '\n'.join(errors))

        def k_ok(p):
            try:
                return 0 < os.path.getsize(p) <= KERNEL_MAX
            except OSError:
                return False

        if not to_binary(k_o, k_bin, 'kernel', k_ok):
            raise XPlusError(src_path, 0,
                             'cannot build the kernel binary:\n%s'
                             % '\n'.join(errors))
        ksize = os.path.getsize(k_bin)
        if ksize > KERNEL_MAX:
            raise XPlusError(src_path, 0,
                             'kernel too big: %d bytes (max %d: boot.asm '
                             'loads it at 0x7E00, up to 0xFE00)'
                             % (ksize, KERNEL_MAX))
        # ---- 2) boot-сектор (ступень 1) ----
        sectors = (ksize + 511) // 512
        boot_asm_path = os.path.join(out_dir, 'boot.asm')
        with open(boot_asm_path, 'w', encoding='ascii',
                  errors='strict') as f:
            f.write(BOOT_ASM_TMPL % {'sectors': sectors})
        b_o = os.path.join(tmpd, 'boot.o')
        b_bin = os.path.join(out_dir, 'boot.bin')
        if not assemble(boot_asm_path, b_o, 'boot'):
            raise XPlusError(src_path, 0,
                             'cannot build the boot sector:\n%s'
                             % '\n'.join(errors))
        if not to_binary(b_o, b_bin, 'boot', lambda p: check_image(p)[0]):
            raise XPlusError(src_path, 0,
                             'cannot build the boot sector:\n%s'
                             % '\n'.join(errors))
        # ---- 3) образ дискеты 1.44 МБ ----
        with open(b_bin, 'rb') as f:
            boot_data = f.read()
        with open(k_bin, 'rb') as f:
            kdata = f.read()
        with open(img_path, 'wb') as f:
            f.write(boot_data)
            f.write(kdata)
            f.write(b'\x00' * (1474560 - 512 - len(kdata)))
        return ksize, sectors
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)


def detect_sysmode(src):
    for raw in src.split('\n'):
        s = sys_strip_comment(raw).strip()
        if not s:
            continue
        return bool(re.match(r'Inject\s+SysMode\b', s))
    return False


def precheck_sysmode_mix(src, fname):
    """Inject X+ + команды SysMode -> понятная ошибка (смешивать нельзя)."""
    for ln, raw in enumerate(src.split('\n'), 1):
        code = sys_strip_comment(raw)
        code = re.sub(r'"[^"]*"', '""', code)     # убрать строковые литералы
        m = re.search(r'\b(vidwrite|vidread|memw|memr|wfkey|wfkeyinp|'
                      r'call)\b', code)
        if m:
            raise XPlusError(fname, ln,
                             "'%s' is a SysMode command (X+13.2): "
                             "the program must start with 'Inject SysMode'. "
                             'SysMode cannot be combined with the X+ library '
                             'yet.' % m.group(1))


def sys_compile(src_path, src):
    base = os.path.splitext(src_path)[0]
    out_dir = os.path.dirname(os.path.abspath(src_path))
    prog = sys_parse(src, src_path)
    kasm = sys_codegen(prog, src_path)
    kasm_path = os.path.join(out_dir, 'myfirstsystem.asm')
    with open(kasm_path, 'w', encoding='ascii', errors='strict') as f:
        f.write(kasm)
    img_path = base + '.img'
    ksize, sectors = sys_build(src_path, out_dir, kasm_path, img_path)
    sys.stdout.write(
        'X+13.2 Experimental: two-stage build\n'
        'entry point: main block "%s"\n'
        'boot.asm: stage 1, boot loader (loads %d sector(s) via INT 0x13)\n'
        'myfirstsystem.asm: stage 2, kernel (%d bytes, loaded at 0x7E00)\n'
        'boot.bin: 512 bytes, signature 0xAA55\n'
        'myfirstsystem.bin: kernel binary\n'
        '%s: 1.44 MB floppy image (boot + kernel)\n'
        'run: qemu-system-i386 -fda %s\n'
        % (prog['entry'], sectors, ksize, os.path.basename(img_path),
           os.path.basename(img_path)))
    return 0


# --------------------------------------------------------------------------
# Сборка и запуск
# --------------------------------------------------------------------------

def read_source(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except OSError as e:
        raise XPlusError(path, 0, 'cannot read file: %s' % (e.strerror or e))
    # utf-8 (с BOM или без), запасной вариант — cp1251
    try:
        return data.decode('utf-8-sig'), 'utf-8'
    except UnicodeDecodeError:
        return data.decode('cp1251'), 'cp1251'


def link(s_path, exe_path, target, src_path):
    if target == 'win':
        cmd = ['gcc', '-nostdlib', '-Wl,-e,main', '-o', exe_path,
               s_path, '-lkernel32']
    else:
        cmd = ['gcc', '-nostdlib', '-o', exe_path, s_path]
    try:
        r = subprocess.run(cmd)
    except FileNotFoundError:
        raise XPlusError(src_path, 0,
                         'gcc not found: install MinGW-w64 and add it to PATH')
    if r.returncode != 0:
        raise XPlusError(src_path, 0,
                         'linker failed (gcc exit code %d)' % r.returncode)


def compile_source(src_path, no_run, target):
    src, codec = read_source(src_path)
    if detect_sysmode(src):
        if target != 'win':
            sys.stderr.write('xpce132: note: --target is ignored in SysMode '
                             '(16-bit real mode boot sector)\n')
        return sys_compile(src_path, src)
    precheck_sysmode_mix(src, src_path)
    toks = lex(src, src_path)
    prog = Parser(toks, src_path).parse_program()
    validate(prog, src_path)
    asm = Codegen(prog, target, codec).generate()
    base = os.path.splitext(src_path)[0]
    s_path = base + '.s'
    with open(s_path, 'w', encoding='ascii', errors='strict') as f:
        f.write(asm)          # в .s только ASCII (литералы — байтовыми .byte)
    exe_path = base + ('.exe' if target == 'win' else '')
    link(s_path, exe_path, target, src_path)
    if no_run:
        return 0
    r = subprocess.run([os.path.abspath(exe_path)])
    return r.returncode


USAGE = """
usage: python xpce132.py program.xp [--no-run] [--target win|linux]
X+ Compiler Experimental 13.2 — X+13.2 Experimental

Inject SysMode — system mode: 16-bit real mode x86, TWO-STAGE BOOT, the
  kernel is no longer limited to one sector:
  boot.asm          — stage 1: boot sector (512 bytes, 0xAA55); loads the
                      kernel from floppy sectors 2..N (INT 0x13) into
                      0x0000:0x7E00 and jumps to it;
  myfirstsystem.asm — stage 2: the kernel (program + runtime), loaded
                      at 0x7E00, size limit 32 KB;
  boot.bin, myfirstsystem.bin — stage binaries;
  <name>.img        — 1.44 MB floppy image (boot + kernel).
  Build chain: as --32 + objcopy -O binary, no ld (Linux and Windows/MinGW).
  run: qemu-system-i386 -fda <name>.img
  Commands: using, vidwrite, vidread, memw, memr, wfkey, wfkeyinp, call,
  var, set, if/else, do.
  Blocks: every block starts with using name "X" (entry point:
    using name "X" main); 3 blank lines separate blocks (and must
    follow Inject SysMode). Exactly ONE block is marked main — it is
    the entry point and runs right after boot. A block sees only the
    blocks defined ABOVE it (help-blocks go above main) and is called
    with: call X (compiler adds ret).
  NO 'end' in system mode: bodies are built with TAB indentation
    (1 tab = 1 level). An if/do body is indented one tab deeper
    and ends when the indentation returns; else sits at the same tab
    level as its if.
  Variables: var num "x" — a 16-bit unsigned word (area 0x7000-0x71FF,
    global; declare at the top level, before/between blocks).
    set x = expression  — + - * / % and parentheses; unsigned 0..65535,
    division by zero yields 0. Values are DECIMAL numbers; 0x-hex means
    READ A MEMORY CELL (word), so if 0x3000 == 0x5000 compares two
    cells. byte 0xADDR reads one byte (key code: if byte 0x7418 == 97),
    word 0xADDR is the explicit word form. Conditions take one operand
    per side; full expressions live in set.
  Conditions: if A == B / != / < / > / <= / >= (unsigned), else,
    else if (else at the if's tab level). Loops (there is NO 'while'):
    do N (N times), do true (forever), do A == B (repeat while the
    condition is true; check before each pass).
  vidwrite forms: vidwrite VIDEO_ADDR "text" | vidwrite SRC VIDEO_ADDR |
    vidwrite VIDEO_ADDR cls. A VIDEO ADDRESS IS REQUIRED (svga/xga may
    come later). Bare 0xB8000 means "the screen" — print AT THE CURSOR
    (text never piles up); 0xB8000+offset prints at that exact address.
    \n moves to the next line; the screen scrolls up when full;
    vidwrite VIDEO_ADDR cls wipes the 0xB8000-0xBFFFF window.
  Devices (main block only, declare before use):
    using device ps2keyb  — enables wfkey / wfkeyinp.
  wfkey — wait for a key press (its ASCII goes to byte 0x7418).
  wfkeyinp ADDR [dyn] — wait for a line of input. The text is STAGED,
    not written yet. Confirm the write on the next line with: memw
    ADDR (the same address). The word dyn turns on live echo (Backspace
    erases; Enter finalizes the input and WIPES the typed line — the
    cursor returns to where the input started).
  Scratch buffer 0x7300 (vidread/memr), input staging 0x7200-0x72FF,
  variables and do-counters 0x7000-0x71FF. User data goes into free
    memory BELOW 0x7E00 (e.g. 0x3000): the kernel itself lives at
    0x7E00-0xFE00, writing there is a compile-time error.
  SysMode cannot be combined with the X+ library yet.

Inject X+ — classic mode, compatible with X+12 (and X+10-style ends):
  --target win     x86-64 Windows PE via gcc + kernel32, no CRT (default)
  --target linux   ELF test build (for checking the compiler on Linux)
  --no-run         compile and link only, do not run the program
"""


def main(argv):
    args = argv[1:]
    no_run = False
    target = 'win'
    src = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--no-run':
            no_run = True
        elif a == '--target':
            i += 1
            if i >= len(args):
                sys.stderr.write('xpce132: error: --target needs a value\n')
                return 2
            target = args[i]
        elif a.startswith('--target='):
            target = a.split('=', 1)[1]
        elif a in ('-h', '--help'):
            sys.stdout.write(USAGE)
            return 0
        elif a.startswith('--'):
            sys.stderr.write('xpce132: error: unknown option %s\n' % a)
            return 2
        else:
            if src is not None:
                sys.stderr.write('xpce132: error: only one source file is allowed\n')
                return 2
            src = a
        i += 1
    if src is None:
        sys.stderr.write(USAGE)
        return 2
    if target not in ('win', 'linux'):
        sys.stderr.write('xpce132: error: unknown target %r (win or linux)\n' % target)
        return 2
    try:
        return compile_source(src, no_run, target)
    except XPlusError as e:
        sys.stderr.write(str(e) + '\n')
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
