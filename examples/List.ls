(import "lib/lib.ls")

(let 'ls (list 1 2 3 4)
  (body
    (print "The list:" ls)
    (print "The expanded list:" *ls)

    (print "Head:" (head ls))
    (print "Last:" (last ls))
    (print "Tail:" (tail ls))

    (print "Apply function:")
    (defun 't 'x (print x))
    (apply 'v ls t)

    (print "Apply anonymous Function:")
    (apply 'v ls
      (defun ' 'v
        (print v)
      )
    )

    (print "Reverse:" (reverse ls))
  )
)
