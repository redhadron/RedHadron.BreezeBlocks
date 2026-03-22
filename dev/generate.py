import os
# import shutil
import itertools
import pathlib
from PIL import Image, ImageChops

"""
todo:
replace scandir with listdir
replace readlines with read
"""




  
def remove_suffix(string, suffix):
  assert len(suffix) <= len(string)
  assert len(suffix) > 0
  assert string.endswith(suffix)
  return string[:-len(suffix)]
  
def remove_prefix(string, prefix):
  assert len(prefix) <= len(string)
  assert len(prefix) > 0
  assert string.startswith(prefix)
  return string[len(prefix):]





# ----- helper functions for working with data pages -----
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






# ----- Hytale path constants -----

HYTALE_ASSETS_PATH = "E:\Hytale Assets 20260221" # path to a folder in which you have put the contents of Assets.zip after decompressing.
assert os.path.isdir(HYTALE_ASSETS_PATH)

SEP = os.sep

HYTALE_BLOCKTEXTURES_PATH = HYTALE_ASSETS_PATH + SEP + "Common" + SEP + "BlockTextures"
assert os.path.isdir(HYTALE_BLOCKTEXTURES_PATH)

HYTALE_BLOCKTEXTURE_FILE_NAMES = [item for item in os.listdir(HYTALE_BLOCKTEXTURES_PATH) if item.endswith(".png")]
assert len(HYTALE_BLOCKTEXTURE_FILE_NAMES) > 600
assert "Bone_Side.png" in HYTALE_BLOCKTEXTURE_FILE_NAMES






# ----- texture file selection tools -----

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



# ----- Hytale game data constants -----

CLAY_COLORS = "Black Blue Cyan Green Grey Lime Orange Pink Purple Red White Yellow".split()

# ROCK_BRICK_NO_TEXTURE_NAME_PROCESSING_REQUIRED = list("Basalt Quartzite Shale Stone Volcanic".split(" ")) # non-exhaustive # maybe add chalk
ROCK_BRICK = "Aqua Basalt Calcite Chalk Gold Ledge Lime Marble Peach Quartzite Sandstone Sandstone_Red Sandstone_White Shale Stone Volcanic".split(" ")
# in-game ID = Rock_(value)_Brick
# in-game name = ROCK_BRICK_NAME_UPGRADES[value] + " Brick"
ROCK_RUNIC_BRICK = "Runic_Blue Runic Runic_Teal Runic_Dark".split(" ") # the texture names on these are so bad that I am boycotting them.

ROCK_BRICK_TEXTURE_NAME_SUBSTRING_REPLACEMENTS = {"Ledge": "Ledgestone", "Lime":"Limestone", "Peach":"Peachstone"}
ROCK_BRICK_TEXTURE_NAME_NO_ROCK_PREFIX_REQUIRED = ["Peachstone", "Calcite", "Runic_Brick_Dark", "Runic_Brick_Dark_Blue"]
ROCK_BRICK_PURE_NAME_UPGRADES = {"Runic_Blue": "Blue Runic", "Runic_Teal": "Dark Blue Runic", "Runic_Dark": "Dark Runic", "Sandstone_Red":"Red Sandstone", "Sandstone_White": "White Sandstone"}

# gold brick only has a side texture

PROTOTYPE_ROCK_BRICKS = "Concrete".split(" ")
SOIL_BRICK = "Hive Hive_Corrupted Clay Clay_Ocean Snow"
SOIL_BRICK_NAME_UPGRADES = {"Hive_Corrupted": "Corrupted Hive", "Clay_Ocean": "Ocean Clay"}
#  Aqua Calcite Gold Ledge Lime Marble # these are available as smooth bricks in-game but their textures have irregular names.
# "Rock": {"LIST": ["Runic_Blue", "Runic_Dark", "Runic_Teal"], "SUFFIX": ""}, # irregular texture names









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

MOD_PATH = SEP.join([os.getcwd(), ".."]) if "dev" in os.getcwd() else os.getcwd()
assert "dev" in os.listdir(MOD_PATH), "mod path may be invalid"

MODEL_FOLDER_PATH = SEP.join([MOD_PATH, "Common", "Blocks", "Breeze"])
assert os.path.exists(MODEL_FOLDER_PATH), MODEL_FOLDER_PATH

OUTPUT_FOLDER_PATH = SEP.join([MOD_PATH, "Server", "Item", "Items"])
assert os.path.exists(OUTPUT_FOLDER_PATH), OUTPUT_FOLDER_PATH

ICON_FOLDER_PATH = SEP.join([MOD_PATH, "Common", "Icons", "ItemsGenerated"])
assert os.path.exists(ICON_FOLDER_PATH), ICON_FOLDER_PATH

TEMPLATE_FILE_PATH = MOD_PATH + SEP + "dev" + SEP + "Breeze_Template.json"
assert os.path.exists(TEMPLATE_FILE_PATH), TEMPLATE_FILE_PATH







  
  
def clear_folder(folder_path, expected_extension):
  for nameToDelete in os.listdir(folder_path):
    pathToDelete = folder_path + SEP + nameToDelete
    assert "RedHadron.BreezeBlocks" in str(pathlib.Path(pathToDelete).resolve())
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
  


# clear assets folder \/

clear_folder(OUTPUT_FOLDER_PATH, ".json")
clear_folder(ICON_FOLDER_PATH, ".png")




# generate assets \/  
  
for modelFileName in (name for name in os.listdir(MODEL_FOLDER_PATH) if name.endswith(".blockymodel")):
  shapeNameWithDepth = remove_suffix(modelFileName, ".blockymodel")
  shapeNameWithoutDepth = remove_suffix(shapeNameWithDepth, "_Db1000")
  iconMaskFileName = shapeNameWithoutDepth + ".png"
  
  for dataPage in DATA_PAGES:
    for family in data_page_get_value(dataPage, "FAMILY_LIST"):
      for textureNameSuffix in data_page_get_value(dataPage, "TEXTURE_NAME_SUFFIX_LIST"):
        unpatchedTextureBaseName = f"{data_page_get_value(dataPage, 'TEXTURE_NAME_PREFIX')}{family}{textureNameSuffix}"
        textureFileName = select_best_texture_file_name(base_name=unpatchedTextureBaseName)
        
        assetInfo = {"full_name": data_page_get_value(dataPage, ("AUTOMATIC_JSON_ITEMS", "JSON_TAGS_TYPE_STR")) + "_" + family + (textureNameSuffix if data_page_get_value(dataPage, "INCLUDE_TEXTURE_NAME_SUFFIX_IN_ASSET_NAME") else "") + "_" + shapeNameWithoutDepth}
        assetInfo["output_file_path"] = OUTPUT_FOLDER_PATH + SEP + assetInfo["full_name"] + ".json"
        assetInfo["icon_file_name"] = assetInfo["full_name"] + ".png"
        assetInfo["icon_file_path"] = ICON_FOLDER_PATH + SEP + assetInfo["icon_file_name"]
        
        assetContents = {
          "ICON_PATH_IN_MOD": "Icons/ItemsGenerated/" + assetInfo["icon_file_name"],
          "BLOCK_SET": unpatchedTextureBaseName,
          "TEXTURE_PATH_IN_MOD": f"BlockTextures/{textureFileName}",
          # "RESOURCE_TYPE_ID_TO_CRAFT": f"{data_page_get_value(dataPage, ('AUTOMATIC_JSON_ITEMS', 'JSON_TAGS_TYPE_STR'))}_{family}",
        }
        
        with Image.open(MODEL_FOLDER_PATH + SEP + iconMaskFileName) as thumbnailMaskImage:
          with Image.open(HYTALE_BLOCKTEXTURES_PATH + SEP + textureFileName) as thumbnailTextureImage:
            assert thumbnailMaskImage.size == thumbnailTextureImage.size
            thumbnailResultImage = ImageChops.multiply(thumbnailMaskImage.convert("RGB"), thumbnailTextureImage.convert("RGB"))
            thumbnailResultImage.save(assetInfo["icon_file_path"])
            
            
        outputFilePath = assetInfo["output_file_path"]
        if os.path.exists(outputFilePath):
          # print(f"replacing {outputFilePath}")
          os.remove(outputFilePath)
        else:
          # print(f"creating {outputFilePath}")
          pass
          
        with open(outputFilePath, "w") as outputFile:
          for currentLine in templateFileLines:
            outputLine = currentLine.replace("${FULL_NAME}", assetInfo["full_name"]
              ).replace("${MODEL_BASE_NAME}", shapeNameWithDepth
              ).replace("${ICON_PATH_IN_MOD}", assetContents["ICON_PATH_IN_MOD"]
              ).replace("${SET}", assetContents["BLOCK_SET"]
              ).replace("${TEXTURE_PATH_IN_MOD}", assetContents["TEXTURE_PATH_IN_MOD"]
              )
            for jsonOld, jsonNew in data_page_get_value(dataPage, "AUTOMATIC_JSON_ITEMS"):
              outputLine = outputLine.replace("${" + jsonOld + "}", jsonNew)
              
            # the following must happen after automatic json items because they are used inside those items:
            outputLine = outputLine.replace("${FAMILY}", family)
            outputLine = outputLine.replace("${TEXTURE_NAME_SUFFIX}", textureNameSuffix)
            
            assert "${" not in outputLine, outputLine
            assert "__" not in outputLine, outputLine # because this probably should never happen.
            outputFile.write(outputLine)
      