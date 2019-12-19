import string
import re
import math
import operator
import argparse
import inspect
from abc import ABC
from functools import reduce
from copy import copy, deepcopy


def pairs(it):
    return ((it[i], it[i+1]) for i in range(0, len(it), 2))


class ParsingError(Exception):
    pass


# Represents a user provided string.
# Making it a subclass means I can prevent
# them being looked up repeatedly.
class StringVar(object):
    def __init__(self, s):
        self.value = s

    def __repr__(self):
        return "StringVar<\"{}\">".format(self.value)

    def __len__(self):
        return len(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError("No slicing string vars!")
        return StringVar(self.value[key])

    def __add__(self, other):
        return StringVar(self.value + other.value)


def lookup_var(scope, global_scope, arg, current_call):
    # Note: current_call is only here for the error msg

    # Don't lookup literal strings, or something that was
    # already resolved.
    if isinstance(arg, StringVar) or not isinstance(arg, str):
        return False, arg

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
    # Empty name means user code won't be calling this fn
    name = ""
    # Whether args must be validated earlier
    validate_on_resolve = False

    def __init__(self, *args):
        self.args = args
        self.resolved_symbols = False
        self.prepared = False

    def can_prepare(self, args, arg_idx):
        # Have we executed enough args to be able to prepare?
        return True

    def sort_args(self, args):
        # Here we would re-order args to put
        # those required for prepare first
        return args

    def __repr__(self):
        # Print in lisp format (f arg1 arg2)
        return "({}{}{})".format(
          self.name, " " if self.args else "",
          " ".join(map(repr, self.args))
        )

    def prepare(self, scope, global_scope, args):
        # Called before any calls are evaled. E.g. for a let expression
        return args, scope

    def validate_args(self, final_args):
        """ This method is only called at runtime.
            So that lists will have been expanded
            already, and we can get the true
            number of arguments.
        """
        insert = "" if self.exact else "at least "
        pluralise = "s" if self.num_args != 1 else ""

        if (self.exact and len(final_args) != self.num_args) or \
           (not self.exact and len(final_args) < self.num_args):
            err = "Expected {}{} argument{} for function \"{}\", got {}."
            raise ParsingError(err.format(
                                insert, self.num_args,
                                pluralise, self.name, len(final_args)))


def execute(call, scope, global_scope):
    execute.count += 1
    """
    Python by default doesn't appreciate a lot of recursion.
    Since the language I'm implementing is all about recursion,
    that's a problem.

    That's why this loop is written as one function, with an
    explicit stack.
    This means that the call depth does not increase when you
    have something like:
    (+ (+ (+ 1 2) 3) 4)

    It will still increase if you nest anyting that
    has to execute things in it's "prepare".
    (a sort of "breadth first" execute)

    Which means let, cond, if, user functions etc.
    This new function does help some at least.
    """
    stack = [(None, None, None, None)]
    arg_idx = 0

    while True:
        if not call.resolved_symbols:
            sym_args = []
            for arg in call.args:
                expand, arg = lookup_var(scope, global_scope, arg, call)
                if expand:
                    sym_args.extend(arg)
                else:
                    sym_args.append(arg)

            # Note that argument sorting is *after* resolve/expansion
            sym_args = call.sort_args(sym_args)

            # Now we know the *number* of args we can check that
            if call.validate_on_resolve:
                call.validate_args(sym_args)

            # This bool is a run-once guard for when we break below
            call.resolved_symbols = True

        num_args = len(sym_args)

        # This is a bit of a hack to cope with 0 arguments
        # e.g. fn f with no args (f) after prepare will have
        # the body as an "argument", which we want to execute.
        # Hence the index of -1
        if call.can_prepare(sym_args, -1) and not call.prepared:
            sym_args, scope = call.prepare(scope, global_scope, sym_args)
            # Prepare can remove args
            num_args = len(sym_args)
            call.prepared = True

        while arg_idx < num_args:
            arg = sym_args[arg_idx]
            if isinstance(arg, Call):
                stack.append((sym_args, arg_idx, call, scope))
                arg_idx = 0
                call = arg
                break

            # See if we have enough to prepare.
            # Note that can_prepare wants the idx
            # of the arg we just executed.
            if call.can_prepare(sym_args, arg_idx) and not call.prepared:
                sym_args, scope = call.prepare(scope, global_scope, sym_args)
                # Prepare can add/remove args
                num_args = len(sym_args)
                call.prepared = True

                # Allow the normal while condition to do its
                # job, on a potentially smaller list of args.
                continue

            arg_idx += 1
        else:
            # Have resolved all calls
            if not call.validate_on_resolve:
                call.validate_args(sym_args)

            # Final run
            result = call.apply(scope, global_scope, *sym_args)

            # Go back to parent
            sym_args, arg_idx, call, scope = stack.pop()

            if not stack:
                # If we just popped the initial dummy stack
                # the program has finished.
                return result
            else:
                # Otherwise replace the arg and move to the next one
                sym_args[arg_idx] = result

                # I'm not going to inc arg_idx here, because we'd
                # have to check whether we can prepare again.
                # Just let the while check the same idx again, it'll
                # see that it's not a call anyway.


# For tests to check number of calls
execute.count = 0


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


# NoneCall and TrueCall being any number of args
# means you can use them to ignore return values.
class NoneCall(Call):
    exact = False
    num_args = 0
    name = "none"

    def apply(self, scope, global_scope, *args):
        return None


class TrueCall(Call):
    exact = False
    num_args = 0
    name = "true"

    def apply(self, scope, global_scope, *args):
        return True


class CondCall(Call):
    exact = False
    num_args = 2
    name = "cond"
    validate_on_resolve = True

    def can_prepare(self, args, arg_idx):
        # Executed first half
        return arg_idx == ((len(args)/2)-1)

    def sort_args(self, args):
        # All conditions to the front
        # c1, a1, c2, a2 => c1, c2, a1, a2
        conditions = [args[i] for i in range(0, len(args), 2)]
        actions = [args[i] for i in range(1, len(args), 2)]
        conditions.extend(actions)
        return conditions

    def prepare(self, scope, global_scope, args):
        mid = len(args)//2
        for i in range(mid):
            if args[i]:
                action = args[mid + i]
                # Remove all the actions tied to other conditions
                args = args[:mid]
                args.append(action)
                return args, scope

        # Otherwise do nothing at all
        return args[:mid], scope

    def apply(self, scope, global_scope, *args):
        if len(args) > (len(self.args)/2):
            # The other arg must be the true condition
            return args[-1]
        # Otherwise return None, nothing was done

    def validate_args(self, final_args):
        # Special routine here since let requires
        # matched pairs of name-value, followed by
        # a single body.
        num_args = len(final_args)
        expect = "(cond <condition> <action> ...)"
        if num_args < 2:
            raise ParsingError(
                "cond \"{}\" requires at least 2 arguments. \
Expected {}".format(self, expect))
        elif num_args % 2:
            raise ParsingError(
                "Wrong number arguments for cond \"{}\". \
Expected {}".format(self, expect))


class IfCall(Call):
    exact = False
    num_args = 2
    name = "if"
    validate_on_resolve = True

    def can_prepare(self, args, arg_idx):
        return arg_idx == 0

    def prepare(self, scope, global_scope, args):
        new_args = [args[0]]
        if args[0]:
            # Applies to either then or then and else
            new_args.append(args[1])
        elif len(args) == 3:
            new_args.append(args[2])
        # Only "then" and condition is False, no body to run

        return new_args, scope

    def apply(self, scope, global_scope, *args):
        # The body has already been evaluated by this point
        # The condition is still argument 0
        if len(args) > 1:
            return args[-1]
        # Otherwise None because nothing was done


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
        print(*map(
            lambda v: v.value if isinstance(v, StringVar) else v,
            args))


class LetCall(Call):
    exact = True
    num_args = 3
    name = "let"
    validate_on_resolve = True

    def can_prepare(self, args, arg_idx):
        # -1 for the body, executed last value
        return arg_idx == len(args)-2

    def prepare(self, scope, global_scope, args):
        # This is called before we evaluate the body
        # Inner scope, don't modify outer
        # E.g. (let 'x 1 (let 'y 2 (+ 1 y)) (+ x y))
        # Should be an error, y is only in the inner scope
        scope = copy(scope)

        for k, v in pairs(args[:-1]):
            if isinstance(k, StringVar):
                k = k.value
            # V can be a StringVar, that's fine
            scope[k] = v

        return args, scope

    def validate_args(self, final_args):
        # Special routine here since let requires
        # matched pairs of name-value, followed by
        # a single body.
        num_args = len(final_args)
        expect = "(let <name> <value> ... (body))"
        if num_args < 3:
            raise ParsingError(
                "Too few arguments for let \"{}\". \
Expected {}".format(self, expect))
        elif not num_args % 2:
            raise ParsingError(
                "Wrong number arguments for let \"{}\". \
Expected {}".format(self, expect))

    def apply(self, scope, global_scope, *args):
        # The body has been executed by this point
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
        flat = []

        def _flatten(_ls):
            try:
                for l in _ls:
                    if isinstance(l, StringVar):
                        flat.append(l)
                    else:
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
    validate_on_resolve = True

    def prepare(self, scope, global_scope, args):
        with open(args[0].value, 'r') as f:
            _, global_scope = run_source_inner(
                f.read(), global_scope=global_scope)
        return (), scope

    def apply(self, scope, global_scope, *args):
        pass


class BaseUserCall(Call):
    def can_prepare(self, args, arg_idx):
        # About to execute the body
        return arg_idx >= (len(args)-1)

    def validate_args(self, final_args):
        # Ignore fn body added by prepare
        super().validate_args(final_args[:-1])

    def prepare(self, scope, global_scope, args):
        scope = dict()

        # Make star empty as default in case they only
        # call with positional args. It must still be defined.
        if self.arg_names and self.arg_names[-1] == "*":
            scope["*"] = ()

        for idx in range(len(self.arg_names)):
            if self.arg_names[idx] == "*":
                # Tuple just to keep printing consistent
                scope["*"] = tuple(args[idx:])
                break
            try:
                scope[self.arg_names[idx]] = args[idx]
            except IndexError:
                # Dummy since body hasn't been added yet
                args.append(None)
                # We validated that MaybeFunctionCall had the right args.
                # Now check that the actual call we got is correct.
                self.validate_args(args)

        # Now we want the body to run
        # deepcopy so that prepared flags aren't set
        # next time we run this body
        args.append(deepcopy(self.body))
        return args, scope

    def apply(self, scope, global_scope, *args):
        # The result of the fn body
        return args[-1]


class DefineFunctionCall(Call):
    exact = False
    num_args = 2
    name = "defun"
    validate_on_resolve = True

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

    def prepare(self, scope, global_scope, args):
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
        self.body = args.pop()
        return args, scope

    def apply(self, scope, global_scope, *args):
        # Add a new Call type to global scope
        # Remember that the body of the function
        # was stashed in self in prepare.

        # Note the name and args have the ' removed by now
        name = args[0]
        if isinstance(name, StringVar):
            name = name.value
        args = args[1:]

        global_scope[name] = type(
            "UserCall_{}".format(name),
            (BaseUserCall,),
            {
                "exact": not self.variadic,
                "name": name,
                # Don't count the *
                "num_args": len(args)-1 if self.variadic else len(args),
                "arg_names": args,
                "variadic": self.variadic,
                "body": self.body
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
    num_args = 1
    exact = False

    def __init__(self, *args):
        # Name is just for printing
        self.name = args[0]
        # Note the name of the fn is included as the first argument
        super().__init__(*args)

    def __repr__(self):
        # Custom repr because the name of the fn is arg[0]
        name = self.args[0]
        args = self.args[1:]
        return "({}{}{})".format(
          name, " " if args else "",
          " ".join(map(repr, args))
        )

    def can_prepare(self, args, arg_idx):
        # Executed the name part
        # (name could be a fn call itself)
        return arg_idx == (len(self.args)-1)

    def prepare(self, scope, global_scope, args):
        # The "name" could be the result of a function,
        # that returns a new function. In that case we can
        # just use the value directly.
        real_fn = args[0]

        # Check if it's a class first otherwise we get:
        # TypeError: cannot create weak reference to '<bla>' object
        # For anything that isn't a class type.
        if not inspect.isclass(real_fn) or not issubclass(real_fn, Call):
            _, real_fn = lookup_var(scope, global_scope,
                                    real_fn, self)
            if isinstance(real_fn, StringVar):
                real_fn = StringVar.value

        # Don't need the name anymore
        args = args[1:]

        # Check that a lookup did return a call type
        if not inspect.isclass(real_fn) or not issubclass(real_fn, Call):
            msg = "\"{}\" is not a function, it is {} ({}). (in \"{}\")"
            raise RuntimeError(msg.format(
                self.name, type(real_fn), real_fn, self))

        # Make an instance of it, with the resolved arguments
        real_fn = real_fn(*args)

        # Add it as an "argument" to the current call
        # So it gets executed after args are resolved
        args.append(real_fn)
        return args, scope

    def apply(self, scope, global_scope, *args):
        # The result of the real function
        return args[-1]


builtin_calls = {v.name: v for v in Call.__subclasses__()}


def make_call(fn_name, args, global_scope):
    try:
        return global_scope[fn_name](*args)
    except KeyError:
        # Maybe this is a user func defined later
        return MaybeFunctionCall(fn_name, *args)


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
        symbol = StringVar(symbol)

    return symbol, idx


def process_call(src, idx, global_scope):
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
    # TODO: you can't use # in a string, or ( )
    # this needs to be more context aware

    # <space><bracket><space> => <bracket>
    return re.sub(r"\s*([\(\)])\s*", r"\g<1>",
                  # <space> n times => <space>
                  re.sub(r"\s+", " ",
                         # remove comments
                         re.sub(r"#.*(\n)?", "", source)))


# Call this one when you want to get the resulting global scope
def run_source_inner(source, global_scope=None):
    if global_scope is None:
        """ No need for a deep copy here,
            the Classes will stay the same.
            Just don't want other fns hanging
            around between runs. """
        global_scope = copy(builtin_calls)

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
            result = execute(body, {}, global_scope)

    # program's return value is the return of the last block
    return result, global_scope


def run_source(source):
    return run_source_inner(source)[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LispALike interpreter')
    parser.add_argument('filename', nargs='?',
                        help="File to interpret. (optional)")
    args = parser.parse_args()

    if args.filename is None:
        raise RuntimeError("Filename is required if not running tests.")
    with open(args.filename) as f:
        print(run_source(f.read()))
