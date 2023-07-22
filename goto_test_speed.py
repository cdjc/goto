import random
import timeit
from enum import Enum

from statemachine import StateMachine, State

from goto import goto


class FPSum(StateMachine):
    '''
    floating point simple expression recogniser
    '''
    s_start = State(initial=True, name='Start')
    s_digits1 = State(name='Digits1')
    s_dot = State(name="Dot")
    s_digits2 = State(name="Digits2")
    s_exp = State(name="Exp")
    s_expsign = State(name="Sign")
    s_expdigits = State(name="ExpDigits")
    s_done = State()

    digit = (s_start.to(s_digits1)
             | s_digits1.to(s_digits1)
             | s_dot.to(s_digits2)
             | s_digits2.to(s_digits2)
             | s_expsign.to(s_expdigits)
             | s_expdigits.to(s_expdigits))
    exp = (s_digits2.to(s_exp)
           | s_digits1.to(s_exp))
    dot = s_digits1.to(s_dot)
    minus = s_exp.to(s_expsign)
    plus = (s_exp.to(s_expsign)
            | s_digits1.to(s_start)
            | s_digits2.to(s_start)
            | s_expdigits.to(s_start))
    done = (s_digits1.to(s_done)
            | s_digits2.to(s_done)
            | s_expdigits.to(s_done))


def run_import_statemachine(s):
    sm = FPSum()
    # sm._graph().write_png('fp_sum_expr.png')

    digit = 'digit'
    exp = 'exp'
    dot = 'dot'
    plus = 'plus'
    minus = 'minus'
    done = 'done'

    event = {
        '0': digit,
        '1': digit,
        '2': digit,
        '3': digit,
        '4': digit,
        '5': digit,
        '6': digit,
        '7': digit,
        '8': digit,
        '9': digit,
        '.': dot,
        '-': minus,
        '+': plus,
        'e': exp,
        '$': done
    }

    # count = 0
    try:
        for c in s:
            sm.send(event[c])
            # count += 1
            # print(sm.current_state)
    except Exception as e:
        print(e)
        return False
    return sm.current_state.id == 's_done'


def run_match(s):
    class States(Enum):
        start = 1
        digits1 = 2
        dot = 3
        digits2 = 4
        exp = 5
        expsign = 6
        expdigits = 7
        done = 8

    count = 0
    state = States.start
    good = True
    for c in s:
        match c:
            case '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '0':
                count += 1
                match state:
                    case States.start | States.digits1:
                        state = States.digits1
                    case States.dot | States.digits2:
                        state = States.digits2
                    case States.expsign | States.expdigits:
                        state = States.expdigits
                    case _:
                        good = False
                        break
            case '-':
                if state == States.exp:
                    state = States.expsign
                else:
                    good = False
                    break
            case '.':
                if state == States.digits1:
                    state = States.dot
                else:
                    good = False
                    break
            case 'e':
                if state in (States.digits2, States.digits1):
                    state = States.exp
                else:
                    good = False
                    break
            case '+':
                if state in (States.digits1, States.digits2, States.expdigits):
                    state = States.start
                elif state is States.exp:
                    state = States.expsign
                else:
                    good = False
                    break
            case '$':
                if state in (States.digits1, States.digits2, States.expdigits):
                    break
            case '_':
                good = False
                break
    if not good:
        print("Not accepted")
    return good


@goto
def run_goto(s):
    DIGITS = set('0123456789')

    i = 0
    good = True

    label.start

    if s[i] in DIGITS:
        i += 1
        goto.digits1
    elif __name__:
        return False

    label.digits1

    while s[i] in DIGITS:
        i += 1
    if s[i] == '+':
        i += 1
        goto.start
    elif s[i] == '.':
        i += 1
        goto.dot
    elif s[i] == 'e':
        i += 1
        goto.exp
    elif s[i] == '$':
        return True
    elif __name__:
        return False

    label.dot

    # drop through to .digits2

    label.digits2

    while s[i] in DIGITS:
        i += 1
    if s[i] == '+':
        i += 1
        goto.start
    elif s[i] == 'e':
        i += 1
        goto.exp
    elif s[i] == '$':
        return True
    elif __name__:
        return False

    label.exp

    if s[i] in '+-':
        i += 1
        goto.expsign

    label.expsign

    label.expdigits

    while s[i] in DIGITS:
        i += 1
    if s[i] == '+':
        i += 1
        goto.start
    elif s[i] == '$':
        return True
    elif __name__:
        return False


def generate_str(n: int, seed: int = None) -> str:
    if seed is not None:
        random.seed(seed)
    fpnums = []
    for i in range(n):
        digits1 = str(random.randint(10, 1000000))  # digits 1
        if random.randint(0, 100) < 20:
            fpnums.append(digits1)
            continue
        if random.randint(0, 100) > 20:
            digits2 = '.' + str(random.choice(['', '', '', '0', '00', '000'])) + str(random.randint(1, 1000000))
            if random.randint(0, 100) < 30:
                fpnums.append(digits1 + digits2)
                continue
        else:
            digits2 = ''
        sign = random.choice(['-', '+'])
        digits3 = str(random.randint(2, 1000))
        assert (digits1 + digits2 != '')
        fpnums.append(digits1 + digits2 + 'e' + sign + digits3)
    return '+'.join(fpnums) + '$'  # '$' for EOF


if __name__ == '__main__':
    s = generate_str(2002, seed=1236)
    print('Length:', len(s))
    # open('rmthis','w').write(s)
    d = timeit.timeit(lambda: run_import_statemachine(s), number=5)
    print('python-statemachine:', d / 5)
    d = timeit.timeit(lambda: run_match(s), number=100)
    print('for loop + match:', d / 100)
    # import dis
    # dis.dis(run_goto)
    # print(s)
    d = timeit.timeit(lambda: run_goto(s), number=1000)
    print('goto:', d / 1000)
