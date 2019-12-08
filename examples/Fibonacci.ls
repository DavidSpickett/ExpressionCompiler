(import "lib/lib.ls")

(defun 'fib 'x 'y
  (let 'n (+ x y)
    (last
      (list
        (print n)
        (if (< n 100)
          (fib y n)
        )
      )
    )
  )
)

(print 0)
(print 1)
(fib 0 1)
