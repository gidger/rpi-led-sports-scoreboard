import os
from PIL import Image
from pathlib import Path


def crop_image(image):
    """ Crops all transparent space around an image.

    Args:
        image (image): Image to have transparent space cropped.

    Returns:
        image: Cropped image.
    """

    # Get the bounding box of the image. Aka, boundaries of what's non-transparent. Crop the image to the contents of the bounding box.
    bbox = image.getbbox()
    image = image.crop(bbox)
    
    # Create a new image object for the output image. Paste the cropped image onto the new image.
    cropped_image = Image.new('RGB', image.size) # Note that since we define this as RGB, there will be no transparency in the resulting image.
    cropped_image.paste(image)

    return cropped_image

def clear_image(image, image_draw):
    """ Draws a black rectangle over a specific image. Effectively, "clearing" it to default state.

    Args:
        image (Image): PIL Image to clear.
        image_draw (ImageDraw): PIL ImageDraw object associated with the image.
    """

    # TODO: Comment this.
    if isinstance(image, list):
        for im, drw in zip(image, image_draw):
            drw.rectangle([(0,0), im.size], fill=(0,0,0))
    else:
        image_draw.rectangle([(0,0), image.size], fill=(0,0,0))

# Resets image to RGB space to ensure alpha channel shows black
def process_in_place(file_path, target_size=(500, 500)):
    # Define a temporary filename in the SAME folder
    temp_path = Path(file_path).with_suffix(".tmp")
    
    try:
        # Open and process
        with Image.open(file_path) as img:
            img = img.convert("RGBA")
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            background = Image.new("RGB", target_size, (0, 0, 0))
            background.paste(img, mask=img.split()[3])
            
            # Save to the .tmp file
            background.save(temp_path, "PNG")
        
        # replace original with the new version
        os.replace(temp_path, file_path)
        
    except Exception as e:
        print(f"Error: {e}")
        # Clean up the temp file if something went wrong
        if temp_path.exists():
            temp_path.unlink()
