# TODO: This is nice but for the recursion limit
# (defun 'len 'ls
#   (if (empty ls)
#     (+ 0)
#     (+ 1
#       (len
#         (tail ls)
#       )
#     )
#   )
# )

(defun 'last 'ls
  (nth -1 ls)
)

(defun 'head 'ls
  (let 'f
    (defun ' 'head '*
      (+ head)
    )
    (f *ls)
  )
)

(defun 'tail 'ls
  (let 'f
    (defun ' 'head '*
      (+ *)
    )
    (f *ls)
  )
)

(defun 'init 'ls
  (reverse (tail (reverse ls)))
)

# TODO: we need a first arg here so that
# "eq" gets at least two for parsing. If it's just
# ** then that's counted as one argument when building
# the call object.
(defun 'neq 'first '*
  (not (eq first **))
)

(defun 'empty 'ls
  (if (eq (len ls) 0)
    (+ 1)
  )
)

(defun 'body 'call '*
  (if (empty *)
    (+ call)
    (last
      (list
        (+ call)
        (last *)
      )
    )
  )
)

(defun 'list '*
  (+ *)
)

(defun 'map 'fn 'ls
  (let '__map_inner
    (defun ' 'fn 'first '*
      (if (empty *)
        (fn first)
        (list
          (fn first)
          (__map_inner fn **)
        )
      )
    )
    (flatten
      (__map_inner fn *ls)
    )
  )
)

(defun 'apply 'fn 'ls
  (none (map fn ls))
)

(defun 'accumulate 'fn 'ls 'initial
  (let '__accumulate_inner
    (defun ' 'fn 'total 'first '*
      (if (empty *)
        (fn total first)
        (__accumulate_inner fn
          (fn total first)
          **
        )
      )
    )
    (__accumulate_inner fn initial *ls)
  )
)

(defun 'reverse 'ls
  (let 'f
    (defun ' '_ls
      (body
        (if (eq (len _ls) 1)
          (+ _ls)
          (list
            (f (tail _ls))
            (+ (head _ls))
          )
        )
      )
    )
    (flatten (f ls))
  )
)
