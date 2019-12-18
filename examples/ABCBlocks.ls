(import "lib/lib.ls")

(defun 'get_letter 'l 'blocks 'used
  (let 'got
    (findif
      (defun ' 'block
        # If the letter we want is on the block
        # check for none not false, since 0 is falsey
        # but also a valid index
        (body
          (print "Find result:" (find l block))
          (if (neq (find l block) (none))
            (body
              (print "found" l "in" block)
              # If the block has not been used
              (if (eq (find block used) (none))
                (true)
              )
            )
          )
        )
      )
      blocks
    )
    (if (eq got (none))
      (list (none) used)
      # Add found block to used list
      (body
        (print "found" l "at index" got)
        (list 
          (true) 
          (+ used 
            (list (nth got blocks))
          )
        )
      )
    )
  )
)

(defun 'can_make_string 'str 'blocks
  (if (empty str)
    (true)
    (let '__inner 
      (defun ' 'str 'idx 'blocks 'used
        (let 'got
          (get_letter (nth idx str) blocks used)
          (body
            (print (nth idx str) "got" got)
            # If we found something
            (if (nth 0 got)
              (if (neq idx (- (len str) 1))
                # Search for next char, using new list of used blocks
                (__inner str (+ idx 1) blocks (nth 1 got))
                # End of string found all chars
                (true)
              )
              # Failed to find char, can't make string
              (false)
            )
          )
        )
      )
      (__inner str 0 blocks (list))
    )
  )
)

(defun 'check_word 'word
  (let
    'blocks (list
    (list "B" "O") (list "X" "K") (list "D" "Q") (list "C" "P")
    (list "N" "A") (list "G" "T") (list "R" "E") (list "T" "G")
    (list "Q" "D") (list "F" "S") (list "J" "W") (list "H" "U")
    (list "V" "I") (list "A" "N") (list "O" "B") (list "E" "R")
    (list "F" "S") (list "L" "Y") (list "P" "C") (list "Z" "M")
    )
    (print word ":" (can_make_string word blocks))
  )
)

(check_word "A")
(check_word "BARK")
(check_word "BOOK")
(check_word "TREAT")
(check_word "COMMON")
(check_word "SQUAD")
# TODO: this fails because when it finds F/S for the S
# it adds (list "F" "S") to the used, which means *both*
# F/S blocks now can't be used. I should store indexes instead
# problem with that is that I don't have access to the index
# during a findif predicate call
(check_word "CONFUSE")
