# builtin
import os
import shutil
import itertools
import pathlib
import codecs # for portuguese

# project
from HYTALE import HYTALE_ASSETS_PATH, SEP, HYTALE_BLOCKTEXTURES_PATH, HYTALE_BLOCKTEXTURE_FILE_NAMES

# pip
from PIL import Image, ImageChops
from tibs import Tibs
import shelve
from libretranslatepy import LibreTranslateAPI
libreTranslateAPI = LibreTranslateAPI("http://127.0.0.1:5000")
# print(libreTranslateAPI.translate("LibreTranslate is awesome!", "en", "pt-BR"))
# import dotted_dict

"""
todo:
replace scandir with listdir
replace readlines with read
rename thumbnails to icons
"""

PARTICLE_COLORATION = "channelwise_median_snapped_to_input_color" # a key provided by colors.py in colors.shelf
ICON_BACKGROUND_INVERSION_THRESHOLD = 0 # brightness at or below which the background will be inverted from black to white.


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
  assert a == b, (a, b)
  
def assert_isinstance(a, b):
  assert isinstance(a, b), (a, b)
  
# def assert_is_empty(a):
  # assert len(a) == 0, a
  
  

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
DIGIT_PATTERN = ("0","1","2","3","4","5","6","7","8","9")
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

# _a = CREATE_SIZE_DESCRIPTION_PATTERN(MAX_UNIVERSAL_NUMBER_COMPONENT_DIGITS)
# print(_a)
# print(parse_string_as_structure("T2p", _a))
# _a = CREATE_UNIVERSAL_NUMBER_PATTERN(1)
# print(_a)
# print(parse_string_as_structure("2p", _a))
# exit()
# del _a








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
  # assert ideal_name.endswith(".png")
  if base_name.startswith("Wood_"):
    return patch_wood_texture_name(base_name + ".png")
  elif base_name.startswith("Rock_"):
    assert base_name.endswith("_Brick") or base_name.endswith("_Brick_Smooth"), base_name
    # print(base_name)
    for oldSubstr, newSubstr in ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS.items():
      # this must happen first because "peachstone" (And maybe similar things) are detected for the the Rock_ prefix removal logic
      base_name = base_name.replace(f"_{oldSubstr}_", f"_{newSubstr}_")
    for rockType in ROCK_BRICK_TEXTURE_NAME_NO_ROCK_PREFIX_REQUIRED:
      if base_name.startswith(f"Rock_{rockType}_"):
        base_name = rockType + "_" + remove_prefix(base_name, f"Rock_{rockType}_")
    # print(base_name)
    # print()
    return select_best_texture_name_by_cost(base_name, BRICK_TEXTURE_NAME_SUBSTRING_COSTS)
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
ROCK_BRICK = "Aqua Basalt Calcite Chalk Gold Ledge Lime Marble Peach Quartzite Sandstone Sandstone_Red Sandstone_White Shale Stone Volcanic".split(" ")
# in-game ID = Rock_(value)_Brick
# in-game name = ROCK_BRICK_NAME_UPGRADES[value] + " Brick"
ROCK_RUNIC_BRICK = "Runic_Blue Runic Runic_Teal Runic_Dark".split(" ") # the texture names on these are so bad that I am boycotting them.

ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS = {"Ledge": "Ledgestone", "Lime":"Limestone", "Peach":"Peachstone"}
ROCK_BRICK_TEXTURE_NAME_NO_ROCK_PREFIX_REQUIRED = ["Peachstone", "Calcite", "Runic_Brick_Dark", "Runic_Brick_Dark_Blue"]
_ROCK_BRICK_DISPLAY_NAME_TRANSLATIONS = {"Runic_Blue": "Blue Runic", "Runic_Teal": "Dark Blue Runic", "Runic_Dark": "Dark Runic", "Sandstone_Red":"Red Sandstone", "Sandstone_White": "White Sandstone"}

# gold brick only has a side texture

PROTOTYPE_ROCK_BRICKS = "Concrete".split(" ")
SOIL_BRICK = "Hive Hive_Corrupted Clay Clay_Ocean Snow"
_SOIL_BRICK_DISPLAY_NAME_TRANSLATIONS = {"Hive_Corrupted": "Corrupted Hive", "Clay_Ocean": "Ocean Clay"}
#  Aqua Calcite Gold Ledge Lime Marble # these are available as smooth bricks in-game but their textures have irregular names.
# "Rock": {"LIST": ["Runic_Blue", "Runic_Dark", "Runic_Teal"], "SUFFIX": ""}, # irregular texture names

UNIFIED_DISPLAY_NAME_TRANSLATIONS = dict(list(_ROCK_BRICK_DISPLAY_NAME_TRANSLATIONS.items()) + list(_SOIL_BRICK_DISPLAY_NAME_TRANSLATIONS.items()) + list(ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS.items()))






# ----- structured data about how to generate assets -----

DATA_PAGES = [
  [
    ("TEXTURE_NAME_PREFIX", "Wood_"),
    ("FAMILY_LIST", list("Blackwood Darkwood Deadwood Drywood Goldenwood Greenwood Hardwood Lightwood Redwood Softwood Tropicalwood".split(" "))),
    ("TEXTURE_NAME_SUFFIX_LIST", ["_Planks"]),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", False),
    ("AUTOMATIC_JSON_ITEMS", [
      ("JSON_RECIPE_INPUT_RESOURCETYPEID_STR", "Wood_${FAMILY}"),
      ("JSON_TAGS_TYPE_STR", "Wood"),
      ("JSON_TAGS_SUBTYPE", ",\n    \"SubType\": [\n      \"Planks\"\n    ]"),
      ("JSON_TAGS_FAMILY", ",\n    \"Family\": [\n      \"${FAMILY}\"\n    ]"),
      ("JSON_BLOCKTYPE_GATHERING_BREAKING_GATHERTYPE_STR", "Woods"),
      ("JSON_BLOCKTYPE_BLOCKPARTICLESETID_STR", "Wood"),
      ("JSON_FUEL_QUALITY_LINE", "\"FuelQuality\": 0.75,"),
      ("JSON_BLOCKTYPE_BLOCKSOUNDSETID_STR", "Wood"),
      ("JSON_ITEMSOUNDSETID_STR", "ISS_Blocks_Wood"),
    ]),
    
  ],
  [
    ("TEXTURE_NAME_PREFIX", "Rock_"),
    ("FAMILY_LIST", ROCK_BRICK),
    ("TEXTURE_NAME_SUFFIX_LIST", ["_Brick"]),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", False),
    ("AUTOMATIC_JSON_ITEMS", [
      ("JSON_RECIPE_INPUT_RESOURCETYPEID_STR", "Rock_${FAMILY}_Brick"),
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
PROTOTYPE_DATA_PAGES = [
  [
    ("TEXTURE_NAME_PREFIX", ""),
    ("FAMILY_LIST", ["Clay"]),
    ("TEXTURE_NAME_SUFFIX_LIST", list("_"+item for item in CLAY_COLORS)),
    ("INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME", True), # this flag exists because of clay.
    ("AUTOMATIC_JSON_ITEMS", [
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

LANGUAGE_EN_US_FILE_SUBPATH = SEP.join(["Server", "Languages", "en-US", "items.lang"])
LANGUAGE_EN_US_FILE_DESTINATION_PATH = SEP.join([MOD_DESTINATION_PATH, LANGUAGE_EN_US_FILE_SUBPATH])
assert os.path.exists(LANGUAGE_EN_US_FILE_DESTINATION_PATH), " could not find: " + LANGUAGE_EN_US_FILE_DESTINATION_PATH


LANGUAGE_PT_BR_FILE_SUBPATH = SEP.join(["Server", "Languages", "pt-BR", "items.lang"])
LANGUAGE_PT_BR_FILE_DESTINATION_PATH = SEP.join([MOD_DESTINATION_PATH, LANGUAGE_PT_BR_FILE_SUBPATH])
assert os.path.exists(LANGUAGE_PT_BR_FILE_DESTINATION_PATH), " could not find: " + LANGUAGE_PT_BR_FILE_DESTINATION_PATH






  
  
def clear_folder(folder_path, expected_extension):
  for nameToDelete in os.listdir(folder_path):
    pathToDelete = folder_path + SEP + nameToDelete
    assert MOD_NAME in str(pathlib.Path(pathToDelete).resolve())
    assert os.path.exists(pathToDelete)
    assert pathToDelete.endswith(expected_extension)
    assert not os.path.isdir(pathToDelete)
    os.remove(pathToDelete)
  
  
  
  
  
  
  
  
  
  
  
# ---------- MAIN PROCEDURE ----------
  
# Load template file \/

templateFileLines = []
with open(TEMPLATE_FILE_PATH, "r") as templateFile:
  # print("opened template file.")
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
os.remove(LANGUAGE_EN_US_FILE_DESTINATION_PATH)


# generate assets \/  

languageFileEnUS = open(LANGUAGE_EN_US_FILE_DESTINATION_PATH, "w")
languageFilePtBR = codecs.open(LANGUAGE_PT_BR_FILE_DESTINATION_PATH, "w", "utf-8-sig")
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
        assetInfo["full_name"] = data_page_get_value(dataPage, ("AUTOMATIC_JSON_ITEMS", "JSON_TAGS_TYPE_STR")) + "_" + family + (textureNameSuffix if data_page_get_value(dataPage, "INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME") else "") + "_" + modelNameWithoutDepth
        assetInfo["output_file_path"] = ASSET_FOLDER_DESTINATION_PATH + SEP + assetInfo["full_name"] + ".json"
        assetInfo["icon_file_name"] = assetInfo["full_name"] + ".png"
        assetInfo["icon_file_path"] = ICON_FOLDER_DESTINATION_PATH + SEP + assetInfo["icon_file_name"]
        assetInfo["particle_color_as_tuple"] = colorsShelf[assetInfo["texture_file_name"]][PARTICLE_COLORATION]
        
        
        # asset info specific to this model and texture, for inclusion in asset file:
        assetContents = {
          "ICON_PATH_IN_MOD": "Icons/ItemsGenerated/" + assetInfo["icon_file_name"],
          "BLOCK_SET": assetInfo["unpatched_texture_base_name"],
          "TEXTURE_PATH_IN_MOD": f"BlockTextures/{assetInfo['texture_file_name']}",
          # "RESOURCE_TYPE_ID_TO_CRAFT": f"{data_page_get_value(dataPage, ('AUTOMATIC_JSON_ITEMS', 'JSON_TAGS_TYPE_STR'))}_{family}",
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
        
        
        # language file stuff:
        modelNameForDecomposition = remove_prefix(modelNameWithoutDepth, 'Breeze_')
        decomposedModelName = parse_string_as_structure(modelNameForDecomposition, [GRID_PATTERN,CREATE_SIZE_DESCRIPTION_PATTERN(MAX_UNIVERSAL_NUMBER_COMPONENT_DIGITS), MULTI_SHAPE_NAME_PATTERN]).assert_complete_and_get_matched_data()
        #print(f"{modelNameForDecomposition} becomes {decomposedModelName}")
        # if isinstance(decomposedModelName, ParseFailure):
        # else:
          # assert isinstance(decomposedModelName, ParseSuccess)
        modelNameLayoutStr, modelNameSizeDescriptionStr, modelNameShapeStr = tuple(flatten_string_structure_and_join(item) for item in decomposedModelName)
        displayNameEnUS = f"{UNIFIED_DISPLAY_NAME_TRANSLATIONS.get(family, family)} Breeze Block (shape: {modelNameShapeStr}, layout: {modelNameLayoutStr}, thickness: {modelNameSizeDescriptionStr})"
        displayNamePtBR = libreTranslateAPI.translate(displayNameEnUS, "en", "pt-BR")
        languageFileEnUS.write(f"{assetInfo['full_name']}.name = {displayNameEnUS}\n")
        languageFilePtBR.write(f"{assetInfo['full_name']}.name = {displayNamePtBR}\n")
        
        
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
            
            assert "${" not in outputLine, outputLine
            assert "__" not in outputLine, outputLine # because this should never happen and usually indicates a mistake in the template or data page.
            outputFile.write(outputLine)

languageFileEnUS.close() # probably not necessary in cpython, 
# and outside of cpython, the lack of a context manager here might result in the file being left open after a crash https://stackoverflow.com/questions/17577137/do-files-get-closed-during-an-exception-exit
# TODO combine multiple language files into one context manager?
languageFilePtBR.close()
colorsShelf.close()