import os
import directory_tree



def pretty_input(prompt, *, default):
  assert isinstance(prompt, str) and isinstance(default, str)
  print("\ndefault value: " + default)
  result = input(prompt)
  return result if len(result) > 0 else default


os.chdir("..")
directory_tree.DisplayTree(onlyDirs=True, ignoreList=["*.ignore*"]) # https://pypi.org/project/directory-tree/

print("\nmultiple folders can be specified with commas between them")

foldersOfNamesToChange = pretty_input("path of folder in which to perform edits> ", default=".\\Common\\Blocks\\Breeze,.\\Common\\Icons\\ItemsGenerated,.\\Server\\Item\\Items").split(",")
assert all(os.path.exists(name) for name in foldersOfNamesToChange)

foldersOfContentsToEdit = pretty_input("path of folder in which to edit file contents> ", default=".\\Server\\Item\\Items,.\\Common\\Blocks\\Breeze").split(",")
assert all(os.path.exists(name) for name in foldersOfContentsToEdit)

extensionsToEdit = pretty_input("extensions to edit> ", default=".json,.txt").split(",")
assert all(item.startswith(".") and len(item)>1 for item in extensionsToEdit)

changesStr = input("semicolon-separated pairs of comma-separated values> ")



def bisect_at_infix(string, infix):
  assert string.count(infix) == 1
  a, b = string.split(infix)
  return (a, b)
  
  
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
