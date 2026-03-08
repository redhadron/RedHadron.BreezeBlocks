import os
import shutil

SEP = os.sep
# DECOMPRESSED_HYTALE_ASSETS_PATH = 
PLANK_TYPES = list("Darkwood Deadwood Drywood Goldenwood Greenwood Hardwood Lightwood Redwood Softwood Tropicalwood".split(" "))

modPath = SEP.join([os.getcwd(), ".."])
modelFolderPath = SEP.join([modPath, "Common", "Blocks", "Breeze"])
# print(modelFolderPath)
outputFolderPath = SEP.join([modPath, "Server", "Item", "Items"])
# print(outputFolderPath)
TEMPLATE_FILE_PATH = os.getcwd() + SEP + "Breeze_Template.json"
# print(f"{TEMPLATE_FILE_PATH=}")
# _ = input("press enter...")




def remove_suffix(a, b):
  assert a.endswith(b)
  return a[:-len(b)]
  
  

templateFileLines = []
with open(TEMPLATE_FILE_PATH, "r") as templateFile:
  print("opened template file.")
  currentLine = templateFile.readline()
  while len(currentLine) > 0:
    templateFileLines.append(currentLine)
    currentLine = templateFile.readline()
if len(templateFileLines) == 0:
  raise ValueError("empty template file?? failed.")
  
  
  
  
  
for dirEntry in os.scandir(modelFolderPath):
  if not dirEntry.name.endswith(".blockymodel"):
    continue
  shapeName = remove_suffix(dirEntry.name, ".blockymodel")
  shapeNameWithoutDepth = remove_suffix(shapeName, "_Db1000") # if this fails, it's because the code is incomplete and it should only be using the Db1000 model as a cue to create a thumbnail image because other depths of model should be using the same thumbnail as that one OR they shouldn't have thumbnails at all because they should never exist in the inventory, depending on design choices I make in the future.
  iconFileName = shapeNameWithoutDepth + ".png"
  
  shutil.copy(
    modelFolderPath + SEP + iconFileName,
    SEP.join([modPath, "Common", "Icons", "ItemsGenerated", iconFileName])
  )
  
  materialType = "Wood"
  for material in PLANK_TYPES:
    assert materialType=="Wood", "form cannot be planks unless type is wood"
    materialForm = "Planks"
    
    fullName = materialType + "_" + material + "_" + shapeName
    outputFilePath = outputFolderPath + SEP + fullName + ".json"
    
    assetContents = {
      "ICON_PATH_IN_MOD": "Icons/ItemsGenerated/" + iconFileName,
      "BLOCK_SET": f"{materialType}_{material}_{materialForm}",
      "TEXTURE_PATH_IN_MOD": f"BlockTextures/{materialType}_{material}_{materialForm}.png".replace("Wood_Softwood_Planks.png", "Wood_Softwood_Planks_Top.png").replace("Wood_Greenwood_Planks.png", "Wood_Green.png"),
      "RESOURCE_TYPE_ID": f"{materialType}_{material}",
    }
    
    if os.path.exists(outputFilePath):
      print(f"replacing {outputFilePath=}")
      os.remove(outputFilePath)
    else:
      print(f"creating {outputFilePath=}")
    with open(outputFilePath, "w") as outputFile:
      print(f"opened output file.")

      for currentLine in templateFileLines:
        outputLine = currentLine.replace("${FULL_NAME}", fullName
          ).replace("${MODEL_NAME}", shapeName
          ).replace("${ICON_PATH_IN_MOD}", assetContents["ICON_PATH_IN_MOD"]
          ).replace("${SET}", assetContents["BLOCK_SET"]
          ).replace("${RESOURCE_TYPE_ID}", assetContents["RESOURCE_TYPE_ID"]
          ).replace("${TEXTURE_PATH_IN_MOD}", assetContents["TEXTURE_PATH_IN_MOD"])
        assert "${" not in outputLine
        outputFile.write(outputLine)
    print("closed output file.")
    