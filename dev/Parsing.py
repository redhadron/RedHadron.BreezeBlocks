

# project
from Utilities import assert_equals, assert_isinstance
from Affixes import remove_prefix


# ----- helpers for name parsing -----
class ParseResult:
  pass
  
class ParseSuccess(ParseResult):
  def __init__(self, matched_data, remaining_text):
    self.matched_data, self.remaining_text = matched_data, remaining_text
  def __repr__(self):
    assert type(self) is ParseSuccess, "__repr__ is not available for subclasses yet"
    return f"ParseSuccess(matched_data={self.matched_data}, remaining_text={self.remaining_text!r})"
  def assert_complete_and_get_matched_data(self):
    assert len(self.remaining_text) == 0, self.remaining_text
    return self.matched_data
    
class ParseFailure(ParseResult):
  def __init__(self, message):
    self.message = message
    
  def __repr__(self):
    assert type(self) is ParseFailure, "__repr__ is not available for subclasses yet"
    return f"ParseFailure(message={self.message})"

class ParseError(Exception):
  """ this is not used for control flow, only for gathering more information during an actual error """
  pass

def parse_string_as_structure(input_string, structure):
  # this method contains reassignment to input_string # TODO
  if len(input_string) == 0:
    return ParseFailure("Parsing an empty input string is bad.") # this is a ParseFailure and not an exception because it needs to be recognized as a non-crash failure in whatever method called it recursively, such as in the case where you are trying to parse (#p#n #p) from string "#p" - #p#n must fail safely for #p to later succeed.
  if isinstance(structure, str):
    if input_string.startswith(structure):
      return ParseSuccess(structure, remove_prefix(input_string, structure))
    return ParseFailure("failure while parsing with string structure.")
  elif isinstance(structure, tuple):
    for item in structure:
      result = parse_string_as_structure(input_string, item)
      if isinstance(result, ParseSuccess):
        return ParseSuccess((result.matched_data,), result.remaining_text)
      else:
        assert isinstance(result, ParseFailure)
    return ParseFailure(f"parsing tuple failed: could not parse any option provided by the tuple {structure} with the input {input_string}.")
  else:
    assert isinstance(structure, list)
    listResult = list()
    for item in structure:
      try:
        itemResult = parse_string_as_structure(input_string, item)
      except Exception as e:
        raise ParseError(f"could not parse the string {input_string} with the structure {structure}, while attempting to parse with sub-structure {item} the following exception occurred:\n {e}")
      if isinstance(itemResult, ParseFailure):
        return ParseFailure("failure while parsing with list structure: " + itemResult.message)
      else:
        assert isinstance(itemResult, ParseSuccess)
        listResult.append(itemResult.matched_data)
        input_string = itemResult.remaining_text
        # if len(input_string) == 0:
          # break
        continue
    assert len(listResult) > 0, "what?"
    return ParseSuccess(listResult, input_string)
  assert False
assert_equals(parse_string_as_structure("abc", ["a","b","c"]).matched_data, ["a","b","c"])
assert_equals(parse_string_as_structure("adc", ["a",("b","d"),"c"]).matched_data, ["a",("d",),"c"])
assert_equals(parse_string_as_structure("amnz", ["a",["m","n"],"z"]).matched_data, ["a",["m","n"],"z"])
assert_equals(parse_string_as_structure("amnz", ["a",["m",("l","m","n","o","p")],"z"]).matched_data, ["a",["m",("n",)],"z"])
assert_equals(parse_string_as_structure("anz", ["a",(("l","m"),("n","o")),"z"]).matched_data, ["a",(("n",),),"z"])
assert_equals(parse_string_as_structure("abc", ["a","b","","c"]).matched_data, ["a","b","","c"])
# match leftmost possible match first:
assert_equals(parse_string_as_structure("amnz", ["a",(["m","n","o"],["m","n"]),"z"]).matched_data, ["a",(["m","n"],),"z"])
assert_equals(parse_string_as_structure("amnz", ["a",(["m","n"],["m","n","z"]),"z"]).matched_data, ["a",(["m","n"],),"z"])

def flatten_string_structure(input_structure):
  if isinstance(input_structure, str):
    return input_structure
  else:
    assert_isinstance(input_structure, (list, tuple))
    result = []
    for item in input_structure:
      itemResult = flatten_string_structure(item)
      if isinstance(itemResult, str):
        result.append(itemResult)
      else:
        assert_isinstance(itemResult, (list,tuple))
        result.extend(itemResult)
    return result
assert_equals(flatten_string_structure(["a",("b",),["c"],["d","e"],("f","g"),[("h","i"),"j",("k","l"),["m"]]]), "a b c d e f g h i j k l m".split(" "))

def flatten_string_structure_and_join(input_structure):
  return "".join(flatten_string_structure(input_structure))
