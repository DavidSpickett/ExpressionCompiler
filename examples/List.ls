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
    (print (apply 'v ls t))

    (print "Apply anonymous Function:")
    (let 'a
      (apply 'v ls
        (defun ' 'v
          (print v)
        )
      )
      (print a)
    )

    (let 'm
      (map 'v ls
        (defun ' 'x
          (body
            (+ x 2)
          )
        )
      )
      (print "Map with + 2:" m)
    )

    (print "Reverse:" (reverse ls))
  )
)
