![](https://github.com/DavidSpickett/ExpressionCompiler/workflows/ExpressionCompiler/badge.svg)

Parser/runner for a Lisp like language.
```
(defun 'f 'n
  (body
    (print n)
    (if (< n 5)
      (f (+ n 1)) 
    ) 
  )
)

(f 0)
```
```
0
1
2
3
4
5
None
```

To run a source file:
```
python main.py examples/FizzBuzz.ls
```

There is a simple Flask application to run code from a web browser.
```
$ cd flask/
$ export FLASK_APP=app.py
$ flask run
```
