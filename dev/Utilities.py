
# builtin:
import itertools




def assert_equals(a, b):
  if a == b:
    return
  hints = [f"{a} does not equal {b}."]
  if type(a) != type(b):
    hints.append(f"they are different types ({type(a)} vs {type(b)}).")
  if hasattr(a, "__len__") and hasattr(b, "__len__"):
    if len(a) != len(b):
      hints.append(f"they are different in length ({len(a)} vs {len(b)}).")
    else:
      hints.append("while comparing items:")
      try:
        for i, aItem, bItem in zip(itertools.count(), a, b):
          assert_equals(aItem, bItem)
      except AssertionError as ae:
        hints.append(f"at index {i}:")
        hints.append(repr(ae))
  raise AssertionError("\n".join(hints))
  
def assert_isinstance(a, b):
  assert isinstance(a, b), (a, b)
  
# def assert_is_empty(a):
  # assert len(a) == 0, a
  
def int_divide_exact(a,b):
  assert isinstance(a, int) and isinstance(b,int)
  assert a%b == 0
  return a // b
  
  

def validate_int_pair_tuple(int_tuple):
  assert isinstance(int_tuple, tuple) and len(int_tuple) == 2 and all(isinstance(item, int) for item in int_tuple), int_tuple

def nand(a, b):
  return not (a and b)
  
def at_most_one(input_list):
  return sum(bool(item) for item in input_list) in (0, 1)