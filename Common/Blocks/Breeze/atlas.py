
from bidict import bidict
from PIL import Image
import enum
import argparse
import os


"""
todo:
  2d range
"""

TILE_FOLDER = "."
SEP = os.sep
ATLAS_IMAGE_NAME = "atlas_image.png"
ATLAS_IMAGE_PATH = ".\\" + ATLAS_IMAGE_NAME
ATLAS_CONFIG_PATH = ".\\atlas_config.json"
ATLAS_CONFIG_SORT_KEYS = True
ATLAS_CONFIG_INDENT = 4
ATLAS_IMAGE_CREATION_FILL_COLOR = (255, 255, 255)
class TRANSPORT_DIRECTION(enum.Enum):
  IMPORT = enum.auto()
  EXPORT = enum.auto()
def PARSE_TRANSPORT_DIRECTION(string):
  return {"in": TRANSPORT_DIRECTION.IMPORT, "out": TRANSPORT_DIRECTION.EXPORT}[string]

coordinates_to_names = bidict()
tile_size = (32, 32)
atlas_size = (4, 16)


def get_atlas_image_size():
  return (tile_size[0]*atlas_size[0], tile_size[1]*atlas_size[1])
  
def get_intersection_coordinate(intersection_address):
  return (tile_size[0]*intersection_address[0], tile_size[1]*intersection_address[1])
  
def get_a_free_address():
  for y in range(atlas_size[1]):
    for x in range(atlas_size[0]):
      if (x,y) not in coordinates_to_names:
        return (x,y)
  assert False, "out of room"        


def create_atlas_image():
  if os.path.exists(ATLAS_IMAGE_PATH):
    raise FileExistsError()
  atlasImg = Image.new(mode="RGB", size=get_atlas_image_size(), color=ATLAS_IMAGE_CREATION_FILL_COLOR)
  atlasImg.save(ATLAS_IMAGE_PATH)
  
def delete_atlas_image():
  assert ATLAS_IMAGE_PATH.endswith(".png"), "invalid atlas image path"
  if not os.path.exists(ATLAS_IMAGE_PATH):
    raise FileNotFoundError()
  os.remove(ATLAS_IMAGE_PATH)


def do_tile_transport(direction, discover=False):
  if not os.path.exists(ATLAS_IMAGE_PATH):
    create_atlas_image()
    
  with open(ATLAS_IMAGE_PATH) as atlasImg:
    if direction is TRANSPORT_DIRECTION.EXPORT:
      if discover:
        raise NotImplementedError("discover is not available while exporting yet.")
      for y in range(atlas_size[1]):
        for x in range(atlas_size[0]):
          if (x,y) not in coordinates_to_paths:
            continue
          locationInAtlasImage = (*get_intersection_coordinate((x,y)), *get_intersection_coordinate((x+1,y+1)))
          tileImg = atlasImg.crop(locationInAtlasImage)
          timeImg.save(coordinates_to_names[(x,y)])
    else:
      assert direction is TRANSPORT_DIRECTION.IMPORT
      for tileName in (dirEntry.name for dirEntry in os.scandir(TILE_FOLDER) if dirEntry.name.endswith(".png") and dirEntry.name != ATLAS_IMAGE_NAME):
        if tileName not in coordinates_to_names.invert:
          if discover:
            coordinates_to_names.invert[tileName] = get_a_free_address()
        if tileName in coordinates_to_names.invert:
          with Image.open(TILE_FOLDER + SEP + tileName) as tileImg:
            atlasImg.paste(tileImg, get_intersection_coordinate(coordinates_to_names.invert[tileName]))
  atlasImg.save(ATLAS_IMAGE_PATH)


def load_config():
  with open(ATLAS_CONFIG_PATH, "r") as configFile:
    configText = configFile.read()
  configData = json.loads(configText)
  assert len(coordinates_to_paths) == 0
  for key, value in configData["coordinates_to_paths"].items():
    assert key not in coordinates_to_paths
    # value duplicates are allowed, though.
    coordinates_to_paths[key] = value


def save_config():
  configData = {"coordinates_to_paths":{key: value for key, value in coordinates_to_paths.items()}}
  textToWrite = json.dumps(configData, sort_keys=ATLAS_CONFIG_SORT_KEYS, indent=ATLAS_CONFIG_INDENT)
  with open(ATLAS_CONFIG_PATH, "w") as configFile:
    configFile.write(textToWrite)
  

"""
texture atlas editor commands:
  atlas-image <create|delete>
  atlas-config <create|delete>
  transport in [--discover]
  transport out
  detect-rename
"""
parser = argparse.ArgumentParser()
subparser_manager = parser.add_subparsers(dest="subcommand")

atlas_image_cmd_parser = subparser_manager.add_parser("atlas-image")
atlas_image_cmd_parser.add_argument("subaction")

atlas_config_cmd_parser = subparser_manager.add_parser("atlas-config")
atlas_config_cmd_parser.add_argument("subaction")

transport_cmd_parser = subparser_manager.add_parser("transport")
transport_cmd_parser.add_argument("direction")

detect_rename_cmd_parser = subparser_manager.add_parser("detect-rename")


args = parser.parse_args()
print(args)
if args.subcommand == "atlas-image":
  if args.subaction == "create":
    create_atlas_image()
  else:
    assert args.subaction == "delete", ars.subaction
    delete_atlas_image()
elif args.subcommand == "atlas-config":
  raise NotImplementedError()
elif args.subcommand == "transport":
  do_tile_transport(PARSE_TRANSPORT_DIRECTION(args.direction))
else:
  assert args.subcommand == "detect-rename", args.subcommand
  raise NotImplementedError()