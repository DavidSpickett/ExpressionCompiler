# https://www.rosettacode.org/wiki/ABC_Problem

(import "lib/lib.ls")

# Possible improvement: this will just take the first thing
# that matches regardless of the other letter on the block.
# This might prevent further matches.
(defun 'get_letter 'l 'blocks 'used
  (body
    (let 'got
      (findif
        (lambda (list 'l 'used) 'idx 'block
          # If the letter we want is on the block
          # check for none not false, since 0 is falsey
          # but also a valid index
          (body
            (if (neq (find l block) (none))
              (body
                (if (eq (find idx used) (none))
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
          (list
            (true)
            (+ used (list got))
          )
        )
      )
    )
  )
)

(defun 'can_make_string 'str 'blocks
  (if (empty str)
    (true)
    (body
      (defun '__inner 'str 'idx 'blocks 'used
        (let 'got
          (get_letter (nth idx str) blocks used)
          (body
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
(check_word "CONFUSE")
