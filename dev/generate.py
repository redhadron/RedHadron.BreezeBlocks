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
import asyncio # for using multiple processes for png crushing
import sys # to use sys.exit inside async, although this does not work.
import json

# project
from Hytale import HYTALE_ASSETS_PATH, SEP, HYTALE_BLOCKTEXTURES_PATH, HYTALE_BLOCKTEXTURE_FILE_NAMES
import ProcessPooling
from Affixes import remove_suffix, remove_prefix, shorten_suffix, lstrip_and_count, rstrip_and_count
from Utilities import assert_equals, int_divide_exact
import Parsing
from colors import COLORS_SHELF_PATH

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
  print("failed to communicate with libretranslate. Are you running a libretranslate server on the default port? https://docs.libretranslate.com/ recommended command \"libretranslate --translation-cache all --disable-web-ui\"")
  exit(BAD_EXIT_CODE)
import psutil
# import numpy
# from stablerandom import stablerandom




USE_HYPERTHREADING = False # if true, use one subprocess per logical core. if false, use one per physical core.
PNG_OPTIMIZATION_SIMULTANEOUS_PROCESSES = psutil.cpu_count(logical=USE_HYPERTHREADING)
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



# ----- helpers for working with data pages -----
""" data pages are lists of tuples. They are used instead of dictionaries to preserve order and to allow duplicate entries. """

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





# ----- mod-specific parsing patterns for use with Parsing.py -----

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

BRICK_TEXTURE_NAME_SUBSTRING_COSTS = {"Cobble": 100, "Corner": 1000, "Ornate": 150, "Decorative": 175, "Top":20, "Side":21, "Smooth":-50, "0":1, "1":2, "2":3, "3":4, "4":5, "5":6, "6":7, "7":8, "8":9, "9":10} # the texture with the lowest score will be chosen when an exact match to the predicted texture name is not found.

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












# ----- display name translation -----

SHAPE_NICKNAMES_TO_NAMES = {"Hair": "Crosshair", "Head": "Empty Crosshair", "SlowNeckNeckSlow": "Bottleneck Basketweave"}

SHAPE_NAME_TRANSLATION_CORRECTIONS = {
  "uk":{"Empty Crosshair":"порожнє перехрестя", "Crosshair":"перехрестя", "Dice":"грати в кості", "Nope":"Ні", "Bottleneck Basketweave":"схема плетіння Вузьке місце", "Void":"порожній"},
  "ru":{"Dice":"Игральные кости", "Nope":"Вычеркнуто", "Bottleneck Basketweave":"Переплетение узких мест"},
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
  return all(item in os.listdir(modPath) for item in ["Common"])
  
# TODO Manifest.json copying

if os.getcwd().count("dev") > 1:
  raise NotImplementedError()
assert not os.getcwd().endswith(SEP)

def assert_path_exists(input_path: str) -> None:
  assert isinstance(input_path, str)
  assert os.path.exists(input_path), input_path
def assert_directory_exists(input_path: str) -> None:
  assert isinstance(input_path, str)
  assert_path_exists(input_path)
  assert os.path.isdir(input_path), input_path
def assert_file_exists(input_path: str) -> None:
  assert isinstance(input_path, str)
  assert_path_exists(input_path)
  assert not os.path.isdir(input_path), input_path

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
assert_directory_exists(MODEL_FOLDER_SOURCE_PATH)
assert_directory_exists(MODEL_FOLDER_DESTINATION_PATH)

ASSET_FOLDER_SUBPATH = SEP.join(["Server", "Item", "Items"])
ASSET_FOLDER_DESTINATION_PATH = MOD_DESTINATION_PATH + SEP + ASSET_FOLDER_SUBPATH
assert_directory_exists(ASSET_FOLDER_DESTINATION_PATH)

ICON_FOLDER_SUBPATH = SEP.join(["Common", "Icons", "ItemsGenerated"])
ICON_FOLDER_DESTINATION_PATH = MOD_DESTINATION_PATH + SEP + ICON_FOLDER_SUBPATH
assert_directory_exists(ICON_FOLDER_DESTINATION_PATH)

BLOCKTEXTURE_FOLDER_SUBPATH = SEP.join(["Common", "BlockTextures"])
BLOCKTEXTURE_FOLDER_DESTINATION_PATH = MOD_DESTINATION_PATH + SEP + BLOCKTEXTURE_FOLDER_SUBPATH
assert_directory_exists(BLOCKTEXTURE_FOLDER_DESTINATION_PATH)

TEMPLATE_FILE_SUBPATH = "dev" + SEP + "Breeze_Template.json"
TEMPLATE_FILE_PATH = MOD_SOURCE_PATH + SEP + TEMPLATE_FILE_SUBPATH
assert_file_exists(TEMPLATE_FILE_PATH)

MANIFEST_FILE_SOURCE_PATH = MOD_SOURCE_PATH + SEP + "manifest.json"
MANIFEST_FILE_DESTINATION_PATH = MOD_DESTINATION_PATH + SEP + "manifest.json"
assert_file_exists(MANIFEST_FILE_SOURCE_PATH)


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
    assert pathToDelete.endswith(expected_extension)
    assert_file_exists(pathToDelete) # and is not dir
    os.remove(pathToDelete)
  
  
  
async def optimize_png_in_place(path):
  command = f"optipng -o9 \"{path}\""  # don't use repr for path because windows does not treat backslash as an escape character in paths.
  # print(f"running command {command}")
  try:
    proc = await asyncio.create_subprocess_shell(command, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
      print(f"{proc.returncode=}") # , {stdout=}, {stderr=}")
  except FileNotFoundError: # TODO test whether this is still effective after async change
    print("the PNG file could not be found OR the executable could not be found.")
    sys.exit(BAD_EXIT_CODE)
  except Exception as e:
    print(f"something else went wrong: {e}")
    sys.exit(BAD_EXIT_CODE)
  
  








# ----- Hytale game data constants -----

CLAY_COLORS = "Black Blue Cyan Green Grey Lime Orange Pink Purple Red White Yellow".split()

# ROCK_BRICK_NO_TEXTURE_NAME_PROCESSING_REQUIRED = list("Basalt Quartzite Shale Stone Volcanic".split(" ")) # non-exhaustive # maybe add chalk
ROCK_BRICK = "Aqua Basalt Calcite Chalk Ledge Lime Marble Peach Quartzite Sandstone Sandstone_Red Sandstone_White Shale Stone Volcanic".split(" ")
# in-game ID = Rock_(value)_Brick
# in-game name = ROCK_BRICK_NAME_UPGRADES[value] + " Brick"
ROCK_RUNIC_BRICK = "Runic_Blue Runic Runic_Teal Runic_Dark".split(" ") # the texture names on these are so bad that I am boycotting them.
ROCK_BRICK_BUT_ACTUALLY_METAL = ["Gold"]
METAL = ["Iron", "Bronze", "Copper", "Zinc"]

ROCK_BRICK_FAMILY_DO_NOT_GENERATE_TEXTURE = ["Aqua", "Marble", "Peach"]
ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS = {"Ledge": "Ledgestone", "Lime":"Limestone", "Peach":"Peachstone"}
ROCK_BRICK_TEXTURE_NAME_NO_ROCK_PREFIX_REQUIRED = ["Peachstone", "Calcite", "Runic_Brick_Dark", "Runic_Brick_Dark_Blue"]
_ROCK_BRICK_DISPLAY_NAME_TRANSLATIONS = {"Runic_Blue": "Blue Runic", "Runic_Teal": "Dark Blue Runic", "Runic_Dark": "Dark Runic", "Sandstone_Red":"Red Sandstone", "Sandstone_White": "White Sandstone"}

PROTOTYPE_ROCK_BRICKS = "Concrete".split(" ")
SOIL_BRICK = "Hive Hive_Corrupted Clay Clay_Ocean Snow"
_SOIL_BRICK_DISPLAY_NAME_TRANSLATIONS = {"Hive_Corrupted": "Corrupted Hive", "Clay_Ocean": "Ocean Clay"}
#  Aqua Calcite Gold Ledge Lime Marble # these are available as smooth bricks in-game but their textures have irregular names.


UNIFIED_DISPLAY_NAME_TRANSLATIONS = dict(list(_ROCK_BRICK_DISPLAY_NAME_TRANSLATIONS.items()) + list(_SOIL_BRICK_DISPLAY_NAME_TRANSLATIONS.items()) + list(ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS.items()))







# ----- structured data about how to generate assets -----

_PROTOTYPE_DATA_PAGES = [
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
      ("JSON_BLOCKTYPE_GROUP_LINE", "\n"), # there's no group for this???
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
      ("JSON_TAGS_SUBTYPE", ""), # ao 20260326, there is no subtype for brick.
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




  
  
  
  
# ---------- MAIN PROCEDURE ----------
  
  
# Load template file \/

templateFileLines = []
with open(TEMPLATE_FILE_PATH, "r") as templateFile:
  currentLine = templateFile.readline()
  while len(currentLine) > 0: # TODO walrus
    templateFileLines.append(currentLine)
    currentLine = templateFile.readline()
if len(templateFileLines) == 0:
  raise ValueError("empty template file?? failed.")
  



# clear destination folders and prepare destination mod \/
def rjust_tuple(input_tuple, fill_value, length):
  assert isinstance(input_tuple, tuple)
  if len(input_tuple) >= length:
    return input_tuple
  else:
    return (fill_value,)*(length-len(input_tuple)) + input_tuple
assert rjust_tuple((3,4,5), 0, 5) == (0,0,3,4,5)
assert rjust_tuple((3,4,5), 0, 2) == (3,4,5)

clear_folder(ASSET_FOLDER_DESTINATION_PATH, ".json")
clear_folder(ICON_FOLDER_DESTINATION_PATH, ".png")
clear_folder(MODEL_FOLDER_DESTINATION_PATH, ".blockymodel")
clear_folder(BLOCKTEXTURE_FOLDER_DESTINATION_PATH, ".png")
if os.path.exists(MANIFEST_FILE_DESTINATION_PATH):
  # TODO make and use a json shelf-like CM
  with open(MANIFEST_FILE_SOURCE_PATH, "r") as srcManifestFile, open(MANIFEST_FILE_DESTINATION_PATH) as destManifestFile:
    srcText, destText = srcManifestFile.read(), destManifestFile.read()
  srcManifest, destManifest = json.loads(srcText), json.loads(destText)
  srcVer, destVer = (tuple(int(component) for component in manifest["Version"].split(".")) for manifest in (srcManifest, destManifest))
  maxComponentCount = max(len(srcVer), len(destVer))
  srcVer, destVer = (rjust_tuple(ver, 0, maxComponentCount) for ver in (srcVer, destVer))
  if srcVer < destVer:
    print("you are overwriting a newer version of the mod. if the newer version has files that are unused by the older version, you should delete them manually.")
shutil.copy(MANIFEST_FILE_SOURCE_PATH, MANIFEST_FILE_DESTINATION_PATH)
for langCode in BREEZE_BLOCKS_LANGUAGE_CODES:
  pathToRemove = GET_LANGUAGE_FILE_DESTINATION_PATH(langCode)
  if os.path.exists(pathToRemove):
    os.remove(pathToRemove)



# build mod \/
  
async def generate_assets():

  codecStrings = {"en-US": "utf-8", "pt-BR": "utf-8-sig", "uk-UA": "utf-8", "ru-RU": "utf-8"}
  languageFiles = {langCode: codecs.open(GET_LANGUAGE_FILE_DESTINATION_PATH(langCode), "w", codecStrings[langCode]) for langCode in BREEZE_BLOCKS_LANGUAGE_CODES}
  colorsShelf = shelve.open(COLORS_SHELF_PATH)


  # iterate through materials:
  for dataPage in DATA_PAGES:
    for family in data_page_get_value(dataPage, "FAMILY_LIST"):
      for textureNameSuffix in data_page_get_value(dataPage, "TEXTURE_NAME_SUFFIX_LIST"):
        
        # asset info specific to this material:
        materialInfo = dict()
        materialInfo["unpatched_texture_base_name"] = f"{data_page_get_value(dataPage, 'TEXTURE_NAME_PREFIX')}{family}{textureNameSuffix}" # this is also used as the block set later
        materialInfo["stock_texture_file_name"] = select_best_texture_file_name(base_name=materialInfo["unpatched_texture_base_name"])
        try:
          materialInfo["particle_color_as_tuple"] = colorsShelf[materialInfo["stock_texture_file_name"]][PARTICLE_COLORATION]
        except KeyError:
          raise KeyError("Some textures in your hytale assets folder aren't registered by colors.py, or the shelf is malformed. Try running colors.py again.")
                  
        
        # texture generation:
        stockTexName = materialInfo["stock_texture_file_name"]
        stockTexPath = HYTALE_BLOCKTEXTURES_PATH + SEP + stockTexName
        if "Brick" in stockTexName and family not in ROCK_BRICK_FAMILY_DO_NOT_GENERATE_TEXTURE:
          
          outputFileNameStr = remove_suffix(stockTexName, ".png") + "_Breeze_Cubes2x2.png"
          
          outputFilePathStr = BLOCKTEXTURE_FOLDER_DESTINATION_PATH + SEP + outputFileNameStr
          
          with Image.open(stockTexPath) as stockTexture:
            outputTexture = stockTexture.copy()
            assert stockTexture.size == (32, 32), "is this Hytale?"
            if "Smooth" in stockTexName:
              outputQuadrant = stockTexture.crop((0,0,16,16))
              assert outputQuadrant.size == (16, 16)
              outputQuadrant.paste(stockTexture.crop((24,0,32,8)), (8,0,16,8))
              outputQuadrant.paste(stockTexture.crop((24,24,32,32)), (8,8,16,16))
              outputQuadrant.paste(stockTexture.crop((0,24,8,32)), (0,8,8,16))
              for location in [(0,0,16,16),(16,0,32,16),(16,16,32,32),(0,16,16,32)]:
                outputTexture.paste(outputQuadrant, location)
            else:
              """
              print("not implemented: process regular bricks texture into breeze blocks texture.")
              materialInfo["final_texture_file_name"] = stockTexName
              materialInfo["generated_texture_exists"] = False
              """
              # use 7 pixel wide bands. I got this number by staring at the basalt brick texture.
              outputTexture.paste(stockTexture.crop((0,0,7,16)), (0,16,7,32)) # top left move down
              outputTexture.paste(stockTexture.crop((32-7,0,32,16)), (32-7,16,32,32)) # top right move down
              outputTexture.paste(stockTexture.crop((16-7,16,16+7,32)), (16-7,0,16+7,16)) # bottom center move up
          outputTexture.save(outputFilePathStr)
          materialInfo["final_texture_file_name"] = outputFileNameStr
          materialInfo["generated_texture_exists"] = True
        else:
          materialInfo["final_texture_file_name"] = stockTexName
          materialInfo["generated_texture_exists"] = False
        
        
        # iterate through models:
        for modelFileName in (name for name in os.listdir(MODEL_FOLDER_SOURCE_PATH) if name.endswith(".blockymodel")):
          shutil.copy(MODEL_FOLDER_SOURCE_PATH+SEP+modelFileName, MODEL_FOLDER_DESTINATION_PATH+SEP+modelFileName)
          modelNameWithDepth = remove_suffix(modelFileName, ".blockymodel")
          modelNameWithoutDepth = remove_suffix(modelNameWithDepth, "_Db1000")
          iconMaskFileName = modelNameWithoutDepth + ".png"
    
          
          
          # asset info specific to this model and material:
          assetInfo = dict()
          assetInfo["full_name"] = data_page_get_value(dataPage, "PRIVATE_TYPE") + "_" + family + (textureNameSuffix if data_page_get_value(dataPage, "INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME") else "") + "_" + modelNameWithoutDepth
          assetInfo["output_file_path"] = ASSET_FOLDER_DESTINATION_PATH + SEP + assetInfo["full_name"] + ".json"
          assetInfo["icon_file_name"] = assetInfo["full_name"] + ".png"
          assetInfo["icon_file_path"] = ICON_FOLDER_DESTINATION_PATH + SEP + assetInfo["icon_file_name"]
          
          
          # asset info specific to this model and texture, for inclusion in asset file:
          assetContents = {
            "ICON_PATH_IN_MOD": "Icons/ItemsGenerated/" + assetInfo["icon_file_name"],
            "TEXTURE_PATH_IN_MOD": f"BlockTextures/{materialInfo['final_texture_file_name']}", # TODO get rid of this here???
            "SET": materialInfo["unpatched_texture_base_name"],
            "PARTICLECOLOR_STR": color_tuple_to_hytale_string(materialInfo["particle_color_as_tuple"]),
          }
          
          
          # texture and icon work:
          with Image.open(MODEL_FOLDER_SOURCE_PATH + SEP + iconMaskFileName) as thumbnailMaskImage:
            with Image.open(BLOCKTEXTURE_FOLDER_DESTINATION_PATH + SEP + materialInfo["final_texture_file_name"] if materialInfo["generated_texture_exists"] else HYTALE_BLOCKTEXTURES_PATH + SEP + materialInfo["stock_texture_file_name"]) as thumbnailTextureImage:
              assert thumbnailMaskImage.size == thumbnailTextureImage.size
              
              # icon generation:
              thumbnailResultImageNoBG = ImageChops.multiply(thumbnailMaskImage.convert("RGB"), thumbnailTextureImage.convert("RGB"))
              if sum(materialInfo["particle_color_as_tuple"]) <= ICON_BACKGROUND_INVERSION_THRESHOLD:
                thumbnailResultImage = ImageChops.add(thumbnailResultImageNoBG, ImageChops.invert(thumbnailMaskImage).convert("RGB"))
              else:
                thumbnailResultImage = thumbnailResultImageNoBG
              thumbnailResultImage.save(assetInfo["icon_file_path"])
              
              
          PNG_OPTIMIZATION_PROCESS_POOLER.put(ProcessPooling.WorkOrder(optimize_png_in_place, [assetInfo["icon_file_path"]], dict()))
          
          
          # language file stuff:
          modelNameForDecomposition = remove_prefix(modelNameWithoutDepth, 'Breeze_')
          decomposedModelName = Parsing.parse_string_as_structure(modelNameForDecomposition, [GRID_PATTERN,CREATE_SIZE_DESCRIPTION_PATTERN(MAX_UNIVERSAL_NUMBER_COMPONENT_DIGITS), MULTI_SHAPE_NAME_PATTERN]).assert_complete_and_get_matched_data()
          modelNameLayoutStr, modelNameSizeDescriptionStr, modelNameShapeNicknameStr = tuple(Parsing.flatten_string_structure_and_join(item) for item in decomposedModelName)
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
                ).replace("${SET}", assetContents["SET"]
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
  
  while PNG_OPTIMIZATION_PROCESS_POOLER.has_work():
    await PNG_OPTIMIZATION_PROCESS_POOLER.do_some_work()

asyncio.run(generate_assets())

print(f"execution took {time.monotonic()-START_TIME:.3f} seconds")