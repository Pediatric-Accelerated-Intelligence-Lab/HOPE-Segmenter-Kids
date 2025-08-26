import base64

def image_to_base64(image_path:str)-> str:
    """Convert a image to the base64 encoding for display of banner.

    Args:
        image_path (str): path to image.

    Returns:
        str: base64 encoded image
    """

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    return 'data:image/jpeg;base64,'+encoded_string