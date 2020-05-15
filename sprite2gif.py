from PIL import Image
from math import floor
from pathlib import Path
import sys
import argparse


def gen_frame(sprite):
    # Make sure the image has an alpha channel, then separate it into a new image
    im = sprite.convert("RGBA")
    alpha = im.getchannel("A")

    # Convert the image into P mode but only use 255 colors in the palette out of 256
    im = im.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)

    # Set all pixel values below 128 to 255 , and the rest to 0
    mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)

    # Paste the color of index 255 and use alpha as a mask
    im.paste(255, mask)

    # The transparency index is 255
    im.info["transparency"] = 255

    return im

# Disable add_help to add it to a different argument group
parser = argparse.ArgumentParser(add_help=False)
required_args = parser.add_argument_group("required arguments")
optional_args = parser.add_argument_group("optional arguments")

# Required arguments
required_args.add_argument(
    "-i",
    "--input",
    help="path to spritesheet",
    type=str,
    required=True
)
required_args.add_argument(
    "-x",
    "--x-frames",
    help="frames per row",
    type=int,
    required=True
)
required_args.add_argument(
    "-y",
    "--y-frames",
    help="frames per column",
    type=int,
    required=True
)

# Optional arguments
optional_args.add_argument(
    "-h",
    "--help",
    help="show this help message and exit",
    action="help"
)
optional_args.add_argument(
    "-d",
    "--delay",
    help="delay between each frame in milliseconds (default: 100)",
    type=int,
    default=100,
)
optional_args.add_argument(
    "-t",
    "--total-frames",
    help="total frames in spritesheet, set to 0 for autodetect",
    type=int
)
optional_args.add_argument(
    "-ac",
    "--autocrop",
    help="automatically crop the gif to the most inclusive size",
    action="store_true",
)
optional_args.add_argument(
    "-o",
    "--output",
    help="output directory",
    type=str,
    default=""
)
args = parser.parse_args()

spritesheet = Image.open(args.input)
# Removes the file extension
filename = Path(args.input).stem
image_x, image_y = spritesheet.size
# Set parameters
x_frames = args.x_frames
y_frames = args.y_frames
delay = args.delay
total_frames = args.total_frames
autocrop = args.autocrop
output_dir = args.output
if output_dir != "": output_dir += "/"
# Set frame sizes
frame_x = floor(image_x / x_frames)
frame_y = floor(image_y / y_frames)
# Set selection
topleft_x = 0
topleft_y = 0
bottomright_x = frame_x
bottomright_y = frame_y
# Frame list stuff
counter = 0
frame_list = []
frame_bbox = []

# Print without newline
print("Processing " + filename + "... ", end="")

# Fill the frame list
for i in range(y_frames):
    for j in range(x_frames):
        counter += 1
        # Cut frame from spritesheet
        sprite = spritesheet.crop((topleft_x, topleft_y, bottomright_x, bottomright_y))

        # Add sprite boundary box to list, returns None if the frame is empty
        frame_bbox.append(sprite.getbbox())

        # Process the frame and add it to the frame list
        frame_list.append(gen_frame(sprite))

        # Move the frame selection horizontally
        topleft_x += frame_x
        bottomright_x += frame_x
        # Exit if the total frames is reached
        if counter == total_frames:
            break
    # Move the frame selection vertically and reset horizontally
    topleft_x = 0
    topleft_y += frame_y
    bottomright_x = frame_x
    bottomright_y += frame_y
    # Exit if the total frames is reached
    if counter == total_frames:
        break

# Since counter is always >= 1, the break is skipped when total_frames is 0
if total_frames == 0:
    for i in range(len(frame_list)):
        # Pops frame_list if the last element is empty according to frame_bbox
        if frame_bbox[-(i + 1)] == None:
            frame_list.pop()
        # If the frame is not empty, exit the loop (To make sure only blank frames at the end are removed)
        else:
            break

# Automatically crops all frames to an inclusive size
if autocrop == True:
    # Removes empty frames from the list
    frame_bbox = [x for x in frame_bbox if x != None]
    # Sets the selection to the entire image
    crop_box = [frame_x, frame_y, 0, 0]
    # Adjusts the selection to the content in each frame
    for i in range(len(frame_bbox)):
        # Left and top, lower value is more inclusive
        crop_box[0] = min(crop_box[0], frame_bbox[i][0])
        crop_box[1] = min(crop_box[1], frame_bbox[i][1])
        # Right and bottom, higher value is more inclusive
        crop_box[2] = max(crop_box[2], frame_bbox[i][2])
        crop_box[3] = max(crop_box[3], frame_bbox[i][3])
    # Crops each frame according to the values in crop_box
    for i in range(len(frame_list)):
        frame_list[i] = frame_list[i].crop(tuple(crop_box))

# Create output directory
Path(output_dir).mkdir(parents=True, exist_ok=True)
# Compile the frame list into a gif
frame_list[0].save(
    # Set directory and append "_output.gif" to the resulting file
    output_dir + filename + "_output.gif",
    save_all=True,
    append_images=frame_list[1:],
    # Endless loop, dispose previous frame, set delay between frames
    loop=0,
    disposal=2,
    duration=delay,
    # This is important
    optimize=False,
)

print("Finished!")
