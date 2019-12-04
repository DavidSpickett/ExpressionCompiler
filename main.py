import string
import re
import math
import operator
from abc import ABC
from functools import reduce

class ParsingError(Exception):
  pass

class Call(ABC):
  def __init__(self, *args):
    self.args = args

  def __repr__(self):
    return "{}({})".format(
      self.name,
      ", ".join(map(repr, self.args))
    )

  def execute(self):
    """
    >>> Call.execute(PlusCall(1, 2))
    3
    >>> Call.execute(PlusCall(1, 2))
    3
    >>> Call.execute(PlusCall(1, 2, 3, 4))
    10
    >>> Call.execute(MinusCall(PlusCall(4, 3), 4))
    3
    >>> Call.execute(SquareRootCall(4))
    2.0
    >>> Call.execute(PlusCall(SquareRootCall(16), MinusCall(12, 13)))
    3.0
    """
    result = None
    prev_arg = None

    if len(self.args) == 1:
      arg = self.args[0]
      if isinstance(arg, Call):
        arg = arg.execute()
      return self.apply(arg)

    # First pass resolves all calls
    new_args = []
    for arg in self.args:
      if isinstance(arg, Call):
        arg = arg.execute()
      new_args.append(arg)
   
    """    
    Now all arguments are constants
    Remember that we validated the number of args
    when we built the Call objects.
    """
    return self.apply(*new_args)

class PlusCall(Call):
  exact = False
  num_args = 2
  name = "+"

  def apply(self, *args):
    return sum(args)

class MinusCall(Call):
  exact = False
  num_args = 2
  name = "-"

  def apply(self, *args):
    return reduce(operator.sub, args)

class SquareRootCall(Call):
  exact = True
  num_args = 1
  name = "sqrt"

  def apply(self, a):
    return math.sqrt(a)

def make_call(operator, args):
  """
  >>> make_call("ooo", [])
  Traceback (most recent call last):
  ParsingError: Call to unknown function "ooo".
  >>> make_call("sqrt", [])
  Traceback (most recent call last):
  ParsingError: Expected 1 argument for function "sqrt", got 0.
  >>> make_call("sqrt", [2, 3])
  Traceback (most recent call last):
  ParsingError: Expected 1 argument for function "sqrt", got 2.
  >>> make_call("+", [])
  Traceback (most recent call last):
  ParsingError: Expected at least 2 arguments for function "+", got 0.
  >>> make_call("-", [1])
  Traceback (most recent call last):
  ParsingError: Expected at least 2 arguments for function "-", got 1.
  
  """
  calls = [
    PlusCall,
    MinusCall,
    SquareRootCall,
  ]
  found_type = None

  if isinstance(operator, Call):
    # Functions cannot return callables
    raise ParsingError("Expected function name, got a call to a function.")

  for call_type in calls:
    if call_type.name == operator:
      found_type = call_type
      break
     
  if found_type:
    insert = "" if found_type.exact else "at least "
    pluralise = "s" if found_type.num_args != 1 else ""

    if (found_type.exact and len(args) != call_type.num_args) or \
       (not found_type.exact and len(args) < call_type.num_args):
        raise ParsingError("Expected {}{} argument{} for function \"{}\", got {}.".format(
          insert, found_type.num_args, pluralise, call_type.name, len(args)))

    return call_type(*args)
  else:
    raise ParsingError("Call to unknown function \"{}\".".format(operator))

def convert_arg(arg):
  """
  >>> convert_arg(PlusCall())
  +()
  >>> convert_arg("1")
  1
  >>> convert_arg("foo")
  Traceback (most recent call last):
  ValueError: Non integer arguments not supported.
  """
  # Convert from strings in the source into Python types
  if isinstance(arg, Call):
    return arg

  try:
    return int(arg)
  except ValueError:
    raise ValueError("Non integer arguments not supported.")

def get_symbol(src, idx):
  delimiters = ["(", ")"]
  delimiters.extend(string.whitespace)

  symbol = ""
  while src[idx] not in delimiters:
    symbol += src[idx]
    idx += 1

  return symbol, idx

def process_call(src, idx=0):
  """
  >>> process_call("(+ 1 2 3 4 5 6)")[0]
  +(1, 2, 3, 4, 5, 6)
  >>> process_call("(- (+ 1 (- 1 2)) 5)")[0]
  -(+(1, -(1, 2)), 5)
  >>> process_call("((+ 1 2))")[0]
  Traceback (most recent call last):
  ParsingError: Expected function name, got a call to a function.
  """ 
  if src[idx] != "(":
    raise ParsingError("Call must begin with \"(\".")

  idx += 1
  operator = None
  args = []

  while idx < len(src):
    if src[idx] == "(":
      call, idx = process_call(src, idx)
      if operator is None:
        operator = call
      else:
        args.append(call)
    elif src[idx] == ")":
      assert operator != None
      # Note the +1 here to consume the closing bracket
      return make_call(operator, args), idx+1
    elif src[idx] in string.whitespace:
      # Whitespace around () will have been removed but
      # it is still in between arguments
      idx += 1 
    else:
      symbol, idx = get_symbol(src, idx)
      if symbol:
        if operator is None:
          operator = symbol
        else:
          args.append(convert_arg(symbol))

def normalise(source):
  """
  >>> normalise("   ( foo )")
  '(foo)'
  >>> normalise("(    foo (bar 1  2 ))")
  '(foo(bar 1 2))'
  """
  return re.sub("\s*([\(\)])\s*", "\g<1>",
    re.sub("\s+", " ", source))

def process(source):
  if not source:
    return

  source = normalise(source)
  current = iter(source)
  prog, _ = process_call(source)
  return prog

def run_source(source):
  """
  >>> run_source("")
  >>> run_source("(+ 1 2)")
  3
  >>> run_source("(sqrt (+ 2 2))")
  2.0
  """
  prog = process(source)
  if prog:
    return prog.execute()

if __name__ == "__main__":
  import doctest
  doctest.testmod()
