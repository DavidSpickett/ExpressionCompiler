(import "lib/lib.ls")

(defun 'encode 'c 'direction
  (let
    'chars (list
      "A"    "B"    "C"    "D"    "E"   "F"    "G"   "H"
      "I"    "J"    "K"    "L"    "M"   "N"    "O"   "P"
      "Q"    "R"    "S"    "T"    "U"   "V"    "W"   "X"
      "Y"    "Z"    " ")
    'morse (list
      ".-"   "-..." "-.-." "-.."  "."   "..-." "--." "...."
      ".."   ".---" "-.-"  ".-.." "--"  "-."   "---" ".--."
      "--.-" ".-."  "..."  "-"    "..-" "...-" ".--" "-..-"
      "-.--" "--.." "/")
    # True = text to morse
    (if direction
        (+ (nth (find c chars) morse) " ")
        (nth (find c morse) chars)
    )
  )
)

(defun 'translate 'chars 'dir
  (accumulate +
    (map
      # Wrapper to pass 2 args to encode above
      (defun ' 'c
        (encode c dir)
      )
      chars)
    ""
  )
)
(defun 'to_morse   'chars (translate chars (true)))
(defun 'from_morse 'chars (translate chars (none)))

(print
  (to_morse
    (str_to_list "THE QUICK BROWN FOX")
  )
)
(print
  (from_morse
    (list "-"   "...." "."   "/" "--.-" "..-"
          ".."  "-.-." "-.-" "/" "-..." ".-."
          "---" ".--"  "-."  "/" "..-." "---"
          "-..-")
  )
)
