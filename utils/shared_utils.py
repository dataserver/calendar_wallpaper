from utils.logger import setup_logger

logger = setup_logger(name="shared_utils_logger")


def hex_to_rgb(hex_code: str | tuple) -> tuple[int, int, int]:
    """
    Converts a hex color code (e.g., '#525252') to an RGB tuple.

    :param hex_code: The hex color code as a string
    :return: Tuple with RGB values
    """
    if isinstance(hex_code, tuple):
        return hex_code
    hex_code = hex_code.lstrip("#")
    rgb = tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))
    logger.debug(f"HEX: '{hex_code}' -> RGB {rgb}")
    return rgb
