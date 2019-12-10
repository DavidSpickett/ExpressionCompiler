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

# Apply fn to all items of ls, return nothing
(defun 'apply 'varname 'ls 'fn
  (let '__apply_inner
    (defun ' 'varname 'ls 'fn 'idx
      (if (< idx (len ls))
        (let 'v (nth idx ls)
          (body
            (fn v)
            (__apply_inner varname ls fn (+ idx 1))
          )
        )
      )
    )
    (__apply_inner varname ls fn 0)
  )
)

(defun 'reverse 'ls
  (let 'f
    (defun ' '_ls
      (body
        (if (eq (len _ls) 1)
          (nth 0 _ls)
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
