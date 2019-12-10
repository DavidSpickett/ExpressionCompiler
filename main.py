import string
import re
import math
import operator
import argparse
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


def lookup_var(scope, global_scope, arg, current_call):
    # Note: current_call is only here for the error msg

    # If it hasn't already been resolved
    if isinstance(arg, str):
        # ' escape char, don't evaluate
        if arg.startswith("'"):
            return False, arg[1:]

        try:
            # Integer argument
            return False, int(arg)
        except ValueError:
            # Must be the name of some symbol

            # Whether to expand a list into flat arguments
            # (print *ls) => (print ls[0] ls[1] ...)
            expand = False

            # Symbol preceeded with * is expanded
            # "*" on its own is not
            if arg.startswith("*") and len(arg) > 1:
                arg = arg[1:]
                expand = True

            # Local scope first
            if arg in scope:
                arg = scope[arg]
            elif arg in global_scope:
                arg = global_scope[arg]
            else:
                msg = "Reference to unknown symbol \"{}\" in \"{}\"."
                raise ParsingError(msg.format(arg, current_call))

            return expand, arg

    # Something that was already evaluated
    return False, arg


class Call(ABC):
    def __init__(self, *args):
        self.args = args
        self.validate_args()

    def __repr__(self):
        # Print in lisp format (f arg1 arg2)
        return "({}{}{})".format(
          self.name, " " if self.args else "",
          " ".join(map(repr, self.args))
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
        ParsingError: Reference to unknown symbol "abc" in "(sqrt 'abc')".
        >>> # Note that this var name is *not* escaped
        >>> Call.execute(LetCall("foo", 2, PlusCall("foo", 5)), {}, {})
        Traceback (most recent call last):
        ParsingError: Reference to unknown symbol "foo" \
in "(let 'foo' 2 (+ 'foo' 5))".
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
        <class 'abc.UserCall_x'>
        """
        # First resolve all symbols
        sym_args = []
        for arg in self.args:
            expand, arg = lookup_var(scope, global_scope, arg, self)
            if expand:
                sym_args.extend(arg)
            else:
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


class NotCall(Call):
    exact = True
    num_args = 1
    name = "not"

    def apply(self, scope, global_scope, boolean):
        return not boolean


class EqualCall(Call):
    exact = False
    num_args = 2
    name = "eq"

    def apply(self, scope, global_scope, *args):
        return len(set(args)) == 1


class LessThanCall(Call):
    exact = True
    num_args = 2
    name = "<"

    def apply(self, scope, global_scope, lhs, rhs):
        return lhs < rhs


class IfCall(Call):
    exact = False
    num_args = 2
    name = "if"

    def prepare(self, scope, global_scope, *args):
        condition = args[0]
        if isinstance(condition, Call):
            condition = condition.execute(scope, global_scope)

        if condition:
            # Applies to either then or then and else
            args = (args[1],)
        elif len(args) == 3:
            args = (args[2],)
        else:
            # Only "then" and condition is False
            args = []

        return args, scope

    def apply(self, scope, global_scope, *args):
        # The body has already been evaluated by this point
        try:
            return args[-1]
        except IndexError:
            # Only "then" and condition was False so no body
            pass


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
    num_args = 0
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
        # Special routine here since let requires
        # matched pairs of name-value, followed by
        # a single body.
        num_args = len(self.args)
        expect = "(let <name> <value> ... (body))"
        if num_args < 3:
            raise ParsingError(
                "Too few arguments for let. Expected {}".format(expect))
        elif not num_args % 2:
            raise ParsingError(
                "Wrong number arguments for let \"{}\". \
Expected {}".format(self, expect))

    def apply(self, scope, global_scope, *args):
        # The body has already been evaluated by this point
        return args[-1]


class LenCall(Call):
    name = "len"
    exact = True
    num_args = 1

    def apply(self, scope, global_scope, ls):
        return len(ls)


class NthCall(Call):
    name = "nth"
    exact = True
    num_args = 2

    def apply(self, scope, global_scope, idx, ls):
        return ls[idx]


class FlattenCall(Call):
    name = "flatten"
    exact = True
    num_args = 1

    def apply(self, scope, global_scope, ls):
        """
        >>> FlattenCall.apply(None, {}, {}, [])
        ()
        >>> FlattenCall("foo").apply({}, {}, 1)
        Traceback (most recent call last):
        ParsingError: Flatten "(flatten 'foo')" not called with a list.
        >>> FlattenCall.apply(None, {}, {}, [1, 2, 3])
        (1, 2, 3)
        >>> FlattenCall.apply(None, {}, {}, [[1, 2], 3])
        (1, 2, 3)
        >>> FlattenCall.apply(None, {}, {}, [[[1, 2]], [3], [4, [5]]])
        (1, 2, 3, 4, 5)
        """
        flat = []

        def _flatten(_ls):
            try:
                for l in _ls:
                    try:
                        iter(l)
                        _flatten(l)
                    except TypeError:
                        flat.append(l)
            except TypeError:
                raise ParsingError(
                    "Flatten \"{}\" not called with a list.".format(self))

        _flatten(ls)

        # Tuple for consistency when printing
        return tuple(flat)


class ImportCall(Call):
    name = "import"
    exact = True
    num_args = 1

    def prepare(self, scope, global_scope, filepath):
        with open(filepath, 'r') as f:
            _, global_scope = run_source_inner(
                f.read(), global_scope=global_scope)
        return (), scope

    def apply(self, scope, global_scope, *args):
        pass


class BaseUserCall(Call):
    def apply(self, scope, global_scope, *args):
        scope = copy(scope)

        """
         No function body here that's handled in the defun
         Do the binding now because if we did it in the
         prepare step then expressions won't be resolved.
         Here: (f (+ 1 2)) has become (f 3) already
        """

        # Make star empty as default in case they only
        # call with positional args. It must still be defined.
        if self.arg_names and self.arg_names[-1] == "*":
            scope["*"] = ()

        for idx in range(len(args)):
            if self.arg_names[idx] == "*":
                scope["*"] = args[idx:]
                break
            scope[self.arg_names[idx]] = args[idx]

        # Run the body of the function with its parameters
        return self.body.execute(scope, global_scope)


class DefineFunctionCall(Call):
    exact = False
    num_args = 2
    name = "defun"

    def __init__(self, *args):
        super().__init__(*args)
        self.body = None
        self.variadic = False

        var = "'*"
        if var in self.args:
            if self.args.index("'*") != len(self.args)-2:
                raise ParsingError(
                    "\"'*\" must be the last parameter if present.")
            self.variadic = True

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
            "UserCall_{}".format(name),
            (BaseUserCall,),
            {
                "exact": not self.variadic,
                "name": name,
                "num_args": 0 if self.variadic else len(args),
                "arg_names": args,
                # The code to be run (which is a Call by now)
                "body": self.body,
                "variadic": self.variadic
            }
        )

        # Return the function itself, so it can be used as an argument
        return global_scope[name]


class MaybeFunctionCall(Call):
    """ Placeholder for a user function call
        to something not defined yet.
        E.g. (defun 'f (f))
        "f" is not defined until the defun
        has added it to the global scope.
        So insert a maybe function call for
        (f) and check that it exists when
        we come to run it.
    """
    num_args = 0
    exact = False

    def __init__(self, name, *args):
        self.name = name
        super().__init__(*args)

    def apply(self, scope, global_scope, *args):
        _, real_fn = lookup_var(scope, global_scope,
                                self.name, self)

        if not issubclass(real_fn, Call):
            msg = "\"{}\" is not a function, it is {}. (in \"{}\")"
            raise RuntimeError(msg.format(self.name, real_fn, self))

        # Make an instance of it
        # Note that we use the pre-evaluation args here
        # though at the moment we only check the number of args
        # not the types. So we could use the paramater args instead.
        real_fn = real_fn(*self.args)

        # Then the post evaluation args here
        return real_fn.apply(scope, global_scope, *args)


def make_call(fn_name, args, global_scope):
    """
    >>> # User function names aren't resolved here
    >>> make_call("ooo", [], {})
    (ooo)
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
    ParsingError: Wrong number arguments for let "(let 1 2 3 4)". \
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
        LessThanCall,
        ModulusCall,
        DefineFunctionCall,
        NthCall,
        LenCall,
        ImportCall,
        FlattenCall,
        NotCall,
    ]
    if isinstance(fn_name, Call):
        # Functions cannot return callables
        raise ParsingError("Expected function name, got a call \
to a function \"{}\".".format(fn_name))

    # First check for a user function
    try:
        return global_scope[fn_name](*args)
    except KeyError:
        # Look for a builtin function
        for call_type in calls:
            if call_type.name == fn_name:
                break
        else:
            # Maybe this is a user func defined later
            return MaybeFunctionCall(fn_name, *args)

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
    (+ '1' '2' '3' '4' '5' '6')
    >>> process_call("(- (+ 1 (- 1 2)) 5)", 0, {})[0]
    (- (+ '1' (- '1' '2')) '5')
    >>> process_call("((+ 1 2))", 0, {})[0]
    Traceback (most recent call last):
    ParsingError: Expected function name, got a call \
to a function "(+ '1' '2')".
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
    >>> normalise("# food")
    ''
    >>> normalise("(+ 2 1) #foo")
    '(+ 2 1)'
    >>> normalise("(+ 1 2) #thing\\n(+ 3 4)")
    '(+ 1 2)(+ 3 4)'
    """
    # <space><bracket><space> => <bracket>
    return re.sub(r"\s*([\(\)])\s*", r"\g<1>",
                  # <space> n times => <space>
                  re.sub(r"\s+", " ",
                         # remove comments
                         re.sub(r"#.*(\n)?", "", source)))


# Call this one when you want to get the resulting global scope
def run_source_inner(source, global_scope=None):
    if global_scope is None:
        # Where user functions are added to
        global_scope = {}

    source = normalise(source)
    idx = 0
    result = None

    if not source:
        return result, global_scope

    while idx < len(source):
        body, idx, global_scope = process_call(source, idx, global_scope)
        if body:
            # Execute as we go so that new functions are defined
            # Each new block will have a new scope
            # The global scope will be updated during blocks
            result = body.execute({}, global_scope)

    # program's return value is the return of the last block
    return result, global_scope


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
    ParsingError: Reference to unknown symbol "y" in "(+ 'x' 'y')".
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
    <class 'abc.UserCall_x'>
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
    ParsingError: Reference to unknown symbol "bar" in "(bar '2')".
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
    >>> run_source(
    ...  "(let 'n \\"negate\\"\\
    ...        (defun n 'n (- n))\\
    ...   )\\
    ...   (negate 1)")
    -1
    >>> run_source(
    ... "# This is a comment\\n\\
    ...  # (+ 1 2)\\n\\
    ...  (print (+ 1 2))\\n\\
    ...  # Or after\\n\\
    ... (print \\"No hashes in strings. *sadface*\\")")
    3
    No hashes in strings. *sadface*
    >>> # Arguments for user funcs can be expressions
    >>> run_source(
    ... "(defun 'f 'n (print n))\\
    ...  (f (+ 1 2))")
    3
    >>> # Ifs can just have the "then" block, no "else"
    >>> run_source("(if (eq 1 2) (+ 1))")
    >>> run_source("(if (eq 1 1) (+ 1))")
    1
    >>> run_source("(defun 'f 'a '* (+ a *))")
    <class 'abc.UserCall_f'>
    >>> run_source("(defun 'g '* 'a (+ a *))")
    Traceback (most recent call last):
    ParsingError: "'*" must be the last parameter if present.
    >>> # Functions can be passed as arguments
    >>> run_source(
    ... "(defun 'f 'x (x 1))\\
    ...  (defun 'g 'y (+ y y))\\
    ...  (f g)")
    2
    >>> # "*" must be defined even if it would be empty
    >>> run_source(
    ... "(let 'f\\
    ...    (defun ' 'x '*\\
    ...      (print *)\\
    ...    )\\
    ...    (f 1)\\
    ...  )")
    ()
    >>> run_source("(not (eq 1 0))")
    True
    >>> run_source("(not (+ 1))")
    0
    """
    return run_source_inner(source)[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LispALike interpreter')
    parser.add_argument('--test', default=False,
                        action='store_true',
                        help='Run tests. (default False)')
    parser.add_argument('filename', nargs='?',
                        help="File to interpret. (optional)")
    args = parser.parse_args()

    if args.test:
        import doctest
        doctest.testmod()
    else:
        if args.filename is None:
            raise RuntimeError("Filename is required if not running tests.")
        with open(args.filename) as f:
            print(run_source(f.read()))
