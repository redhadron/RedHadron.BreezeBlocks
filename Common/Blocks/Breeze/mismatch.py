import os
import itertools
import pprint


# PyPI
import directory_tree



def remove_suffix(string, suffix):
  assert len(suffix) <= len(string)
  assert len(suffix) > 0
  assert string.endswith(suffix), string + " does not end with " + suffix
  return string[:-len(suffix)]




def get_extension_if_present(input_string):
  if len(input_string) == 0:
    return None
  if input_string.startswith("."):
    return get_extension_if_present(input_string[1:])
  if "." in input_string:
    splitResult = input_string.split(".")
    assert len("".join(splitResult[:-1])) != 0, "something failed in leading dot case handling"
    return splitResult[-1]
  else:
    return None
    
def tagged_data_to_group_dict(input_data):
  result = dict()
  for key, value in input_data:
    if key in result:
      result[key].append(value)
    else:
      result[key] = [value]
  return result
    

directory_tree.DisplayTree()


fileFullNamesByExtension = tagged_data_to_group_dict((get_extension_if_present(name), name) for name in os.listdir())

fileBaseNamesByExtension = {extension: tuple((name if extension is None else remove_suffix(name, "."+extension)) for name in group) for extension, group in fileFullNamesByExtension.items()}

for extension, group in fileBaseNamesByExtension.items():
  for fileBaseNamePair in itertools.combinations(group, 2):
    assert not (fileBaseNamePair[0].startswith(fileBaseNamePair[1]) or fileBaseNamePair[1].startswith(fileBaseNamePair[0])), f"no file's base name may be a prefix to the name of another file with the same extension: {fileBaseNamePair}, {extension=}" # because this could cause multiple PNGs to match to a single model. Also it is a practice that should maybe just be avoided
    
    

# ----- procedure for BreezeBlocks icons and models -----

for modelBaseName in fileBaseNamesByExtension["blockymodel"]:
  _pngsForThisModel = [pngBaseName for pngBaseName in fileBaseNamesByExtension["png"] if modelBaseName.startswith(pngBaseName)]
  assert len(_pngsForThisModel) <= 1, f"cannot have multiple icon templates for a single model (yet): {_pngsForThisModel} <-> {modelBaseName!r}"
# del pngBaseName 
print("\n")
pprint.pprint(fileBaseNamesByExtension, indent=4, width=120)

resultsForPNGSearch = {"one_match": [], "multiple_matches": [], "no_matches": []}
for pngBaseName in fileBaseNamesByExtension["png"]:
  searchResults = [modelBaseName for modelBaseName in fileBaseNamesByExtension["blockymodel"] if modelBaseName.startswith(pngBaseName)]
  resultsForPNGSearch["one_match" if len(searchResults) == 1 else "no_matches" if len(searchResults) == 0 else "multiple_matches"].append((pngBaseName, searchResults))
print("\n")
pprint.pprint(resultsForPNGSearch, indent=4, width=120)