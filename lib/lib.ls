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

(defun 'neq '*
  (not (eq **))
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
        # List so that flatten always gets a list
        (list
          (fn first)
        )
        (list
          (fn first)
          (__map_inner fn **)
        )
      )
    )
    (cond
      (empty ls) (list)
      (true)
        (flatten (__map_inner fn *ls))
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

# find v in ls, return its index
(defun 'find 'v 'ls
  (let '__inner
    (defun ' 'v 'idx 'ls
      (if (eq v (nth idx ls))
        (+ idx)
        (if (neq idx (- (len ls) 1))
          (__inner v (+ idx 1) ls)
        )
      )
    )
    (__inner v 0 ls)
  )
)
