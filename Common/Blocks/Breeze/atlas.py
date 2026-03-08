
from bidict import bidict
from PIL import Image

import enum
import argparse
import os
import json
import ast


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
# EXIT_CODES = {"SUCCESS":0, "ASSERTION_FAILURE":1}

def validate_int_pair_tuple(int_tuple):
  assert isinstance(int_tuple, tuple) and len(int_tuple) == 2 and all(isinstance(item, int) for item in int_tuple)

def tuple_to_pretty_coordinate(input_tuple):
  validate_int_pair_tuple(input_tuple)
  return f"row {input_tuple[1]} col {input_tuple[0]}"
assert tuple_to_pretty_coordinate((5, 678)) == "row 678 col 5"
  
def remove_prefix(string, prefix):
  assert len(prefix) <= len(string)
  assert len(prefix) > 0
  assert string.startswith(prefix)
  return string[len(prefix):]
  
def bisect_at_infix(string, infix):
  assert string.count(infix) == 1
  a, b = string.split(infix)
  return (a, b)

def pretty_coordinate_to_tuple(input_string):
  y, x = (int(item) for item in bisect_at_infix(remove_prefix(input_string, "row "), " col "))
  return (x, y)
assert pretty_coordinate_to_tuple("row 12 col 34") == (34, 12)
  

config_data = {
  "coordinates_to_names": bidict(),
  "tile_size": (32, 32),
  "atlas_size": (4, 16),
}

def get_atlas_image_size():
  return (config_data["tile_size"][0]*config_data["atlas_size"][0], 
    config_data["tile_size"][1]*config_data["atlas_size"][1])
  
def get_intersection_coordinate(intersection_address):
  return (config_data["tile_size"][0]*intersection_address[0], config_data["tile_size"][1]*intersection_address[1])
  
def get_a_free_address():
  for y in range(config_data["atlas_size"][1]):
    for x in range(config_data["atlas_size"][0]):
      if (x,y) not in config_data["coordinates_to_names"]:
        return (x,y)
  assert False, "out of room"




def config_file_to_string():
  with open(ATLAS_CONFIG_PATH, "r") as configFile:
    return configFile.read()

def load_config():
  configText = config_file_to_string()
  configData = json.loads(configText)
  assert len(config_data["coordinates_to_names"]) == 0, "config data should not be loaded twice!"
  for keyString, value in configData["coordinates_to_names"].items():
    key = ast.literal_eval(keyString)
    validate_int_pair_tuple(key)
    assert key not in config_data["coordinates_to_names"]
    # value duplicates are allowed, though.
    config_data["coordinates_to_names"][key] = value

def config_data_to_string():
  configData = {"coordinates_to_names":{str(key): value for key, value in config_data["coordinates_to_names"].items()}}
  return json.dumps(configData, sort_keys=ATLAS_CONFIG_SORT_KEYS, indent=ATLAS_CONFIG_INDENT)

def save_config():
  textToWrite = config_data_to_string()
  with open(ATLAS_CONFIG_PATH, "w") as configFile:
    configFile.write(textToWrite)
  
def config_data_has_changed():
  return config_data_to_string() != config_file_to_string()



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
  
def create_atlas_config():
  if os.path.exists(ATLAS_CONFIG_PATH):
    raise FileExistsError()
  save_config()
  
def delete_atlas_config():
  assert ATLAS_CONFIG_PATH.endswith(".json"), "invalid atlas config path"
  if not os.path.exists(ATLAS_CONFIG_PATH):
    raise FileNotFoundError()
  os.remove(ATLAS_CONFIG_PATH)
  
def assert_config_is_saved_correctly():
  if config_data_has_changed():
    print("config data changed unexpectedly.")
    print("config data:")
    print(config_data_to_string())
    print("config file:")
    print(config_file_to_string())
    print("the program will exit.")
    assert False
    


def do_tile_transport(direction, discover=False):
  if not os.path.exists(ATLAS_IMAGE_PATH):
    create_atlas_image()
    
  with Image.open(ATLAS_IMAGE_PATH) as atlasImg:
    if direction is TRANSPORT_DIRECTION.EXPORT:
      if discover:
        raise NotImplementedError("discover is not available while exporting yet.")
      for y in range(config_data["atlas_size"][1]):
        for x in range(config_data["atlas_size"][0]):
          if (x,y) not in config_data["coordinates_to_names"]:
            continue
          locationInAtlasImage = (*get_intersection_coordinate((x,y)), *get_intersection_coordinate((x+1,y+1)))
          tileImg = atlasImg.crop(locationInAtlasImage)
          tileImgPath = TILE_FOLDER + SEP + config_data["coordinates_to_names"][(x,y)]
          if os.path.exists(tileImgPath):
            with Image.open(tileImgPath) as oldTileImg:
              if oldTileImg.getbbox() != tileImg.getbbox():
                raise FileExistsError("the tile will not be overwritten because it is of a different size.")
          tileImg.save(tileImgPath)
    else:
      assert direction is TRANSPORT_DIRECTION.IMPORT
      for tileName in (item for item in os.listdir(TILE_FOLDER) if item.endswith(".png") and item != ATLAS_IMAGE_NAME):
        if tileName not in config_data["coordinates_to_names"].inverse:
          if discover:
            config_data["coordinates_to_names"].inverse[tileName] = get_a_free_address()
        if tileName in config_data["coordinates_to_names"].inverse:
          with Image.open(TILE_FOLDER + SEP + tileName) as tileImg:
            # TODO check whether coordinate is valid
            atlasImg.paste(tileImg, get_intersection_coordinate(config_data["coordinates_to_names"].inverse[tileName]))
            
    atlasImg.save(ATLAS_IMAGE_PATH)






"""
texture atlas editor commands:
  atlas-image <create|delete>
  atlas-config <create|delete>
  transport in [--discover]
  transport out
  detect-rename //only pays attention to files that can no longer be found
"""
parser = argparse.ArgumentParser()
subparser_manager = parser.add_subparsers(dest="subcommand")

atlas_image_cmd_parser = subparser_manager.add_parser("atlas-image")
atlas_image_cmd_parser.add_argument("subaction")

atlas_config_cmd_parser = subparser_manager.add_parser("atlas-config")
atlas_config_cmd_parser.add_argument("subaction")

transport_cmd_parser = subparser_manager.add_parser("transport")
transport_cmd_parser.add_argument("direction")
transport_cmd_parser.add_argument("--discover", action="store_true")

detect_rename_cmd_parser = subparser_manager.add_parser("detect-rename")


args = parser.parse_args()
if args.subcommand == "atlas-image":
  if args.subaction == "create":
    create_atlas_image()
  elif args.subaction == "delete":
    delete_atlas_image()
  else:
    assert args.subaction == "view", ars.subaction
    assert os.path.exists(ATLAS_IMAGE_PATH) and ATLAS_IMAGE_PATH.endswith(".png")
    os.startfile(ATLAS_IMAGE_PATH)
elif args.subcommand == "atlas-config":
  if args.subaction == "create":
    create_atlas_config()
  else:
    assert args.subaction == "delete", ars.subaction
    delete_atlas_config()
elif args.subcommand == "transport":
  direction = PARSE_TRANSPORT_DIRECTION(args.direction)
  assert args.discover is True or args.discover is False
  load_config()
  assert_config_is_saved_correctly()
  do_tile_transport(direction, discover=args.discover)
  if direction is TRANSPORT_DIRECTION.IMPORT and args.discover:
    save_config()
  else:
    assert_config_is_saved_correctly()
  
else:
  assert args.subcommand == "detect-rename", args.subcommand
  raise NotImplementedError()