# builtin
import time
START_TIME = time.monotonic()
import os
import shutil
import itertools
import pathlib
import codecs # for portuguese file encoding
import re
import functools
import urllib # for libretranslate error handling
import subprocess # for png crushing
import asyncio
import sys # to use sys.exit inside async

# project
from HYTALE import HYTALE_ASSETS_PATH, SEP, HYTALE_BLOCKTEXTURES_PATH, HYTALE_BLOCKTEXTURE_FILE_NAMES
import ProcessPooling

BAD_EXIT_CODE = 1

# pip
from PIL import Image, ImageChops
from tibs import Tibs
import shelve
from libretranslatepy import LibreTranslateAPI
LIBRETRANSLATE_API = LibreTranslateAPI("http://127.0.0.1:5000") # recommended args for libretranslate: --disable-web-ui --translation-cache all
try:
  LIBRETRANSLATE_SUPPORTED_LANGUAGE_CODES = [item["code"] for item in LIBRETRANSLATE_API.languages()]
except urllib.error.URLError:
  print("failed to communicate with libretranslate. Are you running a libretranslate server on the default port? https://docs.libretranslate.com/")
  exit(BAD_EXIT_CODE)
import psutil

# PNG_OPTIMIZATION_DO_POOLING = True
USE_HYPERTHREADING = False
PNG_OPTIMIZATION_SIMULTANEOUS_PROCESSES = 2 # psutil.cpu_count(logical=USE_HYPERTHREADING)
PNG_OPTIMIZATION_PROCESS_POOLER = ProcessPooling.Pooler(PNG_OPTIMIZATION_SIMULTANEOUS_PROCESSES)


  
HYTALE_STOCK_LANGUAGE_CODES = ["en-US", "pt-BR", "ru-RU", "uk-UA"]
BREEZE_BLOCKS_NATIVE_LANGUAGE_CODE = "en-US"
BREEZE_BLOCKS_LANGUAGE_CODES = HYTALE_STOCK_LANGUAGE_CODES
LANGUAGE_CODE_LIBRETRANSLATE_SUBSTITUTIONS = {originalCode: originalCode if originalCode in LIBRETRANSLATE_SUPPORTED_LANGUAGE_CODES else originalCode.split("-")[0] if originalCode.split("-")[0] in LIBRETRANSLATE_SUPPORTED_LANGUAGE_CODES else None for originalCode in BREEZE_BLOCKS_LANGUAGE_CODES}
# for languageCode in HYTALE_STOCK_FOREIGN_LANGUAGE_CODES
#for lang in HYTALE_STOCK_FOREIGN_LANGUAGE_CODES:
  # assert lang in LIBRETRANSLATE_SUPPORTED_LANGUAGE_CODES, (lang, LIBRETRANSLATE_SUPPORTED_LANGUAGE_CODES)
# exit()

PARTICLE_COLORATION = "channelwise_median_snapped_to_input_color" # a key provided by colors.py in colors.shelf
ICON_BACKGROUND_INVERSION_THRESHOLD = 0 # brightness at or below which the background will be inverted from black to white.





"""
todo:
replace readline with read
rename thumbnails to icons
"""







# ----- assertion helpers -----
  
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
  
  

# ----- helpers for working with data pages -----
# data pages are lists of tuples. They are used instead of dictionaries to preserve order and to allow duplicate entries.

_unspecified_default = object()
def data_page_get_value(data_page, key, default=_unspecified_default):
  assert isinstance(data_page, list)
  if isinstance(key, tuple):
    innerItem = data_page_get_value(data_page, key[0], default=default)
    if len(key) > 1:
      return data_page_get_value(innerItem, key[1:], default=default)
    else:
      return innerItem
  elif isinstance(key, str):
    for item in data_page:
      assert len(item) == 2 and isinstance(item[0], str)
      if item[0] == key:
        return item[1]
    if default is _unspecified_default:
      raise KeyError(key)
    else:
      return default
  else:
    raise TypeError(type(key))
    
def data_page_has_key(data_page, key):
  assert isinstance(key, (str, tuple))
  if isinstance(key, tuple):
    raise NotImplementedError("tuple keys presence test")
  assert isinstance(data_page, list)
  return any(item[0] == key for item in data_page)




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

# ----- mod-specific patterns -----

ALPHABET_LOWERCASE_PATTERN = tuple([*"abcdefghijklmnopqrstuvwxyz"])
ALPHABET_UPPERCASE_PATTERN = tuple(char.upper() for char in ALPHABET_LOWERCASE_PATTERN)
SHAPE_NAME_PATTERN = [ALPHABET_UPPERCASE_PATTERN] + ([ALPHABET_LOWERCASE_PATTERN]*3)
MULTI_SHAPE_NAME_PATTERN = ([SHAPE_NAME_PATTERN]*4, SHAPE_NAME_PATTERN)
DIGITS = ("0","1","2","3","4","5","6","7","8","9") # this constant is used for other things besides string structure parsing
DIGIT_PATTERN = DIGITS 
# OPTIONAL_DIGIT_PATTERN = DIGIT_PATTERN + ("",)
CREATE_UNSIGNED_INTEGER_PATTERN = lambda maxLength: tuple([DIGIT_PATTERN]*i for i in range(maxLength,0,-1))
CREATE_UNIVERSAL_NUMBER_PATTERN = lambda maxIntegerLength: tuple(
  list(itertools.chain(*zip(itertools.repeat(CREATE_UNSIGNED_INTEGER_PATTERN(maxIntegerLength)), charProvisionsStr))) for charProvisionsStr in ["pnd", "pn", "pd", "p", "nd", "n", "d"]
)
GRID_PATTERN = ["G", DIGIT_PATTERN, "x", DIGIT_PATTERN]
# considering the rightmost letter in a charProvisionsStr list, all strings with that letter must occur before all strings without that letter, so that the letter is never missed due to a pattern getting matched that didn't include that letter, but could have.

proper_bin = lambda x: remove_prefix(bin(x), "0b")

def get_char_provision_strings(input_string):
  # get a list of all strings that can be made by toggling whether each character from the input string is present in the output string, while ensuring that no string in this list is a prefix to another string that comes later in this list.
  # this is useful for parsing a block of text which may contain any of these optional letters in a known order, and doing so in a single step (if strings in the output list could be prefixes to later strings, parsing would not consume as many characters as possible, and multiple parsing steps would be necessary.)
  result = []
  for i in range(2**len(input_string)-1, 0, -1):
    presencesStr = proper_bin(i)[::-1].ljust(len(input_string), "0")
    presences = [{"1":True, "0":False}[item] for item in presencesStr]
    result.append("".join(char for present, char in zip(presences, input_string) if present))
  return result
assert_equals(get_char_provision_strings("abc"), ["abc", "bc", "ac", "c", "ab", "b", "a"])

CREATE_SIZE_DESCRIPTION_PATTERN = lambda maxIntegerLength: tuple(list(itertools.chain([char, CREATE_UNIVERSAL_NUMBER_PATTERN(maxIntegerLength)] for char in charProvisionsStr)) for charProvisionsStr in get_char_provision_strings("TFDBL"))
MAX_UNIVERSAL_NUMBER_COMPONENT_DIGITS = 2









# ----- helpers specific to Hytale -----

BRICK_TEXTURE_NAME_SUBSTRING_COSTS = {"Cobble": 100, "Corner": 1000, "Ornate": 150, "Decorative": 175, "Top":20, "Side":21, "Smooth":30, "0":1, "1":2, "2":3, "3":4, "4":5, "5":6, "6":7, "7":8, "8":9, "9":10} # the texture with the lowest score will be chosen when an exact match to the predicted texture name is not found.

def patch_wood_texture_name(input_string):
  return input_string.replace("Wood_Softwood_Planks.png", "Wood_Softwood_Planks_Top.png").replace("Wood_Greenwood_Planks.png", "Wood_Green.png")

def select_best_texture_name_by_cost(required_substring, substring_costs):
  assert isinstance(required_substring, str) and isinstance(substring_costs, dict)
  costOfName = lambda inputName: sum(inputName.count(substringValue)*substringCost for substringValue, substringCost in substring_costs.items())*1024 + len(inputName)
  try:
    bestName = min((name for name in HYTALE_BLOCKTEXTURE_FILE_NAMES if required_substring in name), key=costOfName)
  except ValueError:
    raise ValueError(f"search failed with {required_substring=}")
  return bestName

def select_best_texture_file_name(*, base_name):
  assert isinstance(base_name, str), type(base_name)
  if base_name.startswith("Wood_"):
    return patch_wood_texture_name(base_name + ".png")
  elif base_name.startswith("Rock_"):
    assert base_name.endswith("_Brick") or base_name.endswith("_Brick_Smooth"), base_name
    for oldSubstr, newSubstr in ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS.items():
      # this must happen first because "peachstone" (And maybe similar things) are detected for the the Rock_ prefix removal logic \/
      base_name = base_name.replace(f"_{oldSubstr}_", f"_{newSubstr}_")
    for rockType in ROCK_BRICK_TEXTURE_NAME_NO_ROCK_PREFIX_REQUIRED:
      if base_name.startswith(f"Rock_{rockType}_"):
        base_name = rockType + "_" + remove_prefix(base_name, f"Rock_{rockType}_")
    return select_best_texture_name_by_cost(base_name, BRICK_TEXTURE_NAME_SUBSTRING_COSTS)
  elif base_name.startswith("Metal_"):
    return base_name + ".png"
  elif base_name.startswith("Clay_"):
    return base_name + ".png"
  elif base_name.startswith("Soil_Clay_"):
    raise ValueError("Clay textures do not begin with the word Soil in Hytale: bad base name: " + base_name)
  else:
    raise NotImplementedError("unimplemented or incorrect prefix for: " + base_name)
    
def color_tuple_to_hytale_string(input_color):
  assert len(input_color) == 3
  assert all(isinstance(component, int) and 0 <= component <= 255 for component in input_color)
  return "#" + "".join(Tibs.from_u(component, 8).to_hex().rjust(2, "0") for component in input_color)
assert_equals(color_tuple_to_hytale_string((255, 254, 0)), "#fffe00")









# ----- Hytale game data constants -----

CLAY_COLORS = "Black Blue Cyan Green Grey Lime Orange Pink Purple Red White Yellow".split()

# ROCK_BRICK_NO_TEXTURE_NAME_PROCESSING_REQUIRED = list("Basalt Quartzite Shale Stone Volcanic".split(" ")) # non-exhaustive # maybe add chalk
ROCK_BRICK = "Aqua Basalt Calcite Chalk Ledge Lime Marble Peach Quartzite Sandstone Sandstone_Red Sandstone_White Shale Stone Volcanic".split(" ")
# in-game ID = Rock_(value)_Brick
# in-game name = ROCK_BRICK_NAME_UPGRADES[value] + " Brick"
ROCK_RUNIC_BRICK = "Runic_Blue Runic Runic_Teal Runic_Dark".split(" ") # the texture names on these are so bad that I am boycotting them.
ROCK_BRICK_BUT_ACTUALLY_METAL = ["Gold"]
METAL = ["Iron", "Bronze", "Copper", "Zinc"]

ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS = {"Ledge": "Ledgestone", "Lime":"Limestone", "Peach":"Peachstone"}
ROCK_BRICK_TEXTURE_NAME_NO_ROCK_PREFIX_REQUIRED = ["Peachstone", "Calcite", "Runic_Brick_Dark", "Runic_Brick_Dark_Blue"]
_ROCK_BRICK_DISPLAY_NAME_TRANSLATIONS = {"Runic_Blue": "Blue Runic", "Runic_Teal": "Dark Blue Runic", "Runic_Dark": "Dark Runic", "Sandstone_Red":"Red Sandstone", "Sandstone_White": "White Sandstone"}

PROTOTYPE_ROCK_BRICKS = "Concrete".split(" ")
SOIL_BRICK = "Hive Hive_Corrupted Clay Clay_Ocean Snow"
_SOIL_BRICK_DISPLAY_NAME_TRANSLATIONS = {"Hive_Corrupted": "Corrupted Hive", "Clay_Ocean": "Ocean Clay"}
#  Aqua Calcite Gold Ledge Lime Marble # these are available as smooth bricks in-game but their textures have irregular names.


UNIFIED_DISPLAY_NAME_TRANSLATIONS = dict(list(_ROCK_BRICK_DISPLAY_NAME_TRANSLATIONS.items()) + list(_SOIL_BRICK_DISPLAY_NAME_TRANSLATIONS.items()) + list(ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS.items()))







# ----- structured data about how to generate assets -----

DATA_PAGES = [
  [ # ----- Wood plank -----
    ("PRIVATE_TYPE", "Wood"), # this is used in the name of the asset file but might not be included in the file as a type tag.
    ("TEXTURE_NAME_PREFIX", "Wood_"),
    ("FAMILY_LIST", list("Blackwood Darkwood Deadwood Drywood Goldenwood Greenwood Hardwood Lightwood Redwood Softwood Tropicalwood".split(" "))),
    ("TEXTURE_NAME_SUFFIX_LIST", ["_Planks"]),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", False),
    ("AUTOMATIC_JSON_ITEMS", [
      ("JSON_CATEGORIES_LINE", r'"Blocks.Structural"'), # TODO check again later whether a wood category exists. 
      ("JSON_RECIPE_INPUT_REQUIREMENT_KEY_STR", "ResourceTypeId"),
      ("JSON_RECIPE_INPUT_REQUIREMENT_VALUE_STR", "Wood_${FAMILY}"),
      ("JSON_TAGS_TYPE", '"Type": [ "Wood" ]'),
      ("JSON_TAGS_SUBTYPE", ",\n    \"SubType\": [\n      \"Planks\"\n    ]"),
      ("JSON_TAGS_FAMILY", ",\n    \"Family\": [\n      \"${FAMILY}\"\n    ]"),
      ("JSON_BLOCKTYPE_GROUP_LINE", "\n"), # there's a group for stone, but not for rock.
      ("JSON_BLOCKTYPE_GATHERING_BREAKING_GATHERTYPE_STR", "Woods"),
      ("JSON_BLOCKTYPE_BLOCKPARTICLESETID_STR", "Wood"),
      ("JSON_FUEL_QUALITY_LINE", "\"FuelQuality\": 0.75,"),
      ("JSON_BLOCKTYPE_BLOCKSOUNDSETID_STR", "Wood"),
      ("JSON_ITEMSOUNDSETID_STR", "ISS_Blocks_Wood"),
    ]),
    
  ],
  [ # ----- Rock Brick (excluding Gold) -----
    ("PRIVATE_TYPE", "Rock"),
    ("TEXTURE_NAME_PREFIX", "Rock_"),
    ("FAMILY_LIST", ROCK_BRICK),
    ("TEXTURE_NAME_SUFFIX_LIST", ["_Brick"]),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", False),
    ("AUTOMATIC_JSON_ITEMS", [
      ("JSON_CATEGORIES_LINE", r'"Blocks.Rocks", "Blocks.Structural"'),
      ("JSON_RECIPE_INPUT_REQUIREMENT_KEY_STR", "ResourceTypeId"),
      ("JSON_RECIPE_INPUT_REQUIREMENT_VALUE_STR", "Rock_${FAMILY}_Brick"),
      ("JSON_TAGS_TYPE", '"Type": [ "Rock" ]'),
      ("JSON_TAGS_SUBTYPE", ""),
      ("JSON_TAGS_FAMILY", ",\n    \"Family\": [\n      \"${FAMILY}\"\n    ]"),
      ("JSON_BLOCKTYPE_GROUP_LINE", ""),
      ("JSON_BLOCKTYPE_GATHERING_BREAKING_GATHERTYPE_STR", "Rocks"),
      ("JSON_BLOCKTYPE_BLOCKPARTICLESETID_STR", "Stone"),
      ("JSON_FUEL_QUALITY_LINE", "\n"),
      ("JSON_BLOCKTYPE_BLOCKSOUNDSETID_STR", "Stone"),
      ("JSON_ITEMSOUNDSETID_STR", "ISS_Blocks_Stone"),
    ]),
  ],
  [ # ----- Gold Brick (both a rock and a metal) -----
    ("PRIVATE_TYPE", "Rock"),
    ("TEXTURE_NAME_PREFIX", "Rock_"),
    ("FAMILY_LIST", ROCK_BRICK_BUT_ACTUALLY_METAL),
    ("TEXTURE_NAME_SUFFIX_LIST", ["_Brick"]),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", False),
    ("AUTOMATIC_JSON_ITEMS", [
      ("JSON_CATEGORIES_LINE", r'"Blocks.Metal", "Blocks.Structural"'),
      ("JSON_RECIPE_INPUT_REQUIREMENT_KEY_STR", "ResourceTypeId"),
      ("JSON_RECIPE_INPUT_REQUIREMENT_VALUE_STR", "Rock_${FAMILY}_Brick"),
      ("JSON_TAGS_TYPE", '"Type": [ "Rock" ]'), # best option for gold as of update 4
      ("JSON_TAGS_SUBTYPE", ""),
      ("JSON_TAGS_FAMILY", ",\n    \"Family\": [\n      \"${FAMILY}\"\n    ]"),
      ("JSON_BLOCKTYPE_GROUP_LINE", '"Group": "Metal",\n'), # this seems to control which creative inventory category it shows up in.
      ("JSON_BLOCKTYPE_GATHERING_BREAKING_GATHERTYPE_STR", "Rocks"), # best option for gold as of hytale update 4
      ("JSON_BLOCKTYPE_BLOCKPARTICLESETID_STR", "Metal"),
      ("JSON_FUEL_QUALITY_LINE", ""),
      ("JSON_BLOCKTYPE_BLOCKSOUNDSETID_STR", "Metal"),
      ("JSON_ITEMSOUNDSETID_STR", "ISS_Items_Metal"),
    ]),
  ],
  [ # ----- Metal (excluding Gold) -----
    ("PRIVATE_TYPE", "Metal"),
    ("TEXTURE_NAME_PREFIX", "Metal_"),
    ("FAMILY_LIST", METAL),
    ("TEXTURE_NAME_SUFFIX_LIST", [""]),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", False),
    ("AUTOMATIC_JSON_ITEMS", [
      ("JSON_CATEGORIES_LINE", r'"Blocks.Metal", "Blocks.Structural"'),
      ("JSON_RECIPE_INPUT_REQUIREMENT_KEY_STR", "ItemId"),
      ("JSON_RECIPE_INPUT_REQUIREMENT_VALUE_STR", "Ingredient_Bar_${FAMILY}"),
      ("JSON_TAGS_TYPE", ""),
      ("JSON_TAGS_SUBTYPE", ""),
      ("JSON_TAGS_FAMILY", ""),
      ("JSON_BLOCKTYPE_GROUP_LINE", '"Group": "Metal",\n'),
      ("JSON_BLOCKTYPE_GATHERING_BREAKING_GATHERTYPE_STR", "Rocks"),
      ("JSON_BLOCKTYPE_BLOCKPARTICLESETID_STR", "Metal"),
      ("JSON_FUEL_QUALITY_LINE", ""),
      ("JSON_BLOCKTYPE_BLOCKSOUNDSETID_STR", "Metal"),
      ("JSON_ITEMSOUNDSETID_STR", "ISS_Items_Metal"),
    ]),
  ],
]

PROTOTYPE_DATA_PAGES = [
  [
    ("TEXTURE_NAME_PREFIX", ""),
    ("FAMILY_LIST", ["Clay"]),
    ("TEXTURE_NAME_SUFFIX_LIST", list("_"+item for item in CLAY_COLORS)),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", True), # this flag exists because of clay.
    ("AUTOMATIC_JSON_ITEMS", [
      ("JSON_CATEGORIES_LINE", r'"Blocks.Soils", "Blocks.Structural"'), # ?
      ("JSON_RECIPE_INPUT_RESOURCETYPEID_STR", "Soil_${FAMILY}${TEXTURE_NAME_SUFFIX}"),
      ("JSON_TAGS_TYPE_STR", "Rock"),
      ("JSON_TAGS_SUBTYPE", ""),
      ("JSON_TAGS_FAMILY", ",\n    \"Family\": [\n      \"${FAMILY}\"\n    ]"),
      ("JSON_BLOCKTYPE_GATHERING_BREAKING_GATHERTYPE_STR", "Rocks"),
      ("JSON_BLOCKTYPE_BLOCKPARTICLESETID_STR", "Stone"),
      ("JSON_FUEL_QUALITY_LINE", ""),
      ("JSON_BLOCKTYPE_BLOCKSOUNDSETID_STR", "Stone"),
      ("JSON_ITEMSOUNDSETID_STR", "ISS_Blocks_Stone"),
    ]),
  ],
]





# ----- display name translation -----

SHAPE_NICKNAMES_TO_NAMES = {"Hair": "Crosshair", "Head": "Empty Crosshair", "SlowNeckNeckSlow": "Bottleneck Basketweave"}

SHAPE_NAME_TRANSLATION_CORRECTIONS = {
  "uk":{"Empty Crosshair":"порожнє перехрестя", "Crosshair":"перехрестя", "Dice":"грати в кості", "Nope":"Ні", "Bottleneck Basketweave":"схема плетіння Вузьке місце", "Void":"порожній"},
  "ru":{"Dice":"Игральные кости", "Nope":"Вычеркнуто", "Bottleneck Basketweave":"Переплетение узких мест"}
}

def dictionary_translate_if_able(dictionary, key):
  return dictionary.get(key, key)

def split_and_keep_delimeters(text, delimeters, keep_empty_strings):
  regexPattern = "(["+"".join("\\"+item for item in delimeters)+"])"
  result = re.split(regexPattern, text)
  return result if keep_empty_strings else [item for item in result if len(item) > 0]
US_KEYBOARD_SYMBOLS = r'`~!@#$%^&*()-_+=[{]}\|;:",<.>/? ' + "'"
for testChar0 in US_KEYBOARD_SYMBOLS:
  for testChar1 in US_KEYBOARD_SYMBOLS:
    _testTup = ("a", testChar0, "b", testChar1, "c", testChar0, testChar1, "d", testChar1, testChar0, "e")
  assert_equals(tuple(split_and_keep_delimeters("".join(_testTup), [testChar0, testChar1], False)), _testTup)
del _testTup

def lstrip_and_count(text, prefix):
  assert len(prefix) > 0
  resultStr = text.lstrip(prefix)
  return (resultStr, int_divide_exact(len(text)-len(resultStr), len(prefix)))

def rstrip_and_count(text, suffix):
  assert len(suffix) > 0
  resultStr = text.rstrip(suffix)
  return (resultStr, int_divide_exact(len(text)-len(resultStr), len(suffix)))

@functools.cache
def cached_libretranslate_call(text, source, target):
  # functools cache here offers significant speedup even when caching is turned on for the libretranslate instance
  if source == "en":
    if target in SHAPE_NAME_TRANSLATION_CORRECTIONS:
      if text in SHAPE_NAME_TRANSLATION_CORRECTIONS[target]:
        return SHAPE_NAME_TRANSLATION_CORRECTIONS[target][text]
  return LIBRETRANSLATE_API.translate(text, source, target)

def translate_with_flavor(text, source, target):
  # flavor includes whitespace and ellipses and other things that might be removed by the translation model. They should always be provided to the translation model in case they improve the output. If the translation model removes them, they should be added back in.
  if source == target:
    return text # don't translate from a language to itself
  assert len(text) > 0
  assert len(text.lstrip(" ")) > 0
  if "..." in text:
    raise NotImplementedError("ellipses")
  textWOLeft, leftSpaceCount = lstrip_and_count(text, " ")
  textWOLeftRight, rightSpaceCount = rstrip_and_count(textWOLeft, " ")
  translationResult = cached_libretranslate_call(textWOLeftRight, source=LANGUAGE_CODE_LIBRETRANSLATE_SUBSTITUTIONS[source], target=LANGUAGE_CODE_LIBRETRANSLATE_SUBSTITUTIONS[target])
  return (" "*leftSpaceCount) + translationResult.lstrip(" ").rstrip(" ") + (" "*rightSpaceCount)

def translate_string_piecewise(text, source, target, delimeters):
  if source == target:
    return text # don't translate from a language to itself
  inputPieces = split_and_keep_delimeters(text, delimeters, keep_empty_strings=False)
  assert all(len(piece) > 0 for piece in inputPieces)
  isTranslatable = lambda string: not (string in delimeters or any(digit in string for digit in DIGITS))
  outputPieces = [translate_with_flavor(piece, source, target) if isTranslatable(piece) else piece for piece in inputPieces]
  return "".join(outputPieces)
  
  
  


# ----- mod path constants -----

def is_a_valid_mod(modPath):
  assert os.path.exists(modPath)
  return all(item in os.listdir(modPath) for item in ["Common", "Server"])
  
# TODO Manifest.json copying

if os.getcwd().count("dev") > 1:
  raise NotImplementedError()
assert not os.getcwd().endswith(SEP)

MOD_NAME = "RedHadron.BreezeBlocks"
assert MOD_NAME in os.getcwd()
MOD_SOURCE_PATH = shorten_suffix(os.getcwd(), SEP+MOD_NAME+SEP+"dev", SEP+MOD_NAME) if os.getcwd().endswith(SEP+"dev") else os.getcwd()
assert is_a_valid_mod(MOD_SOURCE_PATH) and "dev" in os.listdir(MOD_SOURCE_PATH), "mod source path or structure may be invalid"
MOD_DESTINATION_PATH = SEP.join([MOD_SOURCE_PATH, "..", "..", "mods", MOD_NAME])
assert is_a_valid_mod(MOD_DESTINATION_PATH), "Not a valid mod: " + MOD_DESTINATION_PATH
assert "dev" not in os.listdir(MOD_DESTINATION_PATH), "mod destination path or structure may be invalid: " + MOD_DESTINATION_PATH

MODEL_FOLDER_SUBPATH = SEP.join(["Common", "Blocks", "Breeze"])
MODEL_FOLDER_SOURCE_PATH = SEP.join([MOD_SOURCE_PATH, MODEL_FOLDER_SUBPATH])
MODEL_FOLDER_DESTINATION_PATH = SEP.join([MOD_DESTINATION_PATH, MODEL_FOLDER_SUBPATH])
assert os.path.exists(MODEL_FOLDER_SOURCE_PATH), MODEL_FOLDER_SOURCE_PATH
assert os.path.exists(MODEL_FOLDER_DESTINATION_PATH), MODEL_FOLDER_DESTINATION_PATH

ASSET_FOLDER_SUBPATH = SEP.join(["Server", "Item", "Items"])
ASSET_FOLDER_DESTINATION_PATH = MOD_DESTINATION_PATH + SEP + ASSET_FOLDER_SUBPATH
assert os.path.exists(ASSET_FOLDER_DESTINATION_PATH), ASSET_FOLDER_DESTINATION_PATH

ICON_FOLDER_SUBPATH = SEP.join(["Common", "Icons", "ItemsGenerated"])
ICON_FOLDER_DESTINATION_PATH = MOD_DESTINATION_PATH + SEP + ICON_FOLDER_SUBPATH
assert os.path.exists(ICON_FOLDER_DESTINATION_PATH), ICON_FOLDER_DESTINATION_PATH

TEMPLATE_FILE_SUBPATH = "dev" + SEP + "Breeze_Template.json"
TEMPLATE_FILE_PATH = MOD_SOURCE_PATH + SEP + TEMPLATE_FILE_SUBPATH
assert os.path.exists(TEMPLATE_FILE_PATH), TEMPLATE_FILE_PATH


def GET_LANGUAGE_FILE_SUBPATH(language_code):
  if not LANGUAGE_CODE_LIBRETRANSLATE_SUBSTITUTIONS[language_code] in LIBRETRANSLATE_SUPPORTED_LANGUAGE_CODES:
    print(f"warning: {language_code} is not supported.")
  return SEP.join(["Server", "Languages", language_code, "items.lang"])

def GET_LANGUAGE_FILE_DESTINATION_PATH(language_code):
  return SEP.join([MOD_DESTINATION_PATH, GET_LANGUAGE_FILE_SUBPATH(language_code)])






  
  
def clear_folder(folder_path, expected_extension):
  for nameToDelete in os.listdir(folder_path):
    pathToDelete = folder_path + SEP + nameToDelete
    assert MOD_NAME in str(pathlib.Path(pathToDelete).resolve())
    assert os.path.exists(pathToDelete)
    assert pathToDelete.endswith(expected_extension)
    assert not os.path.isdir(pathToDelete)
    os.remove(pathToDelete)
  
  
  
async def optimize_png_in_place(path):
  command = f"optipng -o7 \"{path}\""  # don't use repr for path because windows does not treat backslash as an escape character in paths.
  print(f"running command {command}")
  try:
    subrocess = await asyncio.create_subprocess_shell(command, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await subprocess.communicate()
    print(f"{subprocess.returncode=}, {stdout=}, {stderr=}")
  except FileNotFoundError: # TODO test whether this is still effective after async change
    print("the PNG file could not be found OR the executable could not be found.")
    sys.exit(BAD_EXIT_CODE)
  except:
    print("something else went wrong.")
    sys.exit(BAD_EXIT_CODE)
  print(completedProcess.stdout)
  
  
  
  
  
  
  
# ---------- MAIN PROCEDURE ----------
  
  
# Load template file \/

templateFileLines = []
with open(TEMPLATE_FILE_PATH, "r") as templateFile:
  currentLine = templateFile.readline()
  while len(currentLine) > 0:
    templateFileLines.append(currentLine)
    currentLine = templateFile.readline()
if len(templateFileLines) == 0:
  raise ValueError("empty template file?? failed.")
  



# clear destination folders and prepare destination mod \/

clear_folder(ASSET_FOLDER_DESTINATION_PATH, ".json")
clear_folder(ICON_FOLDER_DESTINATION_PATH, ".png")
clear_folder(MODEL_FOLDER_DESTINATION_PATH, ".blockymodel")
shutil.copy(MOD_SOURCE_PATH+SEP+"manifest.json", MOD_DESTINATION_PATH+SEP+"manifest.json")
for langCode in BREEZE_BLOCKS_LANGUAGE_CODES:
  pathToRemove = GET_LANGUAGE_FILE_DESTINATION_PATH(langCode)
  if os.path.exists(pathToRemove):
    os.remove(pathToRemove)



# build mod \/
  
#async def generate_assets():
  
  # poolerWorkTask = asyncio.create_task(PNG_OPTIMIZATION_PROCESS_POOLER.work())
  # await asyncio.sleep(10)

codecStrings = {"en-US": "utf-8", "pt-BR": "utf-8-sig", "uk-UA": "utf-8", "ru-RU": "utf-8"}
languageFiles = {langCode: codecs.open(GET_LANGUAGE_FILE_DESTINATION_PATH(langCode), "w", codecStrings[langCode]) for langCode in BREEZE_BLOCKS_LANGUAGE_CODES}
colorsShelf = shelve.open("colors.shelf")

for modelFileName in (name for name in os.listdir(MODEL_FOLDER_SOURCE_PATH) if name.endswith(".blockymodel")):
  shutil.copy(MODEL_FOLDER_SOURCE_PATH+SEP+modelFileName, MODEL_FOLDER_DESTINATION_PATH+SEP+modelFileName)
  modelNameWithDepth = remove_suffix(modelFileName, ".blockymodel")
  modelNameWithoutDepth = remove_suffix(modelNameWithDepth, "_Db1000")
  iconMaskFileName = modelNameWithoutDepth + ".png"
  
  
  
  for dataPage in DATA_PAGES:
    for family in data_page_get_value(dataPage, "FAMILY_LIST"):
      for textureNameSuffix in data_page_get_value(dataPage, "TEXTURE_NAME_SUFFIX_LIST"):
        
        
        # asset info specific to this model and texture:
        assetInfo = dict()
        assetInfo["unpatched_texture_base_name"] = f"{data_page_get_value(dataPage, 'TEXTURE_NAME_PREFIX')}{family}{textureNameSuffix}" # this is also used as the block set later
        assetInfo["texture_file_name"] = select_best_texture_file_name(base_name=assetInfo["unpatched_texture_base_name"])
        assetInfo["full_name"] = data_page_get_value(dataPage, "PRIVATE_TYPE") + "_" + family + (textureNameSuffix if data_page_get_value(dataPage, "INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME") else "") + "_" + modelNameWithoutDepth
        assetInfo["output_file_path"] = ASSET_FOLDER_DESTINATION_PATH + SEP + assetInfo["full_name"] + ".json"
        assetInfo["icon_file_name"] = assetInfo["full_name"] + ".png"
        assetInfo["icon_file_path"] = ICON_FOLDER_DESTINATION_PATH + SEP + assetInfo["icon_file_name"]
        try:
          assetInfo["particle_color_as_tuple"] = colorsShelf[assetInfo["texture_file_name"]][PARTICLE_COLORATION]
        except KeyError:
          raise KeyError("Some textures in your hytale assets folder aren't registered by colors.py, or the shelf is malformed. Try running colors.py again.")          
        
        
        # asset info specific to this model and texture, for inclusion in asset file:
        assetContents = {
          "ICON_PATH_IN_MOD": "Icons/ItemsGenerated/" + assetInfo["icon_file_name"],
          "BLOCK_SET": assetInfo["unpatched_texture_base_name"],
          "TEXTURE_PATH_IN_MOD": f"BlockTextures/{assetInfo['texture_file_name']}",
          "PARTICLECOLOR_STR": color_tuple_to_hytale_string(assetInfo["particle_color_as_tuple"]),
        }
        
        
        # icon generation:
        with Image.open(MODEL_FOLDER_SOURCE_PATH + SEP + iconMaskFileName) as thumbnailMaskImage:
          with Image.open(HYTALE_BLOCKTEXTURES_PATH + SEP + assetInfo["texture_file_name"]) as thumbnailTextureImage:
            assert thumbnailMaskImage.size == thumbnailTextureImage.size
            thumbnailResultImageNoBG = ImageChops.multiply(thumbnailMaskImage.convert("RGB"), thumbnailTextureImage.convert("RGB"))
            if sum(assetInfo["particle_color_as_tuple"]) <= ICON_BACKGROUND_INVERSION_THRESHOLD:
              thumbnailResultImage = ImageChops.add(thumbnailResultImageNoBG, ImageChops.invert(thumbnailMaskImage).convert("RGB"))
            else:
              thumbnailResultImage = thumbnailResultImageNoBG
            thumbnailResultImage.save(assetInfo["icon_file_path"])
            # PNG_OPTIMIZATION_PROCESS_POOLER.put(ProcessPooling.WorkOrder(optimize_png_in_place, [assetInfo["icon_file_path"]], dict()))
        
        
        # language file stuff:
        modelNameForDecomposition = remove_prefix(modelNameWithoutDepth, 'Breeze_')
        decomposedModelName = parse_string_as_structure(modelNameForDecomposition, [GRID_PATTERN,CREATE_SIZE_DESCRIPTION_PATTERN(MAX_UNIVERSAL_NUMBER_COMPONENT_DIGITS), MULTI_SHAPE_NAME_PATTERN]).assert_complete_and_get_matched_data()
        modelNameLayoutStr, modelNameSizeDescriptionStr, modelNameShapeNicknameStr = tuple(flatten_string_structure_and_join(item) for item in decomposedModelName)
        modelNameShapeNameStr = dictionary_translate_if_able(SHAPE_NICKNAMES_TO_NAMES, modelNameShapeNicknameStr)
        displayNameNative = f"{dictionary_translate_if_able(UNIFIED_DISPLAY_NAME_TRANSLATIONS, family)} Breeze Block (shape: {modelNameShapeNameStr}, layout: {modelNameLayoutStr}, thickness: {modelNameSizeDescriptionStr})"
        
        for langCode, langFile in languageFiles.items():
          displayNameTranslated = translate_string_piecewise(displayNameNative, source=BREEZE_BLOCKS_NATIVE_LANGUAGE_CODE, target=langCode, delimeters=("(", ")", ":", ","))
          langFile.write(f"{assetInfo['full_name']}.name = {displayNameTranslated}\n")
        
        
        # main procedure:
        if os.path.exists(assetInfo["output_file_path"]):
          os.remove(assetInfo["output_file_path"])
        with open(assetInfo["output_file_path"], "w") as outputFile:
          for currentLine in templateFileLines:
            outputLine = currentLine.replace("${FULL_NAME}", assetInfo["full_name"]
              ).replace("${MODEL_BASE_NAME}", modelNameWithDepth
              ).replace("${ICON_PATH_IN_MOD}", assetContents["ICON_PATH_IN_MOD"]
              ).replace("${SET}", assetContents["BLOCK_SET"]
              ).replace("${TEXTURE_PATH_IN_MOD}", assetContents["TEXTURE_PATH_IN_MOD"]
              ).replace("${PARTICLECOLOR_STR}", assetContents["PARTICLECOLOR_STR"]
              )
            
            for jsonOld, jsonNew in data_page_get_value(dataPage, "AUTOMATIC_JSON_ITEMS"):
              outputLine = outputLine.replace("${" + jsonOld + "}", jsonNew)
              
            # the following must happen after automatic json items because they are used inside those items:
            outputLine = outputLine.replace("${FAMILY}", family)
            outputLine = outputLine.replace("${TEXTURE_NAME_SUFFIX}", textureNameSuffix)
            
            assert "${" not in outputLine, f"a marker for data insertion into the JSON file was not used. The line is {outputLine!r}"
            assert "__" not in outputLine, f"the output line {outputLine!r} contains \"__\". this usually indicates a mistake in the template or data page."
            outputFile.write(outputLine)

for languageFile in languageFiles.values():
  languageFile.close()
colorsShelf.close()

#asyncio.run(generate_assets())

print(f"execution took {time.monotonic()-START_TIME:.3f} seconds")