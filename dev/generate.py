import os
# import shutil
import itertools
from PIL import Image, ImageChops

"""
todo:
replace scandir with listdir
replace readlines with read
"""



HYTALE_ASSETS_PATH = "E:\Hytale Assets 20260221" # path to a folder in which you have put the contents of Assets.zip after extracting them.


SEP = os.sep

HYTALE_BLOCKTEXTURES_PATH = HYTALE_ASSETS_PATH + SEP + "Common" + SEP + "BlockTextures"
DATA_PAGES = [
  [
    ("TEXTURE_NAME_PREFIX", "Wood_"),
    ("FAMILY_LIST", list("Blackwood Darkwood Deadwood Drywood Goldenwood Greenwood Hardwood Lightwood Redwood Softwood Tropicalwood".split(" "))),
    ("TEXTURE_NAME_SUFFIX", "_Planks"),
    ("JSON_TAGS_TYPE_STR", "Wood"),
    ("JSON_TAGS_SUBTYPE", ",\n    \"SubType\": [\n      \"Planks\"\n    ]"),
    ("JSON_TAGS_FAMILY", ",\n    \"Family\": [\n      \"${FAMILY}\"\n    ]"),
    ("JSON_GATHERING_BREAKING_GATHERTYPE_STR", "Woods"),
    ("JSON_FUEL_QUALITY_LINE", "\"FuelQuality\": 3.0,"),
  ],
  [
    ("TEXTURE_NAME_PREFIX", "Rock_"),
    ("FAMILY_LIST", list("Basalt Quartzite Shale Stone Volcanic".split(" "))),
    ("TEXTURE_NAME_SUFFIX", "_Brick_Smooth"),
    ("JSON_TAGS_TYPE_STR", "Rock"),
    ("JSON_TAGS_SUBTYPE", ""),
    ("JSON_TAGS_FAMILY", ",\n    \"Family\": [\n      \"${FAMILY}\"\n    ]"),
    ("JSON_GATHERING_BREAKING_GATHERTYPE_STR", "Rocks"),
    ("JSON_FUEL_QUALITY_LINE", ""),
  ],
]
#  Aqua Calcite Gold Ledge Lime Marble # these are available as smooth bricks in-game but their textures have irregular names.
# "Rock": {"LIST": ["Runic_Blue", "Runic_Dark", "Runic_Teal"], "SUFFIX": ""}, # irregular texture names
SOIL_CLAY_COLORS = "Black Blue Cyan Green Grey Lime Orange Pink Purple Red White Yellow"
# ocean is also like a color of soil clay (non-smooth naming), but I did not include it because it has no smooth counterpart.
# there is also a regular clay: Soil_Clay.
# there is also clay brick and ocean clay brick.
def data_page_get_value(data_page, key):
  assert isinstance(key, str) and isinstance(data_page, list)
  for item in data_page:
    assert len(item) == 2 and isinstance(item[0], str)
    if item[0] == key:
      return item[1]
  raise KeyError(key)
def data_page_has_key(data_page, key):
  assert isinstance(key, str) and isinstance(data_page, list)
  return any(item[0] == key for item in data_page)

MOD_PATH = SEP.join([os.getcwd(), ".."])
MODEL_FOLDER_PATH = SEP.join([MOD_PATH, "Common", "Blocks", "Breeze"])
assert os.path.exists(MODEL_FOLDER_PATH)
OUTPUT_FOLDER_PATH = SEP.join([MOD_PATH, "Server", "Item", "Items"])
assert os.path.exists(OUTPUT_FOLDER_PATH)
ICON_FOLDER_PATH = SEP.join([MOD_PATH, "Common", "Icons", "ItemsGenerated"])
assert os.path.exists(ICON_FOLDER_PATH)
TEMPLATE_FILE_PATH = os.getcwd() + SEP + "Breeze_Template.json"
assert os.path.exists(TEMPLATE_FILE_PATH)



def remove_suffix(a, b):
  assert a.endswith(b)
  return a[:-len(b)]
  
def patch_texture_name(input_string):
  return input_string.replace("Wood_Softwood_Planks.png", "Wood_Softwood_Planks_Top.png").replace("Wood_Greenwood_Planks.png", "Wood_Green.png") # .replace("Rock_Aqua_Brick_Smooth.png"
  
  

templateFileLines = []
with open(TEMPLATE_FILE_PATH, "r") as templateFile:
  print("opened template file.")
  currentLine = templateFile.readline()
  while len(currentLine) > 0:
    templateFileLines.append(currentLine)
    currentLine = templateFile.readline()
if len(templateFileLines) == 0:
  raise ValueError("empty template file?? failed.")
  
  
modelFileNamesList = list(dirEntry.name for dirEntry in os.scandir(MODEL_FOLDER_PATH) if dirEntry.name.endswith(".blockymodel"))
  
for modelFileName in modelFileNamesList:
  shapeNameWithDepth = remove_suffix(modelFileName, ".blockymodel")
  shapeNameWithoutDepth = remove_suffix(shapeNameWithDepth, "_Db1000")
  iconMaskFileName = shapeNameWithoutDepth + ".png"
  
  for dataPage in DATA_PAGES:
    for family in data_page_get_value(dataPage, "FAMILY_LIST"):
      unpatchedTextureFileBaseName = f"{data_page_get_value(dataPage, 'TEXTURE_NAME_PREFIX')}{family}{data_page_get_value(dataPage, 'TEXTURE_NAME_SUFFIX')}"
      textureFileName = patch_texture_name(unpatchedTextureFileBaseName+".png")
      
      assetInfo = {"full_name": data_page_get_value(dataPage, "JSON_TAGS_TYPE_STR") + "_" + family + "_" + shapeNameWithoutDepth}
      assetInfo["output_file_path"] = OUTPUT_FOLDER_PATH + SEP + assetInfo["full_name"] + ".json"
      assetInfo["icon_file_name"] = assetInfo["full_name"] + ".png"
      assetInfo["icon_file_path"] = ICON_FOLDER_PATH + SEP + assetInfo["icon_file_name"]
      
      assetContents = {
        "ICON_PATH_IN_MOD": "Icons/ItemsGenerated/" + assetInfo["icon_file_name"],
        "BLOCK_SET": unpatchedTextureFileBaseName,
        "TEXTURE_PATH_IN_MOD": f"BlockTextures/{textureFileName}",
        "RESOURCE_TYPE_ID_TO_CRAFT": f"{data_page_get_value(dataPage, 'JSON_TAGS_TYPE_STR')}_{family}",
      }
      
      with Image.open(MODEL_FOLDER_PATH + SEP + iconMaskFileName) as thumbnailMaskImage:
        print(thumbnailMaskImage.size)
        with Image.open(HYTALE_BLOCKTEXTURES_PATH + SEP + textureFileName) as thumbnailTextureImage:
          print(thumbnailTextureImage.size)
          thumbnailResultImage = ImageChops.multiply(thumbnailMaskImage.convert("RGB"), thumbnailTextureImage.convert("RGB"))
          thumbnailResultImage.save(assetInfo["icon_file_path"])
          
          
      outputFilePath = assetInfo["output_file_path"]
      if os.path.exists(outputFilePath):
        print(f"replacing {outputFilePath}")
        os.remove(outputFilePath)
      else:
        print(f"creating {outputFilePath}")
        
      with open(outputFilePath, "w") as outputFile:

        for currentLine in templateFileLines:
          outputLine = currentLine.replace("${FULL_NAME}", assetInfo["full_name"]
            ).replace("${MODEL_BASE_NAME}", shapeNameWithDepth
            ).replace("${ICON_PATH_IN_MOD}", assetContents["ICON_PATH_IN_MOD"]
            ).replace("${SET}", assetContents["BLOCK_SET"]
            ).replace("${RESOURCE_TYPE_ID_TO_CRAFT}", assetContents["RESOURCE_TYPE_ID_TO_CRAFT"]
            ).replace("${TEXTURE_PATH_IN_MOD}", assetContents["TEXTURE_PATH_IN_MOD"]
            ).replace("${JSON_TAGS_TYPE_STR}", data_page_get_value(dataPage, "JSON_TAGS_TYPE_STR")
            ).replace("${JSON_TAGS_SUBTYPE}", data_page_get_value(dataPage, "JSON_TAGS_SUBTYPE")
            ).replace("${JSON_TAGS_FAMILY}", data_page_get_value(dataPage, "JSON_TAGS_FAMILY")
            ).replace("${JSON_GATHERING_BREAKING_GATHERTYPE_STR}", data_page_get_value(dataPage, "JSON_GATHERING_BREAKING_GATHERTYPE_STR")
            ).replace("${JSON_FUEL_QUALITY_LINE}", data_page_get_value(dataPage, "JSON_FUEL_QUALITY_LINE")
            ).replace("${FAMILY}", family # must happen after json_ items
            )
          assert "${" not in outputLine, outputLine
          outputFile.write(outputLine)
      