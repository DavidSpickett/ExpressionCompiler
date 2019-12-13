(import "lib/lib.ls")

(defun 'fizzbuzz 'n
  (body
    (cond
      (eq (% n 3) 0)
        (cond
          (eq (% n 5) 0) (print "FizzBuzz")
          (true)         (print "Fizz")
        )
      (eq (% n 5) 0) (print "Buzz")
      (true)         (print n)
    )
    # >97 reaches Python's maximum recursion depth
    (if (< n 97)
      (fizzbuzz (+ n 1))
    )
  )
)

(fizzbuzz 1)
