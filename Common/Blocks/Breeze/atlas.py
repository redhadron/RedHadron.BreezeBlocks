
from bidict import bidict
from PIL import Image, ImageTk, ImageDraw # the k in ImageTk is lowercase.

import enum
import argparse
import os
import json
import ast
import tkinter


"""
todo:
  -outline pixels in the save name prompt.
  -allow multiple values to be specified as blank, so that a solid-color tile in any of those colors will be ignored. Introduce checkerboard background pattern.
  -make a better atlas_config.json creation process, eliminate default values for atlas size and tile size.
  -2d range.
  -search "TODO" and "NotImplementedError" in this file.
"""

TILE_FOLDER = "."
SEP = os.sep
ATLAS_IMAGE_NAME = "atlas_image.png"
ATLAS_IMAGE_PATH = ".\\" + ATLAS_IMAGE_NAME
ATLAS_CONFIG_PATH = ".\\atlas_config.json"
ATLAS_CONFIG_SORT_KEYS = True
ATLAS_CONFIG_INDENT = 4
ATLAS_IMAGE_CREATION_FILL_COLOR = (255, 255, 255)
ATLAS_IMAGE_BLANK_COLOR = (*ATLAS_IMAGE_CREATION_FILL_COLOR, 255)
PREVIEW_SCALE = 10
PREVIEW_GRID_LINE_COLOR = (127, 127, 127)
class TRANSPORT_DIRECTION(enum.Enum):
  IMPORT = enum.auto()
  EXPORT = enum.auto()
def PARSE_TRANSPORT_DIRECTION(string):
  return {"in": TRANSPORT_DIRECTION.IMPORT, "out": TRANSPORT_DIRECTION.EXPORT}[string]
EXIT_CODES = {"GENERAL_SUCCESS":0, "EXIT_BUTTON": 2}

def validate_int_pair_tuple(int_tuple):
  assert isinstance(int_tuple, tuple) and len(int_tuple) == 2 and all(isinstance(item, int) for item in int_tuple)

def tuple_to_pretty_coordinate(input_tuple):
  validate_int_pair_tuple(input_tuple)
  return f"row {input_tuple[1]} col {input_tuple[0]}"
assert tuple_to_pretty_coordinate((5, 678)) == "row 678 col 5"
  
def remove_suffix(string, suffix):
  assert len(suffix) <= len(string)
  assert len(suffix) > 0
  assert string.endswith(suffix)
  return string[:-len(suffix)]
  
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

# TODO introduce pretty coordinates to actual atlas config file.
  
# def nand(a, b):
#  return not (a and b)
  
def at_most_one(input_list):
  return sum(bool(item) for item in input_list) in (0, 1)
  
  

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
  configData = dict()
  for cfgKey in config_data.keys():
    if cfgKey == "coordinates_to_names":
      configData[cfgKey] = {str(coord): name for coord, name in config_data["coordinates_to_names"].items()}
    else:
      configData[cfgKey] = config_data[cfgKey]
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



class PromptResponseType:
  def __init__(self):
    pass
class Submit(PromptResponseType):
  def __init__(self, value):
    self.value = value
class Skip(PromptResponseType):
  pass
class Exit(PromptResponseType):
  pass 
  
def prompt_user_for_tile_name(tile_image):
  assert isinstance(tile_image, Image.Image) # tile_image must be a PIL Image # is this even true?
  window = tkinter.Tk()
  window.configure(bg="#cccccc")
  topLabel = tkinter.Label(window, text="Give this tile a name")
  topLabel.pack()
  
  previewSize = (config_data["tile_size"][0]*PREVIEW_SCALE, config_data["tile_size"][1]*PREVIEW_SCALE)
  modifiedTileImage = tile_image.resize(size=previewSize, resample=Image.Resampling.NEAREST) # resizing makes a copy so we are not drawing on the original.
  imageDrawer = ImageDraw.Draw(modifiedTileImage) 
  for y in range(config_data["tile_size"][1]):
    imageDrawer.line((0,y*PREVIEW_SCALE,modifiedTileImage.size[0],y*PREVIEW_SCALE), PREVIEW_GRID_LINE_COLOR)
  for x in range(config_data["tile_size"][0]):
    imageDrawer.line((x*PREVIEW_SCALE, 0, x*PREVIEW_SCALE, modifiedTileImage.size[1]), PREVIEW_GRID_LINE_COLOR)
    
  
  canvas = tkinter.Canvas(window, width=previewSize[0], height=previewSize[1])
  canvas.pack()
  tkinterImage = ImageTk.PhotoImage(image=modifiedTileImage, size=previewSize)
  tkinterImageSprite = canvas.create_image(previewSize[0]//2, previewSize[1]//2, image=tkinterImage)
  
  entryStringVar = tkinter.StringVar()
  entry = tkinter.Entry(window, textvariable=entryStringVar)
  entry.focus_set()
  entry.pack()
  
  class PromptResultHolder:
    def __init__(self):
      self.value = None
  promptResultHolder = PromptResultHolder()
  
  def okayCallback(*args, **kwargs):
    entryText = entry.get()
    if not entryText.endswith(".png"):
      print("name must end with .png")
      return
    if not len(remove_suffix(entryText, ".png")) > 0:
      print("name must be longer")
      return
    if entryText.lower() == ATLAS_IMAGE_NAME.lower():
      print("name must not match the name of the atlas image")
      return
    if any(char in "\/\:*?\"<>|" for char in entryText):
      print("name contains invalid character") # TODO
      return
    promptResultHolder.value = Submit(entryText)
    window.destroy()
  entry.bind('<Return>', okayCallback)
  okayButton = tkinter.Button(text="OK", command=okayCallback)
  okayButton.bind('<Return>', okayCallback)
  okayButton.pack()
  
  def skipCallback(*args, **kwargs):
    promptResultHolder.vale = Skip()
    window.destroy()
  skipButton = tkinter.Button(text="Skip", command=skipCallback)
  skipButton.bind('<Return>', skipCallback)
  skipButton.pack()
  
  def exitCallback(*args, **kwargs):
    print("Exit button pressed.")
    promptResultHolder.value = Exit()
    window.destroy()
  exitButton = tkinter.Button(text="Exit", command=exitCallback)
  exitButton.bind('<Return>', exitCallback)
  exitButton.pack()
  
  window.mainloop()
  
  return promptResultHolder.value
  
  
  

def tile_image_is_blank(tile_image):
  # assert tile_image.mode == "RGB", tile_image.mode
  assert tile_image.size == config_data["tile_size"]
  for pixelY in range(tile_image.size[1]):
    for pixelX in range(tile_image.size[0]):
      if tile_image.getpixel((pixelX,pixelY)) != ATLAS_IMAGE_BLANK_COLOR:
        return False
  return True
  
def find_tile_names():
  return [item for item in os.listdir(TILE_FOLDER) if item.endswith(".png") and item != ATLAS_IMAGE_NAME]

def do_tile_transport(direction, discover=False, organize=False):
  assert not (discover and organize)
    
  with Image.open(ATLAS_IMAGE_PATH) as atlasImg:
    if direction is TRANSPORT_DIRECTION.EXPORT:
      for y in range(config_data["atlas_size"][1]):
        for x in range(config_data["atlas_size"][0]):
          
          locationInAtlasImage = (*get_intersection_coordinate((x,y)), *get_intersection_coordinate((x+1,y+1)))
          tileImg = atlasImg.crop(locationInAtlasImage)
          if (x,y) not in config_data["coordinates_to_names"]:
            if discover and not tile_image_is_blank(tileImg):
              response = prompt_user_for_tile_name(tileImg)
              assert isinstance(response, PromptResponseType)
              if isinstance(response, Submit):
                newTileName = response.value
              elif isinstance(response, Skip):
                continue
              elif isinstance(response, Exit):
                exit(EXIT_CODES["EXIT_BUTTON"])
              else:
                raise ValueError()
              config_data["coordinates_to_names"][(x,y)] = newTileName
            else:
              continue # don't attempt to export.
          tileImgPath = TILE_FOLDER + SEP + config_data["coordinates_to_names"][(x,y)]
          if os.path.exists(tileImgPath):
            with Image.open(tileImgPath) as oldTileImg:
              if oldTileImg.size != tileImg.size:
                raise FileExistsError("the tile will not be overwritten because it is of a different size.")
          tileImg.save(tileImgPath)
    else:
      assert direction is TRANSPORT_DIRECTION.IMPORT
      if not os.path.exists(ATLAS_IMAGE_PATH):
        create_atlas_image()
      for tileName in find_tile_names():
        if tileName not in config_data["coordinates_to_names"].inverse:
          if discover:
            config_data["coordinates_to_names"].inverse[tileName] = get_a_free_address()
          elif organize:
            raise NotImplementedError("prompt to place a single tile")
        if tileName in config_data["coordinates_to_names"].inverse:
          with Image.open(TILE_FOLDER + SEP + tileName) as tileImg:
            # TODO check whether coordinate is valid
            if tileImg.size != config_data["tile_size"]:
              print(f"WARNING: Tile with name {tileName} will not be imported because it is the wrong size: {tileImg.size}")
              continue
            atlasImg.paste(tileImg, get_intersection_coordinate(config_data["coordinates_to_names"].inverse[tileName]))
            
    atlasImg.save(ATLAS_IMAGE_PATH)






"""
texture atlas editor commands:
  atlas-image <create|delete|view>
  atlas-config <create|delete|view>
  transport in [<--discover|--organize|--organize-all>]
  transport out [--discover]
  tiles delete [--confirm] //note: command must fail if confirm is provided when it is not necessary.
  // some way to regenerate or detect renamed tiles.
  // some way to swap tile positions, or copy tiles.
"""
parser = argparse.ArgumentParser()
subparser_manager = parser.add_subparsers(dest="subcommand")

atlas_image_cmd_parser = subparser_manager.add_parser("atlas-image", help="commands for handling the single atlas image for the project")
atlas_image_cmd_parser.add_argument("subaction")

atlas_config_cmd_parser = subparser_manager.add_parser("atlas-config", help="commands for handling the single atlas image")
atlas_config_cmd_parser.add_argument("subaction")

transport_cmd_parser = subparser_manager.add_parser("transport")
transport_cmd_parser.add_argument("direction")
transport_cmd_parser.add_argument("--discover", action="store_true")
transport_cmd_parser.add_argument("--organize", action="store_true")
transport_cmd_parser.add_argument("--organize-all", action="store_true")



args = parser.parse_args()
if args.subcommand == "atlas-image":
  # assert not any((args.discover, args.organize, args.organize_all))
  if args.subaction == "create":
    create_atlas_image()
  elif args.subaction == "delete":
    delete_atlas_image()
  elif args.subaction == "view":
    assert os.path.exists(ATLAS_IMAGE_PATH) and ATLAS_IMAGE_PATH.endswith(".png")
    os.startfile(ATLAS_IMAGE_PATH)
  else:
    raise ValueError(ars.subaction)
elif args.subcommand == "atlas-config":
  # assert not any((args.discover, args.organize, args.organize_all))
  if args.subaction == "create":
    create_atlas_config()
  elif args.subaction == "delete":
    delete_atlas_config()
  elif args.subaction == "view":
    assert os.path.exists(ATLAS_CONFIG_PATH)
    with open(ATLAS_CONFIG_PATH, "r") as configFile:
      print(configFile.read())
  else:
    raise ValueError(ars.subaction)
elif args.subcommand == "transport":
  load_config()
  assert_config_is_saved_correctly()
  direction = PARSE_TRANSPORT_DIRECTION(args.direction)
  assert args.discover is True or args.discover is False
  assert at_most_one((args.discover, args.organize, args.organize_all))
  if args.organize_all:
    raise NotImplementedError("a window to allow all tiles to be placed by the user into the atlas one by one") # this is only allowed while an atlas image does not exist, to prevent confusion from the atlas image and atlas config being completely different, which could cause data loss if you forget about it and then transport out and delete the atlas image.
  else:
    if direction is TRANSPORT_DIRECTION.EXPORT:
      assert not args.organize
      assert not args.organize_all
    do_tile_transport(direction, discover=args.discover, organize=args.organize)
  if args.discover:
    save_config()
  assert_config_is_saved_correctly()
else:
  raise ValueError(args.subcommand)
  
exit(EXIT_CODES["GENERAL_SUCCESS"])