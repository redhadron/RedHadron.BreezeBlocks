import os


folderToModify = input("path of folder in which to perform edits> ")
string1 = input("String 1> ")
string2 = input("String 2> ")
assert len(string1) > 0
# string 2 is allowed to be empty though
# folderItemStrs = os.listDir(folderToModify)
for dirEntry in os.scandir(folderToModify):
  name = dirEntry.name
  assert len(name) > 0
  if string1 in name:
    newName = name.replace(string1, string2)
    assert newName != name
    os.rename(folderToModify+os.sep+name, folderToModify+os.sep+newName)
    print(f"renamed {name} to {newName}")
  else:
    print(f"skipped {name}")