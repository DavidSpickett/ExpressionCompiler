from main import *  # noqa: F403 F401


def test_pairs():
    """
    >>> list(pairs((1,)))
    Traceback (most recent call last):
    IndexError: tuple index out of range
    >>> list(pairs((1, 2)))
    [(1, 2)]
    >>> list(pairs((1, 2, 3)))
    Traceback (most recent call last):
    IndexError: tuple index out of range
    >>> list(pairs((1, 2, 3, 4)))
    [(1, 2), (3, 4)]
    """
    pass


def test_normalise():
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
    pass


def test_execute():
    """
    >>> execute(PlusCall(1, 2), {}, {})
    3
    >>> execute(PlusCall(1, 2), {}, {})
    3
    >>> execute(PlusCall(1, 2, 3, 4), {}, {})
    10
    >>> execute(MinusCall(PlusCall(4, 3), 4), {}, {})
    3
    >>> execute(SquareRootCall(4), {}, {})
    2.0
    >>> execute(
    ...     PlusCall(
    ...         SquareRootCall(16),
    ...         MinusCall(12, 13)
    ...     ), {}, {})
    3.0
    >>> execute(PlusCall("foo", "bar"), {"foo":1, "bar":2}, {})
    3
    >>> execute(SquareRootCall("abc"), {}, {})
    Traceback (most recent call last):
    main.ParsingError: Reference to unknown symbol "abc" in "(sqrt 'abc')".
    >>> # Note that this var name is *not* escaped
    >>> execute(LetCall("foo", 2, PlusCall("foo", 5)), {}, {})
    Traceback (most recent call last):
    main.ParsingError: Reference to unknown symbol "foo" \
in "(let 'foo' 2 (+ 'foo' 5))".
    >>> # Whereas this one is
    >>> execute(LetCall("'bar", 16, SquareRootCall("bar")), {}, {})
    4.0
    >>> execute(EqualCall(1, 2), {}, {})
    False
    >>> execute(EqualCall(1, 1, 1, 1), {}, {})
    True
    >>> # Show that the body is not evaluated
    >>> execute(
    ...     DefineFunctionCall("'x", "'y", PlusCall("x", "y")), {}, {})
    <class 'abc.UserCall_x'>
    >>> execute(SquareRootCall(), {}, {})
    Traceback (most recent call last):
    main.ParsingError: Expected 1 argument for function "sqrt", got 0.
    >>> execute(LetCall(1, 2), {}, {})
    Traceback (most recent call last):
    main.ParsingError: Too few arguments for let "(let 1 2)". \
Expected (let <name> <value> ... (body))
    >>> execute(LetCall(1, 2, 3, 4), {}, {})
    Traceback (most recent call last):
    main.ParsingError: Wrong number arguments for let "(let 1 2 3 4)". \
Expected (let <name> <value> ... (body))
    """
    pass


def test_flatten_call():
    """
    >>> FlattenCall.apply(None, {}, {}, [])
    ()
    >>> FlattenCall("foo").apply({}, {}, 1)
    Traceback (most recent call last):
    main.ParsingError: Flatten "(flatten 'foo')" not called with a list.
    >>> FlattenCall.apply(None, {}, {}, [1, 2, 3])
    (1, 2, 3)
    >>> FlattenCall.apply(None, {}, {}, [[1, 2], 3])
    (1, 2, 3)
    >>> FlattenCall.apply(None, {}, {}, [[[1, 2]], [3], [4, [5]]])
    (1, 2, 3, 4, 5)
    """
    pass


def test_make_call():
    """
    >>> # User function names aren't resolved here
    >>> make_call("ooo", [], {})
    (ooo)
    >>> # Number of args is checked at runtime not here
    >>> make_call("+", [], {})
    (+)
    """
    pass


def test_process_call():
    """
    >>> process_call("+ 1 2)", 0, {})
    Traceback (most recent call last):
    main.ParsingError: Call must begin with "(".
    >>> process_call("(+ 1 2", 0, {})
    Traceback (most recent call last):
    main.ParsingError: Unterminated call to function "+"
    >>> process_call("(- (sqrt 2", 0, {})
    Traceback (most recent call last):
    main.ParsingError: Unterminated call to function "sqrt"
    >>> process_call("(+ 1 2 3 4 5 6)", 0, {})[0]
    (+ '1' '2' '3' '4' '5' '6')
    >>> process_call("(- (+ 1 (- 1 2)) 5)", 0, {})[0]
    (- (+ '1' (- '1' '2')) '5')
    >>> # This will become a MaybeFunctionCall, with the +
    >>> # call run later and then we check if it returns a fn
    >>> process_call("((+ '1' '2'))", 0, {})[0]
    ((+ "'1'" "'2'"))
    """
    pass


def test_run_source():
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
    main.ParsingError: Reference to unknown symbol "y" in "(+ 'x' 'y')".
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
    main.ParsingError: Expected 1 argument for function "x", got 2.
    >>> run_source("(defun 'x 'y (+ y)) (x))")
    Traceback (most recent call last):
    main.ParsingError: Expected 1 argument for function "x", got 0.
    >>> # This does not define "bar"
    >>> run_source(
    ... "(if (+ 1)\\
    ...     (defun 'foo 'x (+ x))\\
    ...     (defun 'bar 'x (+ x))\\
    ...  )\\
    ...  (foo 1)\\
    ...  (bar 2)")
    Traceback (most recent call last):
    main.ParsingError: Reference to unknown symbol "bar" in "(bar '2')".
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
    main.ParsingError: "'*" must be the last parameter if present.
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
    >>> run_source(
    ... "(defun 'f 'x (print x))\\
    ...  (f)")
    Traceback (most recent call last):
    main.ParsingError: Expected 1 argument for function "f", got 0.
    >>> run_source(
    ... "(defun 'f 'x 'y '* (+ 0))\\
    ...  (f 1 2 3 4)\\
    ...  (f 1 2 3)\\
    ...  (f 1 2)\\
    ...  (f 1)")
    Traceback (most recent call last):
    RuntimeError: Wrong number of arguments for function \
"f" in "(f '1')". Got 1, expected at least 2.
    >>> # Check that let replaces it's arguments with evaluated
    >>> # versions. Otherwise this will print foo twice.
    >>> run_source(
    ... "(defun 'f (print \\"foo\\"))\\
    ...  (let 'a (f) (print \\"bar\\"))")
    foo
    bar
    >>> # Argument validation delayed until execution time
    >>> # If we didn't, the * would count as one and be an error.
    >>> run_source(
    ... "(import \\"lib/lib.ls\\")\\
    ...  (let 'ls (list 1 2)\\
    ...    (+ *ls)\\
    ...  )")
    3
    >>> # Built in functions should also be in the global scope
    >>> run_source(
    ... "(defun 'f 'otherf '* (otherf **))\\
    ...  (f + 1 2 3)")
    6
    >>> # You can call a function that is returned from another function
    >>> run_source("((+ (defun ' 'x (print x))) 2)")
    2
    >>> run_source("((+ +) 2 2)")
    4
    >>> # Calling something that doesn't return a fn is an error
    >>> run_source("((+ 2) 1)")
    Traceback (most recent call last):
    RuntimeError: "(+ '2')" is not a function, it is 2. (in "((+ '2') '1')")
    >>> # At least 2 args
    >>> run_source("(cond (+0))")
    Traceback (most recent call last):
    main.ParsingError: cond "(cond (+0))" requires at least 2 arguments. \
Expected (cond <condition> <action> ...)
    >>> # Must be matched pairs of arguments
    >>> run_source("(cond (+ 0) (+ 0) (+ 1))")
    Traceback (most recent call last):
    main.ParsingError: Wrong number arguments for cond "(cond (+ '0') (+ '0') \
(+ '1'))". Expected (cond <condition> <action> ...)
    >>> run_source("(cond (+ 0) (+ 5) (+ 1) (+ 6))")
    6
    >>> # Nothing matches, nothing returned
    >>> run_source("(cond (eq 1 2) (+ 1) (eq 2 3) (+ 2))")
    >>> # First true condition wins
    >>> run_source("(cond (eq 1 1) (+ 1) (eq 2 2) (+ 2))")
    1
    >>> run_source("(true (eq 1 0))")
    True
    """
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()
