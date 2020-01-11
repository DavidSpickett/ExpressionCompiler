import string
import re
import argparse
from copy import copy
from calls import builtin_calls, StringVar
from calls import Call, MaybeFunctionCall, lookup_var


class ParsingError(Exception):
    pass


# This call is here to avoid circular import of run_source_inner
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


builtin_calls["import"] = ImportCall


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
