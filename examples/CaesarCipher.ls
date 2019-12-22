(import "lib/lib.ls")

# Assuming only upper case ASCII A-Z
(defun 'caeser 'in 'key
  # Wrap keys within the range of the letters
  (let 'key (% key 26)
    (accumulate
      +
      (map
        (lambda (list 'key) 'c
          (cond
            (eq c " ") (+ c)
            (true)
              (let 'new_code (+ (chartoint c) key)
                (let 'wrapped_code
                  (cond
                    (>= new_code 91) (+ 65 (% new_code 91))
                    (< new_code 65) (- 91 (- 65 new_code))
                    (true) (+ new_code)
                  )
                  (inttochar wrapped_code)
                )
              )
          )
        )
        in
      )
      ""
    )
  )
)
(defun 'encode 'input 'key
  (caeser input key)
)
(defun 'decode 'input 'key
  (caeser input (- key))
)

(let 'in "THE QUICK BROWN FOX JUMPED OVER THE LAZY DOG" 'key 3
  (let 'encoded (encode in key)
    (body
      (print "Encoding:" in "Key:" key)
      (print " Encoded:" encoded)
      (print " Decoded:" (decode encoded key))
    )
  )
)

(defun 'find_key 'encoded 'expected
  (body
    (defun 'attempt_decode 'encoded 'key 'expected
      (let 'got (decode encoded key)
        (let 'matches_until
          # First point where the plaintext doesn't match the expected
          (findif
            (lambda (list 'expected) 'idx 'v
              # If everything in expected matched
              (if (>= idx (len expected))
                (true)
                # Otherwise break as soon as expected != plaintext
                (neq (nth idx expected) v)
              )
            )
            got
          )
          # If we matched expected completely
          (if (>= matches_until (len expected))
            (+ (list got key))
            # Otherwise try the next key
            (attempt_decode encoded (+ key 1) expected)
          )
        )
      )
    )
    (attempt_decode encoded 0 expected)
  )
)

# Key here is deliberatley >65 to show decode can handle it
(let 'in "NOW IS THE WINTER OF OUR DISCONTENT" 'key 67
  (let 'encoded (encode in key)
    (body
      (let 'got (find_key encoded "NOW")
        (body
          (print "Decoding:" encoded)
          (print " Decoded:" (head got) "Found key:" (last got))
        )
      )
    )
  )
)
