
from bidict import bidict
from PIL import Image
import enum
import argparse


"""
todo:
  2d range
"""

ATLAS_IMAGE_PATH = ".\\atlas_image.png"
ATLAS_CONFIG_PATH = ".\\atlas_config.json"
ATLAS_IMAGE_CREATION_FILL_COLOR = (255, 255, 255)
class TRANSPORT_DIRECTION(enum.Enum):
  IMPORT = enum.auto()
  EXPORT = enum.auto()
def PARSE_TRANSPORT_DIRECTION(string):
  return {"in": TRANSPORT_DIRECTION.IMPORT, "out": TRANSPORT_DIRECTION.EXPORT}[string]

coordinates_to_paths = bidict()
tile_size = (32, 32)
atlas_size = (4, 16)

def get_atlas_image_size():
  return (tile_size[0]*atlas_size[0], tile_size[1]*atlas_size[1])
def get_intersection_coordinate(intersection_id):
  return (tile_size[0]*intersection_id[0], tile_size[1]*intersection_id[1])

def create_atlas_image():
  atlasImg = Image.new(mode="RGB", size=get_atlas_image_size(), color=ATLAS_IMAGE_CREATION_FILL_COLOR)
  atlasImg.save(ATLAS_IMAGE_PATH)

def do_tile_transport(direction):
  if not os.path.exists(ATLAS_IMAGE_PATH):
    create_atlas_image()
  with open(ATLAS_IMAGE_PATH) as atlasImg:
    for y in range(atlas_size[1]):
      for x in range(atlas_size[0]):
        locationInAtlasImage = (*get_intersection_coordinate((x,y)), *get_intersection_coordinate((x+1,y+1)))
        if direction is TRANSPORT_DIRECTION.EXPORT:
          tileImg = atlasImg.crop(locationInAtlasImage)
          timeImg.save(coordinates_to_paths[(x,y)])
        else:
          assert direction is TRANSPORT_DIRECTION.IMPORT
          with Image.open(coordinates_to_paths[(x,y)]) as tileImg:
            atlasImg.paste(tileImg, (x,y))
  atlasImg.save(ATLAS_IMAGE_PATH)



"""
texture atlas editor commands:
  atlas-image <create|delete>
  atlas-config <create|delete>
  transport <in|out>
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
    raise NotImplementedError()
elif args.subcommand == "atlas-config":
  raise NotImplementedError()
elif args.subcommand == "transport":
  do_tile_transport(PARSE_TRANSPORT_DIRECTION(args.direction))
else:
  assert args.subcommand == "detect-rename", args.subcommand
  raise NotImplementedError()