# import collections
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
  
  

def is_valid_int_pair_tuple(int_tuple):
  return isinstance(int_tuple, tuple) and len(int_tuple) == 2 and all(isinstance(item, int) for item in int_tuple), int_tuple

def nand(a, b):
  return not (a and b)
  
def at_most_one(input_list):
  return sum(bool(item) for item in input_list) in (0, 1)

def xor(a, b):
  return a ^ b
  
# _print_once_
# def print_once(*args, **kwargs)


def rjust_tuple(input_tuple, fill_value, length):
  assert isinstance(input_tuple, tuple)
  if len(input_tuple) >= length:
    return input_tuple
  else:
    return (fill_value,)*(length-len(input_tuple)) + input_tuple
assert rjust_tuple((3,4,5), 0, 5) == (0,0,3,4,5)
assert rjust_tuple((3,4,5), 0, 2) == (3,4,5)


def lflag_is_first(input_iterable):
  for i, item in enumerate(input_iterable):
    yield (i==0, item)


def first_half_of(input_sliceable):
  assert hasattr(input_sliceable, "__len__")
  assert len(input_sliceable)%2 == 0
  return input_sliceable[:len(input_sliceable)//2]