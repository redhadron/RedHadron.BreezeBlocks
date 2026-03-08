import os
# import shutil
from PIL import Image, ImageChops

SEP = os.sep
HYTALE_ASSETS_PATH = "E:\Hytale Assets 20260221" # path to a folder in which you have put the contents of Assets.zip after extracting them.
HYTALE_BLOCKTEXTURES_PATH = HYTALE_ASSETS_PATH + SEP + "Common" + SEP + "BlockTextures"
PLANK_TYPES = list("Blackwood Darkwood Deadwood Drywood Goldenwood Greenwood Hardwood Lightwood Redwood Softwood Tropicalwood".split(" "))

modPath = SEP.join([os.getcwd(), ".."])
modelFolderPath = SEP.join([modPath, "Common", "Blocks", "Breeze"])
assert os.path.exists(modelFolderPath)
outputFolderPath = SEP.join([modPath, "Server", "Item", "Items"])
assert os.path.exists(outputFolderPath)
iconFolderPath = SEP.join([modPath, "Common", "Icons", "ItemsGenerated"])
assert os.path.exists(iconFolderPath)
TEMPLATE_FILE_PATH = os.getcwd() + SEP + "Breeze_Template.json"
assert os.path.exists(TEMPLATE_FILE_PATH)



def remove_suffix(a, b):
  assert a.endswith(b)
  return a[:-len(b)]
  
def patch_texture_name(input_string):
  return input_string.replace("Wood_Softwood_Planks.png", "Wood_Softwood_Planks_Top.png").replace("Wood_Greenwood_Planks.png", "Wood_Green.png")
  
  

templateFileLines = []
with open(TEMPLATE_FILE_PATH, "r") as templateFile:
  print("opened template file.")
  currentLine = templateFile.readline()
  while len(currentLine) > 0:
    templateFileLines.append(currentLine)
    currentLine = templateFile.readline()
if len(templateFileLines) == 0:
  raise ValueError("empty template file?? failed.")
  
  
modelFileNamesList = list(dirEntry.name for dirEntry in os.scandir(modelFolderPath) if dirEntry.name.endswith(".blockymodel"))
  
  
for modelFileName in modelFileNamesList:
  shapeName = remove_suffix(modelFileName, ".blockymodel")
  shapeNameWithoutDepth = remove_suffix(shapeName, "_Db1000")
  iconMaskFileName = shapeNameWithoutDepth + ".png"
  
  materialType = "Wood"
  for material in PLANK_TYPES:
    assert materialType=="Wood", "form cannot be planks unless type is wood"
    materialForm = "Planks"
      
    textureFileName = patch_texture_name(f"{materialType}_{material}_{materialForm}.png")
    
    assetInfo = {
      "full_name": materialType + "_" + material + "_" + shapeName,
    }
    assetInfo["output_file_path"] = outputFolderPath + SEP + assetInfo["full_name"] + ".json"
    assetInfo["icon_file_name"] = assetInfo["full_name"] + ".png"
    assetInfo["icon_file_path"] = iconFolderPath + SEP + assetInfo["icon_file_name"]
    
    assetContents = {
      "ICON_PATH_IN_MOD": "Icons/ItemsGenerated/" + assetInfo["icon_file_name"],
      "BLOCK_SET": f"{materialType}_{material}_{materialForm}",
      "TEXTURE_PATH_IN_MOD": f"BlockTextures/{textureFileName}",
      "RESOURCE_TYPE_ID": f"{materialType}_{material}",
    }
    
    with Image.open(modelFolderPath + SEP + iconMaskFileName) as thumbnailMaskImage:
      print(thumbnailMaskImage.getbbox())
      with Image.open(HYTALE_BLOCKTEXTURES_PATH + SEP + textureFileName) as thumbnailTextureImage:
        print(thumbnailTextureImage.getbbox())
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
          ).replace("${MODEL_NAME}", shapeName
          ).replace("${ICON_PATH_IN_MOD}", assetContents["ICON_PATH_IN_MOD"]
          ).replace("${SET}", assetContents["BLOCK_SET"]
          ).replace("${RESOURCE_TYPE_ID}", assetContents["RESOURCE_TYPE_ID"]
          ).replace("${TEXTURE_PATH_IN_MOD}", assetContents["TEXTURE_PATH_IN_MOD"])
        assert "${" not in outputLine
        outputFile.write(outputLine)
    