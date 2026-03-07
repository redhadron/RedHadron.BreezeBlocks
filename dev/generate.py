import os

sep = os.sep

modelFolderPath = sep.join([os.getcwd(), "..", "Common", "Blocks", "Breeze"])
# print(modelFolderPath)
outputFolderPath = sep.join([os.getcwd(), "..", "Server", "Item", "Items"])
# print(outputFolderPath)
TEMPLATE_FILE_PATH = os.getcwd() + sep + "Breeze_Template.json"
# print(f"{TEMPLATE_FILE_PATH=}")
# _ = input("press enter...")

material = "Wood_Goldenwood"



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
  modelName = remove_suffix(dirEntry.name, ".blockymodel")
  
  fullName = material + "_" + modelName
  outputFilePath = outputFolderPath + sep + fullName + ".json"
  if os.path.exists(outputFilePath):
    print(f"replacing {outputFilePath=}")
    os.remove(outputFilePath)
  else:
    print(f"creating {outputFilePath=}")
  with open(outputFilePath, "w") as outputFile:
    print(f"opened output file.")

    for currentLine in templateFileLines:
      outputLine = currentLine.replace("${FULL_NAME}", fullName).replace("${MODEL_NAME}", modelName)
      assert "${" not in outputLine
      outputFile.write(outputLine)
  print("closed output file.")
  