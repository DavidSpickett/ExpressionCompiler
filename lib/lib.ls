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

(defun 'map 'varname 'ls 'fn
  (let '__map_inner
    (defun ' 'varname 'ls 'fn 'idx
      (if (neq idx (- (len ls) 1))
        (let 'v (nth idx ls)
          (list
            (fn v)
            (__map_inner varname ls fn (+ idx 1))
          )
        )
        (fn (nth idx ls))
      )
    )
    (flatten
      (__map_inner varname ls fn 0)
    )
  )
)

# Apply fn to all items of ls, return nothing
(defun 'apply 'varname 'ls 'fn
  (none (map varname ls fn))
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
