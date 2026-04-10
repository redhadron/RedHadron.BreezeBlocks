

from Utilities import int_divide_exact






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
  
  
def lstrip_and_count(text: str, prefix: str) -> tuple[str, int]:
  assert len(prefix) > 0
  resultStr = text.lstrip(prefix)
  return (resultStr, int_divide_exact(len(text)-len(resultStr), len(prefix)))

def rstrip_and_count(text: str, suffix: str) -> tuple[str, int]:
  assert len(suffix) > 0
  resultStr = text.rstrip(suffix)
  return (resultStr, int_divide_exact(len(text)-len(resultStr), len(suffix)))