![](https://github.com/DavidSpickett/ExpressionCompiler/workflows/ExpressionCompiler/badge.svg)

Simple parser/compiler for Lisp style expressions. For example:
```
(+ (- 4 2) 3) => 5
```

To run an example:
```
python main.py examples/FizzBuzz.ls
```

There is a simple Flask application to run code from a web browser. To run:
```
$ cd flask/
$ export FLASK_APP=app.py
$ flask run
```
