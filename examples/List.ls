(import "lib/lib.ls")

(let 'ls (list 1 2 3 4)
  (body
    (print "The list:" ls)
    (print "The expanded list:" *ls)

    (print "Head:" (head ls))
    (print "Last:" (last ls))
    (print "Tail:" (tail ls))
    (print "Init:" (init ls))

    (print "Apply function:")
    (defun 't 'x (print x))
    (print (apply t ls))

    (print "Apply anonymous Function:")
    (let 'a
      (apply
        (defun ' 'v
          (print v)
        )
        ls
      )
      (print a)
    )

    (let 'm
      (map
        (defun ' 'x
          (+ x 2)
        )
        ls
      )
      (print "Map with + 2:" m)
    )

    (let 'm
      (map
        (defun ' 'x
          (neq x 3)
        )
        ls
      )
      (print "Map with neq 3:" m)
    )

    (print "Accumulate:"
      (accumulate + ls 0)
    )

    (defun 'is_even 'n
      (eq (% n 2) 0)
    )
    (print "Filter (evens):"
      (filter is_even ls)
    )
    (print "Filter (odds):"
      (filter
        (lambda (list) 'n (not (is_even n)))
        ls
      )
    )

    (print "Reverse:" (reverse ls))
  )
)

(let 'ls (list 1)
  (body
    (print "On single item list:" ls)
    (print "Map:" (map + ls))
    (print "Apply:" (apply + ls))
    (print "Accumulate" (accumulate + ls 0))
  )
)

(let 'ls (list)
  (body
    (print "On empty list:" ls)
    (print "Map:" (map + ls))
    (print "Apply:" (apply + ls))
    (print "Accumulate:" (accumulate + ls 1))
  )
)
