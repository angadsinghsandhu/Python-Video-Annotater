"""
setup.py

This module contains the function to align the application window at the specified position and size 
based on the screen dimensions.
"""

# General Imports
import logging, sys, os

# Set up logging
logger = logging.getLogger('app')

# Constants
DEFAULT_OFFSET = -9
DEFAULT_TOP_BAR = 29
DEFAULT_WINDOW_WIDTH = 0.5
DEFAULT_WINDOW_HEIGHT = 0.5

def align_window(app, window_width: float = DEFAULT_WINDOW_WIDTH, window_height: float = DEFAULT_WINDOW_HEIGHT, 
                 horizontal: str = "center", vertical: str = "center", offset: int = DEFAULT_OFFSET, 
                 top_bar: int = DEFAULT_TOP_BAR) -> tuple:
    """
    Aligns the application window at the specified position and size based on the screen dimensions.

    Args:
        app (ctk.CTk): The application window.
        window_width (float): The desired width of the window as a fraction of the screen width. Defaults to 0.5.
        window_height (float): The desired height of the window as a fraction of the screen height. Defaults to 0.5.
        horizontal (str): The horizontal alignment of the window ("center", "left", "right"). Defaults to "center".
        vertical (str): The vertical alignment of the window ("center", "top", "bottom"). Defaults to "center".
        offset (int): The offset for positioning the window. Defaults to -9.
        top_bar (int): The height of the top bar for adjusting the vertical position. Defaults to 29.

    Returns:
        tuple: Coordinates (mid_x, mid_y) for the window, window dimensions (window_width, window_height), 
               and screen dimensions (screen_width, screen_height).
    """
    # Get screen dimensions
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()

    # Check if window width and height are valid
    if window_width == 0 or window_height == 0:
        logger.error("Window width and height cannot be 0, setting to default values")
        window_width, window_height = DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT

    # Calculate window width and height
    if window_width <= 1: window_width *= screen_width
    if window_height <= 1: window_height *= screen_height

    # Set window size
    app.geometry(f"{window_width}x{window_height}")

    # Wait for window to update
    while app.winfo_width() == 200 or app.winfo_height() == 200:
        app.update()
        app.after(100)

    # Get window dimensions
    window_width, window_height = app.winfo_width(), app.winfo_height()

    # Calculate window position
    position_right = (screen_width / 2) - (window_width / 2)
    position_top = (screen_height / 2) - (window_height / 2)

    # Adjust horizontal window position based on alignment
    if horizontal == "left": position_right = 0
    elif horizontal == "right": position_right = screen_width - window_width

    # Adjust vertical window position based on alignment
    if vertical == "top": position_top = 0
    elif vertical == "bottom": position_top = screen_height - window_height

    # calculate the mid point of the window
    mid_x, mid_y = int(position_right+offset), int(position_top-top_bar+offset)
    
    # Set window position and update
    app.geometry(f"+{mid_x}+{mid_y}")
    app.update()

    logger.info(f"'{app.title()}' App Dimentions ==> Screen (Width, Height) : ({screen_width}, {screen_height}) | Window (Width, Height) : ({window_width}, {window_height}) | position (right, top) : ({position_right}, {position_top})")

    return (mid_x, mid_y), (int(window_width), int(window_height)), (int(screen_width), int(screen_height))

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)