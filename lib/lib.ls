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

#TODO: do I even need a true call?
# eq 1 1
(defun 'false '*
  (not (true))
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
  (body
    (defun '__map_inner 'fn 'first '*
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
  (body
    (defun '__accumulate_inner 'fn 'total 'first '*
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
  (body
    (defun '__reverse_inner '_ls
      (body
        (if (eq (len _ls) 1)
          (+ _ls)
          (list
            (__reverse_inner (tail _ls))
            (+ (head _ls))
          )
        )
      )
    )
    (flatten (__reverse_inner ls))
  )
)

(defun 'findif 'predicate 'ls
  (if (empty ls)
    (none)
    (body
      (defun '__findif_inner 'idx 'ls 'pred
        # Predicate also gets the index.
        # A bit weird but it makes one of the
        # examples easier.
        (if (pred idx (nth idx ls))
          (+ idx)
          (if (neq idx (- (len ls) 1))
            (__findif_inner (+ idx 1) ls pred)
          )
        )
      )
      (__findif_inner 0 ls predicate)
    )
  )
)

# find v in ls, return its index
(defun 'find 'v 'ls
  (body
    (defun '__find_get_v v)
    (findif
      (defun ' 'idx 'val
        (eq val (__find_get_v))
      )
      ls
    )
  )
)
