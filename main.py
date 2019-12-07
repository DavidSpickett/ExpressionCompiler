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

    def prepare(self, scope, global_scope, *args):
        # Called before any calls are evaled. E.g. for a let expression
        return args, scope

    def execute(self, scope, global_scope):
        """
        >>> Call.execute(PlusCall(1, 2), {}, {})
        3
        >>> Call.execute(PlusCall(1, 2), {}, {})
        3
        >>> Call.execute(PlusCall(1, 2, 3, 4), {}, {})
        10
        >>> Call.execute(MinusCall(PlusCall(4, 3), 4), {}, {})
        3
        >>> Call.execute(SquareRootCall(4), {}, {})
        2.0
        >>> Call.execute(
        ...     PlusCall(
        ...         SquareRootCall(16),
        ...         MinusCall(12, 13)
        ...     ), {}, {})
        3.0
        >>> Call.execute(PlusCall("foo", "bar"), {"foo":1, "bar":2}, {})
        3
        >>> Call.execute(SquareRootCall("abc"), {}, {})
        Traceback (most recent call last):
        ParsingError: Reference to unknown variable "abc".
        >>> # Note that this var name is *not* escaped
        >>> Call.execute(LetCall("foo", 2, PlusCall("foo", 5)), {}, {})
        Traceback (most recent call last):
        ParsingError: Reference to unknown variable "foo".
        >>> # Whereas this one is
        >>> Call.execute(LetCall("'bar", 16, SquareRootCall("bar")), {}, {})
        4.0
        >>> Call.execute(EqualCall(1, 2), {}, {})
        False
        >>> Call.execute(EqualCall(1, 1, 1, 1), {}, {})
        True
        >>> # Show that the body is not evaluated
        >>> Call.execute(
        ...     DefineFunctionCall("'x", "'y", PlusCall("x", "y")), {}, {})
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
        # Things like "if" may modify it's args
        sym_args, scope = self.prepare(scope, global_scope, *sym_args)

        # Then resolve the calls using the updated scope
        resolved_args = []
        for arg in sym_args:
            if isinstance(arg, Call):
                arg = arg.execute(scope, global_scope)
            resolved_args.append(arg)

        """
        Now all arguments are constants
        Remember that we validated the number of args
        when we built the Call objects.
        """
        return self.apply(scope, global_scope, *resolved_args)


class EqualCall(Call):
    exact = False
    num_args = 2
    name = "eq"

    def apply(self, scope, global_scope, *args):
        return len(set(args)) == 1


class IfCall(Call):
    exact = True
    num_args = 3
    name = "if"

    def prepare(self, scope, global_scope, *args):
        condition = args[0]
        if isinstance(condition, Call):
            condition = condition.execute(scope, global_scope)
        # Choose the "then" or the "else"
        args = (args[1],) if condition else (args[2],)
        return args, scope

    def apply(self, scope, global_scope, *args):
        # The body has already been evaluated by this point
        return args[-1]


class ModulusCall(Call):
    exact = True
    num_args = 2
    name = "%"

    def apply(self, scope, global_scope, a, b):
        return a % b


class PlusCall(Call):
    exact = False
    num_args = 1
    name = "+"

    def apply(self, scope, global_scope, *args):
        return reduce(operator.add, args)


class MinusCall(Call):
    exact = False
    num_args = 1
    name = "-"

    def apply(self, scope, global_scope, *args):
        if len(args) == 1:
            return -args[0]
        return reduce(operator.sub, args)


class SquareRootCall(Call):
    exact = True
    num_args = 1
    name = "sqrt"

    def apply(self, scope, gobal_scope, a):
        return math.sqrt(a)


class PrintCall(Call):
    exact = False
    num_args = 1
    name = "print"

    def apply(self, scope, global_scope, *args):
        print(*args)


class LetCall(Call):
    exact = True
    num_args = 3
    name = "let"

    def prepare(self, scope, global_scope, *args):
        # This is called before we evaluate the body
        # Inner scope, don't modify outer
        # E.g. (let 'x 1 (let 'y 2 (+ 1 y)) (+ x y))
        # Should be an error, y is only in the inner scope
        scope = copy(scope)

        for k, v in pairwise(args[:-1]):
            if isinstance(v, Call):
                v = v.execute(scope, global_scope)
            scope[k] = v
        return args, scope

    def validate_args(self):
        num_args = len(self.args)
        expect = "(let <name> <value> ... (body))"
        if num_args < 3:
            raise ParsingError(
                "Too few arguments for let. Expected {}".format(expect))
        elif not num_args % 2:
            raise ParsingError(
                "Wrong number arguments for let. Expected {}".format(expect))

    def apply(self, scope, global_scope, *args):
        # The body has already been evaluated by this point
        return args[-1]


class BaseUserCall(Call):
    def prepare(self, scope, global_scope, *args):
        # Add the names of the function args to the current
        # scope with the values they're being called with.
        scope = copy(scope)
        # Note that there's no need to skip the body here.
        # When we're processing the *defun* we need that.
        # Here these args are the function's parameters.
        for k, v in zip(self.arg_names, args):
            scope[k] = v
        return args, scope

    def apply(self, scope, global_scope, *args):
        # Run the body of the function with its parameters
        return self.body.execute(scope, global_scope)


def make_user_function(name, *args):
    # Args in this case is the names of the arguments
    # to this new function
    return type(
        "UserCall{}".format(name),
        (BaseUserCall,),
        {
            "exact": True,
            "name": name,
            # -1 because last is the body of the function
            "num_args": len(args)-1,
            "arg_names": args[:-1],
            # The code to be run (which is a Call by now)
            "body": args[-1],
        }
    )


class DefineFunctionCall(Call):
    exact = False
    num_args = 2
    name = "defun"

    def __init__(self, *args):
        super().__init__(*args)
        self.body = None

    def prepare(self, scope, global_scope, *args):
        """
        We need to prevent the body of the function
        being evaluated until it's actually called.
        We could just add the function to global scope here,
        but then defuns that aren't executed would still
        define a function. if c def a else def b etc.
        So just remove the body from the args and stash
        it in the defun call until it actually gets
        executed.
        """
        self.body = args[-1]
        return args[:-1], scope

    def apply(self, scope, global_scope, *args):
        # Add a new Call type to global scope
        # Remember that the body of the function
        # was stashed in self in prepare.

        # Note the name and args have the ' removed by now
        name = args[0]
        args = args[1:]

        global_scope[name] = type(
            "UserCall{}".format(name),
            (BaseUserCall,),
            {
                "exact": True,
                "name": name,
                "num_args": len(args),
                "arg_names": args,
                # The code to be run (which is a Call by now)
                "body": self.body,
            }
        )

        # We don't return anything here, just add a fn to global scope


def make_call(operator, args, global_scope):
    """
    >>> make_call("ooo", [], {})
    Traceback (most recent call last):
    ParsingError: Call to unknown function "ooo".
    >>> make_call("sqrt", [], {})
    Traceback (most recent call last):
    ParsingError: Expected 1 argument for function "sqrt", got 0.
    >>> make_call("sqrt", [2, 3], {})
    Traceback (most recent call last):
    ParsingError: Expected 1 argument for function "sqrt", got 2.
    >>> make_call("+", [], {})
    Traceback (most recent call last):
    ParsingError: Expected at least 1 argument for function "+", got 0.
    >>> make_call("let", [1, 2], {})
    Traceback (most recent call last):
    ParsingError: Too few arguments for let. \
Expected (let <name> <value> ... (body))
    >>> make_call("let", [1, 2, 3, 4], {})
    Traceback (most recent call last):
    ParsingError: Wrong number arguments for let. \
Expected (let <name> <value> ... (body))
    >>> make_call("eq", [1], {})
    Traceback (most recent call last):
    ParsingError: Expected at least 2 arguments for function "eq", got 1.
    """
    calls = [
        PlusCall,
        MinusCall,
        SquareRootCall,
        LetCall,
        IfCall,
        PrintCall,
        EqualCall,
        ModulusCall,
        DefineFunctionCall,
    ]
    if isinstance(operator, Call):
        # Functions cannot return callables
        raise ParsingError("Expected function name, got a call to a function.")

    # First check for a user function
    try:
        return global_scope[operator](*args)
    except KeyError:
        # Look for a builtin function
        for call_type in calls:
            if call_type.name == operator:
                break
        else:
            raise ParsingError(
                    "Call to unknown function \"{}\".".format(operator))

        return call_type(*args)


def get_symbol(src, idx):
    is_string = src[idx] == "\""
    if is_string:
        delimiters = ["\""]
        idx += 1
    else:
        delimiters = ["(", ")"]
        delimiters.extend(string.whitespace)

    symbol = ""
    while idx < len(src) and src[idx] not in delimiters:
        symbol += src[idx]
        idx += 1

    if is_string:
        idx += 1
        symbol = "'" + symbol

    return symbol, idx


def process_call(src, idx, global_scope):
    """
    >>> process_call("+ 1 2)", 0, {})
    Traceback (most recent call last):
    ParsingError: Call must begin with "(".
    >>> process_call("(+ 1 2", 0, {})
    Traceback (most recent call last):
    ParsingError: Unterminated call to function "+"
    >>> process_call("(- (sqrt 2", 0, {})
    Traceback (most recent call last):
    ParsingError: Unterminated call to function "sqrt"
    >>> process_call("(+ 1 2 3 4 5 6)", 0, {})[0]
    +('1', '2', '3', '4', '5', '6')
    >>> process_call("(- (+ 1 (- 1 2)) 5)", 0, {})[0]
    -(+('1', -('1', '2')), '5')
    >>> process_call("((+ 1 2))", 0, {})[0]
    Traceback (most recent call last):
    ParsingError: Expected function name, got a call to a function.
    """
    if src[idx] != "(":
        raise ParsingError("Call must begin with \"(\".")

    idx += 1
    parts = []

    while idx < len(src):
        if src[idx] == "(":
            call, idx, global_scope = process_call(src, idx, global_scope)
            parts.append(call)
        elif src[idx] == ")":
            # Note the +1 here to consume the closing bracket
            return make_call(
                parts[0], parts[1:], global_scope), idx+1, global_scope
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
    >>> run_source("(+ (+ 1) (- 1))")
    0
    >>> run_source("(if 0 (+ 1) (- 1))")
    -1
    >>> run_source("(if 1 (+ 1) (- 1))")
    1
    >>> run_source("(if (- 2 2) (+ 1) (- 1))")
    -1
    >>> run_source("(+ 'b 'c)")
    'bc'
    >>> # Multiple blocks
    >>> run_source("(print \\"The result is:\\")(+ 1 2)")
    The result is:
    3
    >>> run_source("(let 'foo 1 'bar \\"cat\\" (print foo bar))")
    1 cat
    >>> run_source(
    ...  "(let 'x 1 'y 1 'z 1\\
    ...     (if (eq x y z)\\
    ...       (print \\"hello\\")\\
    ...       (print \\"goodbye\\")\\
    ...     )\\
    ...   )")
    hello
    >>> run_source("(defun 'add 'a 'b (+ a b)) (add 1 2)")
    3
    >>> # C rules, B must be defined before A
    >>> run_source(
    ...  "(defun 'B 'y (+ y 10))\\
    ...   (defun 'A 'x (+ (B x) 1))\\
    ...   (A 24)")
    35
    >>> #No return value from program should be fine
    >>> run_source("(defun 'x (+ 1))")
    >>> # Can have no arguments
    >>> run_source("(defun 'x (+ 4)) (sqrt (x))")
    2.0
    >>> # Usual argument validaton takes place
    >>> run_source("(defun 'x 'y (+ y))(x 2 3)")
    Traceback (most recent call last):
    ParsingError: Expected 1 argument for function "x", got 2.
    >>> run_source("(defun 'x 'y (+ y)) (x))")
    Traceback (most recent call last):
    ParsingError: Expected 1 argument for function "x", got 0.
    >>> # This does not define "bar"
    >>> run_source(
    ... "(if (+ 1)\\
    ...     (defun 'foo 'x (+ x))\\
    ...     (defun 'bar 'x (+ x))\\
    ...  )\\
    ...  (foo 1)\\
    ...  (bar 2)")
    Traceback (most recent call last):
    ParsingError: Call to unknown function "bar".
    >>> # We can define a function with a different body
    >>> run_source(
    ... "(if (+ 0)\\
    ...     (defun 'x (+ 2))\\
    ...     (defun 'x (+ 3))\\
    ...  )\\
    ...  (x)")
    3
    >>> # Value of x at time of defun is irrelevant
    >>> run_source(
    ... "(let 'x 99\\
    ...     (defun 'y 'a (+ a x))\\
    ...  )\\
    ...  (let 'x 1\\
    ...     (y 10)\\
    ...  )")
    11
    >>> run_source("(% 5 3)")
    2
    >>> # fn returning a string can be used as a name
    >>> run_source(
    ...     "(defun (+ \\"f\\") (print \\"Hello\\"))\\
    ...      (f)")
    Hello
    """
    if not source:
        return

    source = normalise(source)
    idx = 0
    # Where user functions are added to
    global_scope = {}

    result = None
    while idx < len(source):
        body, idx, global_scope = process_call(source, idx, global_scope)
        if body:
            # Execute as we go so that new functions are defined

            # Each new block will have a new scope
            # The global scope will be updated during blocks
            result = body.execute({}, global_scope)

    # program's return value is the return of the last block
    return result


if __name__ == "__main__":
    import doctest
    doctest.testmod()
