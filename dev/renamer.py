

# builtin:
import os
import sys
import subprocess

# project:
from Affixes import bisect_at_infix

# third party:
import directory_tree



def pretty_input(prompt, *, default):
  assert isinstance(prompt, str) and isinstance(default, str)
  print("\ndefault value: " + default)
  result = input(prompt)
  return result if len(result) > 0 else default

"""
def list_with_one_value_removed(input_list, value_to_remove):
  result = [item for item in input_list if item != value_to_remove]
  assert len(result) == len(input_list) - 1
  return result
"""
def remove_one_value_from_list(input_list, value_to_remove):
  assert hasattr(input_list, "__delitem__")
  startingLength = len(input_list)
  for i, value in enumerate(input_list):
    if value == value_to_remove:
      del input_list[i]
  assert len(input_list) == startingLength - 1


os.chdir("..")
directory_tree.DisplayTree(onlyDirs=True, ignoreList=["*.ignore*"]) # https://pypi.org/project/directory-tree/


MODEL_FOLDER = ".\\Common\\Blocks\\Breeze"
ICON_FOLDER = ".\\Common\\Icons\\ItemsGenerated"
ITEM_FOLDER = ".\\Server\\Item\\Items"
GENERATE_SCRIPT_PATH = ".\\dev\\generate.py"

print("\nmultiple folders can be specified with commas between them")

foldersOfNamesToChange = pretty_input("path of folder in which to perform edits> ", default=MODEL_FOLDER + "," + ICON_FOLDER + "," + ITEM_FOLDER).split(",")
assert all(os.path.exists(name) for name in foldersOfNamesToChange)

foldersOfContentsToEdit = pretty_input("path of folder in which to edit file contents> ", default=MODEL_FOLDER + "," + ITEM_FOLDER).split(",")
assert all(os.path.exists(name) for name in foldersOfContentsToEdit)

extensionsToEdit = pretty_input("extensions to edit> ", default=".json,.txt").split(",")
assert all(item.startswith(".") and len(item)>1 for item in extensionsToEdit)

changesStr = input("semicolon-separated pairs of comma-separated values> ")

regenerateAssets = {"y": True, "": True, "n": False}[input("regenerate assets Y/n> ").lower()]

if regenerateAssets:
  remove_one_value_from_list(foldersOfContentsToEdit, ITEM_FOLDER)
  # at the end of this file, GENERATE_SCRIPT_PATH will run in a subprocess. This means that all items in the item folder will be deleted and regenerated anyway, so there is no point in editing them first.
  
  

  
  
successfulChanges = []

for folderOfNamesToChange in foldersOfNamesToChange:
  for name in os.listdir(folderOfNamesToChange):
    assert len(name) > 0
    for changeStr in changesStr.split(";"):
      try:
        string1, string2 = bisect_at_infix(changeStr, ",")
        assert len(string1) > 0
      except:
        print(f"failed for changeStr {changeStr}")
        continue
      if string1 in name:
        newName = name.replace(string1, string2)
        assert newName != name
        os.rename(folderOfNamesToChange + os.sep + name, folderOfNamesToChange + os.sep + newName)
        successfulChanges.append((name, newName))
        print(f"renamed {name} to {newName}")
      else:
        print(f"skipped {name}")
      
for folderOfContentsToEdit in foldersOfContentsToEdit:
  for currentName in os.listdir(folderOfContentsToEdit):
    if not any(currentName.endswith(ext) for ext in extensionsToEdit):
      continue
    currentPath = folderOfContentsToEdit + os.sep + currentName
    with open(currentPath, "r") as currentFile:
      text = currentFile.read()
    if any(oldName in text for oldName, _ in successfulChanges):
      with open(currentPath, "w") as currentFile:
        print(f"modifying file {currentPath}...")
        for change in successfulChanges:
          text = text.replace(*change)
        currentFile.seek(0)
        currentFile.write(text)
        currentFile.truncate()



if regenerateAssets: # (BreezeBlocks mod-specific)
  subprocess.run([sys.executable, GENERATE_SCRIPT_PATH])