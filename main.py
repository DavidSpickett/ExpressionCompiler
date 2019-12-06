import string
import re
import math
import operator
from abc import ABC
from functools import reduce
from copy import copy
from itertools import tee

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class ParsingError(Exception):
    pass


class Call(ABC):
    def __init__(self, *args):
        self.args = args
        self.validate_args()

    def __repr__(self):
        return "{}({})".format(
          self.name,
          ", ".join(map(repr, self.args))
        )

    def validate_args(self):
        insert = "" if self.exact else "at least "
        pluralise = "s" if self.num_args != 1 else ""

        if (self.exact and len(self.args) != self.num_args) or \
           (not self.exact and len(self.args) < self.num_args):
            err = "Expected {}{} argument{} for function \"{}\", got {}."
            raise ParsingError(err.format(
                                insert, self.num_args,
                                pluralise, self.name, len(self.args)))

    def prepare(self, scope, *args):
        # Called before any calls are evaled. E.g. for a let expression
        return scope

    def execute(self, scope):
        """
        >>> Call.execute(PlusCall(1, 2), {})
        3
        >>> Call.execute(PlusCall(1, 2), {})
        3
        >>> Call.execute(PlusCall(1, 2, 3, 4), {})
        10
        >>> Call.execute(MinusCall(PlusCall(4, 3), 4), {})
        3
        >>> Call.execute(SquareRootCall(4), {})
        2.0
        >>> Call.execute(PlusCall(SquareRootCall(16), MinusCall(12, 13)), {})
        3.0
        >>> Call.execute(PlusCall("foo", "bar"), {"foo":1, "bar":2})
        3
        >>> Call.execute(SquareRootCall("abc"), {})
        Traceback (most recent call last):
        ParsingError: Reference to unknown variable "abc".
        >>> # Note that this var name is *not* escaped
        >>> Call.execute(LetCall("foo", 2, PlusCall("foo", 5)), {})
        Traceback (most recent call last):
        ParsingError: Reference to unknown variable "foo".
        >>> # Whereas this one is
        >>> Call.execute(LetCall("'bar", 16, SquareRootCall("bar")), {})
        4.0
        """
        # First resolve all symbols
        sym_args = []
        for arg in self.args:
            if isinstance(arg, str):
                if arg.startswith("'"):
                    # Don't evaluate this, just treat as string
                    arg = arg[1:]
                else:
                    try:
                        arg = int(arg)
                    except ValueError:
                        try:
                            arg = scope[arg]
                        except KeyError:
                            msg = "Reference to unknown variable \"{}\"."
                            raise ParsingError(msg.format(arg))

            sym_args.append(arg)

        # Then we prepare the scope, adding any new vars
        scope = self.prepare(scope, *sym_args)

        # Then resolve the calls using the updated scope
        resolved_args = []
        for arg in sym_args:
            if isinstance(arg, Call):
                arg = arg.execute(scope)
            resolved_args.append(arg)

        """
        Now all arguments are constants
        Remember that we validated the number of args
        when we built the Call objects.
        """
        return self.apply(scope, *resolved_args)


class PlusCall(Call):
    exact = False
    num_args = 2
    name = "+"

    def apply(self, scope, *args):
        return sum(args)


class MinusCall(Call):
    exact = False
    num_args = 2
    name = "-"

    def apply(self, scope, *args):
        return reduce(operator.sub, args)


class SquareRootCall(Call):
    exact = True
    num_args = 1
    name = "sqrt"

    def apply(self, scope, a):
        return math.sqrt(a)


class LetCall(Call):
    exact = True
    num_args = 3
    name = "let"

    def prepare(self, scope, *args):
        # This is called before we evaluate the body
        # Inner scope, don't modify outer
        # E.g. (let 'x 1 (let 'y 2 (+ 1 y)) (+ x y))
        # Should be an error, y is only in the inner scope
        scope = copy(scope)

        for k,v in pairwise(args[:-1]):
            if isinstance(v, Call):
                v = v.execute(scope)
            scope[k] = v
        return scope

    def validate_args(self):
        num_args = len(self.args)
        expect = "(let <name> <value> ... (body))"
        if num_args < 3:
            raise ParsingError("Too few arguments for let. Expected {}".format(expect))
        elif not num_args % 2:
            raise ParsingError("Wrong number arguments for let. Expected {}".format(expect))


    def apply(self, scope, *args):
        # The body has already been evaluated by this point
        return args[-1]


def make_call(operator, args):
    """
    >>> make_call("ooo", [])
    Traceback (most recent call last):
    ParsingError: Call to unknown function "ooo".
    >>> make_call("sqrt", [])
    Traceback (most recent call last):
    ParsingError: Expected 1 argument for function "sqrt", got 0.
    >>> make_call("sqrt", [2, 3])
    Traceback (most recent call last):
    ParsingError: Expected 1 argument for function "sqrt", got 2.
    >>> make_call("+", [])
    Traceback (most recent call last):
    ParsingError: Expected at least 2 arguments for function "+", got 0.
    >>> make_call("-", [1])
    Traceback (most recent call last):
    ParsingError: Expected at least 2 arguments for function "-", got 1.
    >>> make_call("let", [1, 2])
    Traceback (most recent call last):
    ParsingError: Too few arguments for let. Expected (let <name> <value> ... (body))
    >>> make_call("let", [1, 2, 3, 4])
    Traceback (most recent call last):
    ParsingError: Wrong number arguments for let. Expected (let <name> <value> ... (body))
    """
    calls = [
        PlusCall,
        MinusCall,
        SquareRootCall,
        LetCall,
    ]
    if isinstance(operator, Call):
        # Functions cannot return callables
        raise ParsingError("Expected function name, got a call to a function.")

    for call_type in calls:
        if call_type.name == operator:
            break
    else:
        raise ParsingError("Call to unknown function \"{}\".".format(operator))

    return call_type(*args)

def get_symbol(src, idx):
    delimiters = ["(", ")"]
    delimiters.extend(string.whitespace)

    symbol = ""
    while idx < len(src) and src[idx] not in delimiters:
        symbol += src[idx]
        idx += 1

    return symbol, idx


def process_call(src, idx=0):
    """
    >>> process_call("+ 1 2)")
    Traceback (most recent call last):
    ParsingError: Call must begin with "(".
    >>> process_call("(+ 1 2")
    Traceback (most recent call last):
    ParsingError: Unterminated call to function "+"
    >>> process_call("(- (sqrt 2")
    Traceback (most recent call last):
    ParsingError: Unterminated call to function "sqrt"
    >>> process_call("(+ 1 2 3 4 5 6)")[0]
    +('1', '2', '3', '4', '5', '6')
    >>> process_call("(- (+ 1 (- 1 2)) 5)")[0]
    -(+('1', -('1', '2')), '5')
    >>> process_call("((+ 1 2))")[0]
    Traceback (most recent call last):
    ParsingError: Expected function name, got a call to a function.
    """
    if src[idx] != "(":
        raise ParsingError("Call must begin with \"(\".")

    idx += 1
    parts = []

    while idx < len(src):
        if src[idx] == "(":
            call, idx = process_call(src, idx)
            parts.append(call)
        elif src[idx] == ")":
            # Note the +1 here to consume the closing bracket
            return make_call(parts[0], parts[1:]), idx+1
        elif src[idx] in string.whitespace:
            # Whitespace around () will have been removed but
            # it is still in between arguments
            idx += 1
        else:
            symbol, idx = get_symbol(src, idx)
            parts.append(symbol)

    if parts:
        raise ParsingError(
            "Unterminated call to function \"{}\"".format(parts[0]))


def normalise(source):
    """
    >>> normalise("   ( foo )")
    '(foo)'
    >>> normalise("(    foo (bar 1  2 ))")
    '(foo(bar 1 2))'
    """
    return re.sub(r"\s*([\(\)])\s*", r"\g<1>",
                  re.sub(r"\s+", " ", source))


def run_source(source):
    """
    >>> run_source("")
    >>> run_source("(+ 1 2)")
    3
    >>> run_source("(sqrt (+ 2 2))")
    2.0
    >>> run_source("(+ (sqrt (- 9 5)) (- 10 (+ (- 2 3) 2)))")
    11.0
    >>> run_source("(let 'a 1 (+ a 1) )")
    2
    >>> run_source("(let 'x (let 'y 1 (+ y 0)) (+ x y))")
    Traceback (most recent call last):
    ParsingError: Reference to unknown variable "y".
    >>> run_source("(let 'x 1 (let 'y 2 (+ x y)))")
    3
    >>> # Declare multiple variables in one let
    >>> run_source("(let 'x 1 'y 2 (+ x y))")
    3
    """
    if not source:
        return

    source = normalise(source)
    prog, _ = process_call(source)
    if prog:
        return prog.execute({})


if __name__ == "__main__":
    import doctest
    doctest.testmod()
