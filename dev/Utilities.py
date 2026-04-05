
# builtin:
import itertools


def remove_suffix(string, suffix):
  assert len(suffix) <= len(string)
  # assert len(suffix) > 0
  assert string.endswith(suffix), string + " does not end with " + suffix
  return string[:-len(suffix)]
  
def remove_prefix(string, prefix):
  assert len(prefix) <= len(string)
  # assert len(prefix) > 0
  assert string.startswith(prefix), string + " does not start with " + prefix
  return string[len(prefix):]

def shorten_suffix(string, suffix, new_suffix):
  assert suffix.startswith(new_suffix), "the suffixes do not have a matching beginning"
  assert len(new_suffix) < len(suffix)
  return remove_suffix(string, suffix) + new_suffix
  
def bisect_at_infix(string, infix):
  assert string.count(infix) == 1
  a, b = string.split(infix)
  return (a, b)

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