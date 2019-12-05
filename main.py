import string
import re
import math
import operator
from abc import ABC
from functools import reduce
from copy import copy


class ParsingError(Exception):
    pass


class Call(ABC):
    def __init__(self, *args):
        self.args = args

    def __repr__(self):
        return "{}({})".format(
          self.name,
          ", ".join(map(repr, self.args))
        )

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
        >>> Call.execute(LetCall("foo", 2, PlusCall("foo", 5)), {})
        Traceback (most recent call last):
        ParsingError: Reference to unknown variable "foo".
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

    def prepare(self, scope, name, value, body):
        # This is called before we evaluate the body
        # Inner scope, don't modify outer
        # E.g. (let 'x 1 (let 'y 2 (+ 1 y)) (+ x y))
        # Should be an error, y is only in the inner scope
        scope = copy(scope)
        if isinstance(value, Call):
            value = value.execute(scope)
        scope[name] = value
        return scope

    def apply(self, scope, name, value, body):
        # The body has already been evaluated by this point
        return body


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
    """
    calls = [
        PlusCall,
        MinusCall,
        SquareRootCall,
        LetCall,
    ]
    found_type = None

    if isinstance(operator, Call):
        # Functions cannot return callables
        raise ParsingError("Expected function name, got a call to a function.")

    for call_type in calls:
        if call_type.name == operator:
            found_type = call_type
            break

    if found_type:
        insert = "" if found_type.exact else "at least "
        pluralise = "s" if found_type.num_args != 1 else ""

        if (found_type.exact and len(args) != found_type.num_args) or \
           (not found_type.exact and len(args) < found_type.num_args):
            err = "Expected {}{} argument{} for function \"{}\", got {}."
            raise ParsingError(err.format(
                                insert, found_type.num_args,
                                pluralise, found_type.name, len(args)))

        return call_type(*args)
    else:
        raise ParsingError("Call to unknown function \"{}\".".format(operator))


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
    operator = None
    args = []

    while idx < len(src):
        if src[idx] == "(":
            call, idx = process_call(src, idx)
            if operator is None:
                operator = call
            else:
                args.append(call)
        elif src[idx] == ")":
            assert operator is not None
            # Note the +1 here to consume the closing bracket
            return make_call(operator, args), idx+1
        elif src[idx] in string.whitespace:
            # Whitespace around () will have been removed but
            # it is still in between arguments
            idx += 1
        else:
            symbol, idx = get_symbol(src, idx)
            if symbol:
                if operator is None:
                    operator = symbol
                else:
                    args.append(symbol)

    if operator:
        raise ParsingError(
            "Unterminated call to function \"{}\"".format(operator))


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
