(defun 'last 'ls
  (nth -1 ls)
)

(defun 'body 'call '*
  (if (eq (len *) 0)
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
