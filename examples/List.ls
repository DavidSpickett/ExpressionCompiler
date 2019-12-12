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
          (body
            (+ x 2)
          )
        )
        ls
      )
      (print "Map with + 2:" m)
    )

    (print "Accumulate:"
      # TODO: a builtin like "+" should be allowed for 'fn
      (accumulate
        (defun ' 'x 'y (+ x y))
        ls 0)
    )

    (print "Reverse:" (reverse ls))
  )
)
