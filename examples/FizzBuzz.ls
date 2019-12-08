(import "lib/lib.ls")

(defun 'fizzbuzz 'n
  # So we only see one None not 99 nested
  (last
    (list
      (if (eq (% n 3) 0)
        (if (eq (% n 5) 0)
          # Divides exactly by 3 and 5
          (print "FizzBuzz")
          # Divides exactly by only 3
          (print "Fizz")
        )
        (if (eq (% n 5) 0)
          # Only divides exactly by 5
          (print "Buzz")
          # Anything else
          (print n)
        )
      )
      # >97 reaches Python's maximum recursion depth
      (if (< n 97)
        (fizzbuzz (+ n 1))
      )
    )
  )
)

(fizzbuzz 1)
