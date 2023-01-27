# -----------------------------------------------------------------------------
# calc.py
#
# A simple calculator with variables -- all in one file.
# -----------------------------------------------------------------------------
import copy

keywords = {
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'program': 'PROGRAM',
    'var': 'VAR',
    'begin': 'BEGIN',
    'end': 'END',
    'do': 'DO',
    'int': 'INT',
    'real': 'REAL',
    'print': 'PRINT',
    'switch': 'SWITCH',
    'of': 'OF',
    'done': 'DONE',
    'default': 'DEFAULT',
    'mod': 'MOD',
    'or': 'OR',
    'and': 'AND',
    'not': 'NOT'
}

tokens = [
             'TRUE', 'FALSE',
             'LPAREN', 'RPAREN',
             'PLUS',
             'MINUS',
             'TIMES',
             'DIVIDE',
             'INTEGER',
             'ID',
             'EQUAL',
             'LESS',
             'LESSEQ',
             'MORE',
             'MOREEQ',
             'NOTEQ',
             'SEM',
             'COLON',
             'COMMA',
             'ASSIGN',
             'UMINUS'
         ] + list(keywords.values())


# Tokens
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = keywords.get(t.value, 'ID')  # Check for reserved words
    return t


def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t


t_LPAREN = r'\('
t_RPAREN = r'\)'
t_TRUE = r'true'
t_FALSE = r'false'
t_PLUS = r'\+'
t_MINUS = r'\-'
t_DIVIDE = r'\/'
t_TIMES = r'\*'
t_EQUAL = r'\='
t_LESS = r'\<'
t_LESSEQ = r'\<='
t_NOTEQ = r'\<>'
t_MORE = r'\>'
t_MOREEQ = r'\>='
t_SEM = r'\;'
t_COLON = r'\:'
t_COMMA = r'\,'
t_ASSIGN = r'\:='
t_UMINUS = r'\-'

# Ignored characters
t_ignore = " \t"


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Parsing rules

precedence = (
    ('right', 'OR'),
    ('right', 'AND'),
    ('right', 'NOT'),
    ('right', 'PLUS', 'MINUS'),
    ('right', 'TIMES', 'DIVIDE'),
    ('nonassoc', 'MOD'),  # Nonassociative operators
    ('right', 'UMINUS'),
)

#
# dictionary of names
names = []

quadruples = []


class Temp:
    def __init__(self):
        self.temp = 0
        self.temp_list = []

    def newTemp(self):
        self.temp += 1
        self.temp_list.append('temp' + str(self.temp))
        return 'temp' + str(self.temp)


glob_temp = Temp()


def backpatch(l: list, i: int):
    for line_number in l:
        prv_tuple = quadruples[line_number-1 ]
        new_tuple = (prv_tuple[0], i)
        quadruples[line_number - 1] = new_tuple


def nextinstr():
    return len(quadruples) + 1


def p_marker(t):
    'marker : '
    t[0] = nextinstr()


class E:
    def __init__(self, t, f):
        self.truelist = t
        self.falselist = f
        self.addr = ""


def p_expression_or(t):
    """expression : expression OR marker expression"""
    backpatch(t[1].falselist, t[3])
    truelist = t[1].truelist + t[4].truelist
    falselist = t[4].falselist
    t[0] = E(truelist, falselist)


def p_expression_and(t):
    """expression : expression AND marker expression"""
    backpatch(t[1].truelist, t[3])
    truelist = t[4].truelist
    falselist = t[4].falselist + t[1].falselist
    t[0] = E(truelist, falselist)


def p_expression_unot(t):
    """expression : NOT expression"""
    t[0] = E(t[2].falselist, t[2].truelist)


def p_expression_group(t):
    """expression : LPAREN expression RPAREN"""
    t[0] = copy.deepcopy(t[2])
    # t[0] = E([], [])
    # t[0].addr = t[2]
    # quadruples.append(('(' + str(t[2].addr) + ')'))


def p_expression_true(t):
    """expression : TRUE"""
    t[0] = E([nextinstr()], [])
    quadruples.append(("goto",))


def p_expression_false(t):
    """expression : FALSE"""
    t[0] = E([], [nextinstr()])
    quadruples.append(("goto",))


# our code
def p_expression_integer(t):
    """expression : INTEGER"""
    t[0] = E([], [])
    t[0].addr = t[1]


def p_expression_id(t):
    """expression : ID"""
    t[0] = E([], [])
    t[0].addr = t[1]
    if(t[1] not in names):
        names.append(t[1])


# def p_expression_real(t):
#     """expression : REAL"""
#     t[0] = t[1]


def p_expression_plus(t):
    """expression : expression PLUS expression"""
    t[0] = E([], [])
    t[0].addr = glob_temp.newTemp()
    quadruples.append((t[0].addr + '=' + str(t[1].addr) + '+' + str(t[3].addr),))


def p_expression_minus(t):
    """expression : expression MINUS expression"""
    t[0] = E([], [])
    t[0].addr = glob_temp.newTemp()
    quadruples.append((t[0].addr + '=' + str(t[1].addr) + '-' + str(t[3].addr),))


def p_expression_uminus(t):
    """expression : MINUS expression %prec UMINUS"""
    t[0] = E([], [])
    t[0].addr = "-" + str(t[2].addr)


def p_expression_times(t):
    """expression : expression TIMES expression"""
    t[0] = E([], [])
    t[0].addr = glob_temp.newTemp()
    quadruples.append((t[0].addr + '=' + str(t[1].addr) + '*' + str(t[3].addr)))


def p_expression_div(t):
    """expression : expression DIVIDE expression"""
    t[0] = E([], [])
    t[0].addr = glob_temp.newTemp()
    quadruples.append((t[0].addr + '=' + str(t[1].addr) + '/' + str(t[3].addr),))


def p_expression_mod(t):
    """expression : expression MOD expression"""
    t[0] = E([], [])
    t[0].addr = glob_temp.newTemp()
    quadruples.append((t[0].addr + '=' + str(t[1].addr) + '%' + str(t[3].addr),))


def p_expression_relop(t):
    """expression : expression LESS expression
                       | expression LESSEQ expression
                  | expression NOTEQ expression
                  | expression EQUAL expression
                       | expression MORE expression
                       | expression MOREEQ expression"""
    t[0] = E([nextinstr()], [nextinstr() + 1])
    if t[2] == '<':
        quadruples.append(('if (' + str(t[1].addr) + '<' + str(t[3].addr) + ")" + ' goto',))
    if t[2] == '<=':
        quadruples.append(('if (' + str(t[1].addr) + '<=' + str(t[3].addr) + ")" + ' goto',))
    if t[2] == '<>':
        quadruples.append(('if (' + str(t[1].addr) + '<>' + str(t[3].addr) + ")" + ' goto',))
    if t[2] == '=':
        quadruples.append(('if (' + str(t[1].addr) + '=' + str(t[3].addr) + ")" + ' goto',))
    if t[2] == '>':
        quadruples.append(('if (' + str(t[1].addr) + '>' + str(t[3].addr) + ")" + ' goto',))
    if t[2] == '>=':
        quadruples.append(('if ( ' + str(t[1].addr) + '>=' + str(t[3].addr) + ")" + ' goto',))

    t[0].addr = str(t[1]) + t[2] + str(t[3])
    quadruples.append(('goto',))


def p_error(t):
    print("Syntax error at '%s'" % t.value)


# class Cons:
#     def __init__(self, t, f):
#         self.truelist = t
#         self.falselist = f
#
#
# def p_cons_integer(t):
#     """cons : INTEGER"""
#     t[0] = t[1]
#
#
# # def p_cons_real(t):
# #     """cons : REAL"""
# #     t[0] = t[1]
#
#
# class ConsList:
#     def __init__(self, t, f):
#         self.truelist = t
#         self.falselist = f
#
#
# def p_consList_cons(t):
#     """consList : cons"""
#     t[0] = [t[1]]
#
#
# def p_consList_conscons(t):
#     """consList : consList COMMA cons"""
#     t[0] = t[1] + t[3]


class N:
    def __init__(self, nextlist):
        self.nextlist = nextlist
        quadruples.append(('goto',))


def p_N(t):
    'N : '
    t[0] = N([])



class Statement:
    def __init__(self, nextlist):
        self.nextlist = nextlist


def p_statement_assign(t):
    """statement : ID ASSIGN expression"""
    quadruples.append((str(t[1]) + '=' + str(t[3].addr),))
    t[0] = Statement([])
    if (t[1] not in names):
        names.append(t[1])


def p_statement_ifthen(t):
    """statement : IF expression THEN marker statement"""
    backpatch(t[2].truelist, t[4])
    if t[5].nextlist == None:
        nextlist = t[2].falselist
    else:
        nextlist = t[2].falselist + t[5].nextlist
    t[0] = Statement(nextlist)


def p_statement_ifthenelse(t):
    """statement : IF expression THEN marker statement N ELSE marker statement"""
    backpatch(t[2].truelist, t[4])
    backpatch(t[2].falselist, t[8])
    temp = t[5].nextlist + t[6].nextlist
    nextlist = temp + t[9].nextlist
    t[0] = Statement(nextlist)


def p_statement_while(t):
    """statement : WHILE marker expression DO marker statement"""
    backpatch(t[6].nextlist, t[2])
    backpatch(t[3].truelist, t[5])
    nextlist = t[3].falselist
    t[0] = Statement(nextlist)
    quadruples.append(('goto', t[2]))


def p_statement_compound(t):
    """statement : compoundStatement"""
    t[0] = t[1]


def p_statement_print(t):
    """statement : PRINT LPAREN expression RPAREN"""
    t[3] = str(t[3])
    quadruples.append(('printf("%d\n",' + t[3].addr + ")",))


class StatementList:
    def __init__(self, nextlist):
        self.nextlist = nextlist


def p_statementList_stmliststm(t):
    """statementList : statementList SEM marker statement"""
    backpatch(t[1].nextlist, t[3])
    nextlist = t[4].nextlist
    t[0] = StatementList(nextlist)


def p_statementList_stm(t):
    """statementList : statement"""
    nextlist = t[1].nextlist
    t[0] = StatementList(nextlist)


class CompoundStatement:
    def __init__(self, nextlist):
        self.nextlist = nextlist


def p_compoundStatement_beginend(t):
    """compoundStatement : BEGIN statementList END"""
    nextlist = t[2].nextlist
    t[0] = CompoundStatement(nextlist)
    quadruples.append('endblock')


def p_type_int(t):
    """type : INT"""
    t[0] = t[1]


# def p_type_real(t):
#     """type : REAL"""
#     t[0] = t[1]


def p_idList_id(t):
    """idList : ID"""
    t[0] = [t[1]]
    if (t[1] not in names):
        names.append(t[1])


def p_idList_idid(t):
    """idList : idList COMMA ID"""
    t[0] = t[1] + t[3]
    if (t[1] not in names):
        names.append(t[1])


def p_declarationList_type(t):
    """declarationList : idList COLON type"""
    pass


def p_declarationList_decidtype(t):
    """declarationList : declarationList SEM idList COLON type"""
    pass


def p_declarations_var(t):
    """declarations : VAR declarationList"""
    pass


def p_declarations_empty(t):
    """declarations : """
    pass


def p_program(t):
    """program : PROGRAM ID declarations compoundStatement"""
    if (t[2] not in names):
        names.append(t[2])


# Build the lexer
import ply.lex as lex
lexer = lex.lex()

# string = 'if x<y and y<z then y:=3'
# lexer.input(string)
# for tok in lexer:
#     print(tok)
import ply.yacc as yacc


parser = yacc.yacc(start='statement')

# while True:
# try:
#     s = input('calc > ')  # Use raw_input on Python 2
# except EOFError:
#     print("Error")
# r = parser.parse(s)
# print(quadruples)
# print(r.truelist, r.falselist)
# quadruples.clear()
# s = input()
# parser.parse(s)
# print(quadruples)

# read from file

file1 = open('test.txt', 'r')
Lines = file1.readlines()
for line in Lines:
    s = line.strip()
    parser.parse(s)

# write to c file

with open('output.c', 'a') as the_file:
    str1 = '#include <stdio.h>'
    the_file.write(str1 + "\n")
    print(str1)
    if len(names) != 0:
        str_names = 'int '
        for i in range(len(names)):
            if(i!=len(names)-1):
                str_names += names[i] + ", "
            else:str_names += names[i] + "; "
    print(str_names)
    the_file.write(str_names + "\n")

    if len(glob_temp.temp_list) != 0:

        str_temp = 'int '
        for j in range(len(glob_temp.temp_list)):
            if(j!=len(glob_temp.temp_list)-1):
                str_temp += glob_temp.temp_list[j] + ", "
            else:
                str_temp += glob_temp.temp_list[j] + "; "

        print(str_temp)
        the_file.write(str_temp + "\n")

    str_main = 'int main ()'
    print(str_main)
    the_file.write(str_main + "\n")

    str_start = '{'
    print(str_start)
    the_file.write(str_start + "\n")

    count = 1
    for q in quadruples:

        if (len(q) == 2):

            if (count == 1):
                str_q = str(q[0]) + " " + "label_" + str(q[1]) + ";"
                print(str_q)
                the_file.write(str_q + "\n")
                count += 1
            else:
                str_q = str("label_" + str(count)) + ": " + str(q[0]) + " " + "label_" + str(q[1]) + ";"
                print(str_q)
                the_file.write(str_q + "\n")
                count += 1

        elif(len(q)==1):

            if (count == 1):
                str_q = str(q[0]) + ";"
                print(str_q)
                the_file.write(str_q + "\n")
                count += 1
            else:
                str_q = str("label_" + str(count)) + ": " + str(q[0]) + ";"
                print(str_q)
                the_file.write(str_q + "\n")
                count += 1

    str_end = '}'
    print(str_end)
    the_file.write(str_end + "\n")
