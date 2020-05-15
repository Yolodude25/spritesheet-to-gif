from PIL import Image
from math import floor
from pathlib import Path
import sys


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


print("╔════════════════════╗")
print("║ Spritesheet to GIF ║")
print("╚════════════════════╝")

if len(sys.argv) < 5:
    # Don't add tabs here
    # re: yeah srry lmao
    input(
        """Format:
sprite2gif.py <input> <x frames> <y frames> <delay> [total frames] [autocrop] [output dir]
Delay is in milliseconds, autocrop is True or False
Default total frames is x frames * y frames, 0 total frames is autodetect
MUST set total frames if using autocrop, MUST set autocrop if using output dir"""
    )

if len(sys.argv) > 4:
    spritesheet = Image.open(sys.argv[1])
    # Removes the file extension
    filename = Path(sys.argv[1]).stem
    image_x, image_y = spritesheet.size
    # Set parameters
    x_frames = int(sys.argv[2])
    y_frames = int(sys.argv[3])
    delay = int(sys.argv[4])
    # Default to spritesheet dimensions if user did not give total_frames
    if len(sys.argv) > 5:
        total_frames = int(sys.argv[5])
    else:
        total_frames = None
    # Set autocrop if specified, MUST BE A STRING
    if len(sys.argv) > 6:
        autocrop = sys.argv[6].lower()
        if autocrop != "true" and autocrop != "false":
            raise Exception("Autocrop must be either True or False")
    else:
        autocrop = "false"
    # Set output directory if specified
    if len(sys.argv) > 7:
        output_dir = sys.argv[7] + "/"
    else:
        output_dir = ""
    # Set frame sizes
    frame_x = floor(image_x / x_frames)
    frame_y = floor(image_y / y_frames)
    # Set selection
    topleft_x = 0
    topleft_y = 0
    bottomright_x = frame_x
    bottomright_y = frame_y

    counter = 0
    frame_list = []
    frame_bbox = []
    # Fill the frame list
    for i in range(y_frames):
        for j in range(x_frames):
            counter += 1
            # Cut frame from spritesheet
            sprite = spritesheet.crop(
                (topleft_x, topleft_y, bottomright_x, bottomright_y)
            )

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
    if autocrop == "true":
        # Sets the selection to the entire image
        crop_box = [frame_x, frame_y, 0, 0]
        # Adjusts the selection to the content in each frame
        for i in range(len(frame_list)):
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
