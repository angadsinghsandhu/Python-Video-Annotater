"""
main.py

Entry point for the video annotation tool. This script sets up the logging,
initializes the main application window, and starts the annotation tool.
"""

# General Imports
import logging, logging.config, yaml, ctypes
import customtkinter as ctk

# Custom Imports
from src.screens import Splash
from src.anno import create_annotater

# v1.2.0
# TODO: add controls for video playback

# v1.1.2
# TODO : update documentation

# Set DPI Awareness for Windows 10
ctypes.windll.shcore.SetProcessDpiAwareness(2)

# Set up logging
def setup_logging(config_path="logging_config.yaml"):
    """
    Sets up logging configuration from the provided YAML file.

    Args:
        config_path (str): Path to the logging configuration YAML file.

    Returns:
        (logging.Logger): Configured logger object
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config=config)
    logger = logging.getLogger('main')
    return logger, str(config.get("app-version"))

logger, version = setup_logging()

def close(app):
    """
    Closes the application and logs the closure.

    Args:
        app (customtkinter.CTk): The main application window.
    """
    logger.info("### Closing the Annotation Tool ###")
    app.destroy()

def main():
    """Main function to initialize and run the annotation tool application."""
    logger.info("### Starting the Annotation Tool ###")

    try:
        # Set the theme (optional)
        ctk.set_appearance_mode("Dark")  # Can be "Dark" or "Light"
        logger.debug("Appearance mode set to Dark")

        # Create the main application window
        app = ctk.CTk()
        app.title("Annotater") # Set the title of the window
        app.protocol("WM_DELETE_WINDOW", lambda: close(app))
        logger.debug("Main application window created and configured")

        # # add calback for mouse position
        # app.bind("<Motion>", lambda e: logger.debug(f"Mouse position: {e.x}, {e.y}"))

        # Hide the main application window initially
        app.withdraw()
        logger.debug("Main application window hidden")

        # Show splash screen
        Splash(app, version=version)
        logger.info("Splash screen displayed")

        create_annotater(app)
        logger.info("Annotater created and started")

    except Exception as e: logger.exception("An error occurred in the main loop: %s", e)
    finally: logger.info("Application terminated")

# run main loop
if __name__ == "__main__":
    main()
