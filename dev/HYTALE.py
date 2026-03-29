
import os

# ----- Hytale path constants -----

HYTALE_ASSETS_PATH = "E:\Hytale Assets 20260328" # path to a folder in which you have put the contents of Assets.zip after decompressing.
assert os.path.isdir(HYTALE_ASSETS_PATH), "please extract hytale assets and configure the path to the exctracted assets within HYTALE.py"

SEP = os.sep

HYTALE_BLOCKTEXTURES_PATH = HYTALE_ASSETS_PATH + SEP + "Common" + SEP + "BlockTextures"
assert os.path.isdir(HYTALE_BLOCKTEXTURES_PATH)

HYTALE_BLOCKTEXTURE_FILE_NAMES = [item for item in os.listdir(HYTALE_BLOCKTEXTURES_PATH) if item.endswith(".png")]
assert len(HYTALE_BLOCKTEXTURE_FILE_NAMES) > 600
assert "Bone_Side.png" in HYTALE_BLOCKTEXTURE_FILE_NAMES