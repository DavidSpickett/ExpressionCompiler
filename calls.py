import operator
import inspect
from abc import ABC
from math import sqrt
from functools import reduce
from copy import copy, deepcopy


def pairs(it):
    return ((it[i], it[i+1]) for i in range(0, len(it), 2))


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
            raise RuntimeError(msg.format(arg, current_call))

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
            raise RuntimeError(err.format(
                                insert, self.num_args,
                                pluralise, self.name, len(final_args)))


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


class CharToIntCall(Call):
    exact = True
    num_args = 1
    name = "chartoint"

    def apply(self, scope, global_scope, c):
        return ord(c.value)


class IntToCharCall(Call):
    exact = True
    num_args = 1
    name = "inttochar"

    def apply(self, scope, global_scope, i):
        return StringVar(chr(i))


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
            raise RuntimeError(
                "cond \"{}\" requires at least 2 arguments. \
Expected {}".format(self, expect))
        elif num_args % 2:
            raise RuntimeError(
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
        return sqrt(a)


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
            raise RuntimeError(
                "Too few arguments for let \"{}\". \
Expected {}".format(self, expect))
        elif not num_args % 2:
            raise RuntimeError(
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
                raise RuntimeError(
                    "Flatten \"{}\" not called with a list.".format(self))

        _flatten(ls)

        # Tuple for consistency when printing
        return tuple(flat)


class BaseUserCall(Call):
    def can_prepare(self, args, arg_idx):
        # About to execute the body
        return arg_idx >= (len(args)-1)

    def validate_args(self, final_args):
        # Ignore fn body added by prepare
        super().validate_args(final_args[:-1])

    def prepare(self, scope, global_scope, args):
        scope = dict()

        # Add lambda captured vars
        scope.update(self.captures)

        # Make star empty as default in case they only
        # call with positional args. It must still be defined.
        if self.variadic:
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

        # Variables captured from the local scope
        # as the fn is defined. This will only be filled
        # in for lambdas.
        self.captures = dict()

        self.variadic = False
        var = "'*"
        if var in self.args:
            if self.args.index(var) != len(self.args)-2:
                raise RuntimeError("\
\"{}\" must be the last parameter if present.".format(var))
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
                "body": self.body,
                "captures": self.captures,
            }
        )

        # Return the function itself, so it can be used as an argument
        return global_scope[name]


class LambdaFunctionCall(DefineFunctionCall):
    name = "lambda"

    def apply(self, scope, global_scope, *args):
        capture_names = args[0]
        self.captures = dict()
        # Get the values of these variables now at definition time
        for name in capture_names:
            expand, self.captures[name] = lookup_var(
                scope, global_scope, name, self)
            assert not expand

        # Lambdas are always anonymous
        args = ('',) + args[1:]

        return super().apply(scope, global_scope, *args)


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
                real_fn = real_fn.value

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


def subclasses(cls):
    classes = set()
    for c in cls.__subclasses__():
        classes.add(c)
        classes.update(subclasses(c))

    return classes


builtin_calls = {v.name: v for v in subclasses(Call)}
