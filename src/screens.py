"""
screens.py

This module contains the classes for the splash screen and save progress screen
used in the Annotater application.
"""

# General Imports
import logging
import os, customtkinter as ctk
from PIL import Image

# Custom Imports
from src.setup import align_window

# Set up logging
logger = logging.getLogger('app')

class Splash(ctk.CTkToplevel):
    """
    The Splash class creates a splash screen that displays a loading message and an image.

    Args:
        root (ctk.Ctk): The root window of the application.
        counter (int): The countdown timer before closing the splash screen.
    """
    def __init__(self, root, counter=4):
        super().__init__(root)
        
        self.root = root
        self.protocol("WM_DELETE_WINDOW", self.root.deiconify)
        logger.debug("Initializing Splash screen")

        # Set the size of the splash screen
        self.base_width, self.base_height = 350, 300
        
        self.create_splash()
        self.update_countdown(counter)

    def create_splash(self):
        """Creates and configures the splash screen layout."""
        self.title("Loading...")

        # Center the splash screen
        (mid_x, mid_y), (self.window_width, self.window_height), _ = align_window(self, self.base_width, self.base_height)

        self.resizable(False, False)

        # show application window
        self.deiconify()

        # Make the splash screen topmost
        self.attributes("-topmost", True)
        logger.debug(f"Splash screen centered at position: {mid_x}, {mid_y}")

        # Load and resize the image
        self.image_path = "./imgs/jhu.png"
        img = self.load_and_resize_image(self.image_path)

        # Create widgets
        self.image_label = ctk.CTkLabel(self, image=img, text="")
        self.label = ctk.CTkLabel(self, text="Welcome to the Annotater Application", font=("Arial", 16))
        self.countdown_label = ctk.CTkLabel(self, text="Closing in 3 seconds", font=("Courier", 12))

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)  # Make the column grow with the window
        self.grid_rowconfigure(0, weight=1)  # Image label row
        self.grid_rowconfigure(1, weight=0)  # Text label row
        self.grid_rowconfigure(2, weight=0)  # Countdown label row

        # Place widgets using grid
        self.image_label.grid(row=0, column=0, sticky="nsew", pady=20)
        self.label.grid(row=1, column=0, sticky="ew")
        self.countdown_label.grid(row=2, column=0, sticky="ew")

        logger.debug("Splash screen layout created with grid")

    def load_and_resize_image(self, image_path):
        """
        Loads and resizes an image to fit the application window.
        
        Args:
            image_path (str): Path to the image file.
        """
        if os.path.exists(image_path):
            img = Image.open(image_path)
            img_width, img_height = img.size
            logger.debug(f"Original Image Size: {img_width}x{img_height}")
            scaling_factor = min(self.base_width / img_width, self.base_height / img_height)
            new_width = int(img_width * scaling_factor)
            new_height = int(img_height * scaling_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized Image Size: {new_width}x{new_height}")
            return ctk.CTkImage(img, size=(new_width, new_height))
        else:
            logger.error(f"Splash image not found: {image_path}")
            return None

    def update_countdown(self, count):
        """
        Update the countdown timer on the splash screen.

        Args:
            count (int): Countdown timer in seconds.
        """
        if count > 0:
            self.countdown_label.configure(text=f"Closing in {count} seconds...")
            logger.debug(f"Countdown updated to {count} seconds")
            self.after(1000, self.update_countdown, count-1)
        else:
            self.destroy_splash()

    def destroy_splash(self):
        """Destroy the splash screen and show the main window."""
        self.destroy()
        self.root.deiconify()    # Show the main window
        logger.info("Countdown finished, destroying splash screen, showing main window")

class SaveProgress(ctk.CTkToplevel):
    """
    Save Progress Window for the Annotater application.

    Args:
        root (ctk.CTk): The root Tkinter application.
        name (str): The name of the file being saved.
    """
    def __init__(self, root, name):
        super().__init__(root)
        self.root = root
        self.name = name
        logger.debug(f"Initializing SaveProgress window for {name}")
        self.create_save_progress()
        self.protocol("WM_DELETE_WINDOW", self.destroy_save_progress)

    def create_save_progress(self):
        """Create and display the save progress window."""
        self.title(f"{self.name}: Saving Progress...")
        self.geometry("500x200")
        self.attributes("-topmost", True)

        # Layout Configuration
        for i in range(5): self.grid_rowconfigure(i, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=6)

        # Add a label to show the current status
        self.status_label = ctk.CTkLabel(self, text="Saving Annotation Files", font=("Courier", 16))
        self.status_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # video data progress bar
        self.video_progress_label = ctk.CTkLabel(self, text="Video Progress:")
        self.video_progress_label.grid(row=1, column=0, padx=10, pady=0, sticky="ew")
        self.video_progress = ctk.CTkProgressBar(self, mode='determinate', height=20, border_width=1, border_color="black", corner_radius=5, progress_color="green")
        self.video_progress.grid(row=1, column=1, padx=20, pady=0, sticky="ew")

        # audio data progress bar
        self.audio_progress_label = ctk.CTkLabel(self, text="Audio Progress:")
        self.audio_progress_label.grid(row=2, column=0, padx=10, pady=0, sticky="ew")
        self.audio_progress = ctk.CTkProgressBar(self, mode='determinate', height=20, border_width=1, border_color="black", corner_radius=5, progress_color="green")
        self.audio_progress.grid(row=2, column=1, padx=20, pady=0, sticky="ew")

        # audio-video data progress bar
        self.av_progress_label = ctk.CTkLabel(self, text="Audio-Video Progress:")
        self.av_progress_label.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        self.av_progress = ctk.CTkProgressBar(self, mode='determinate', height=20, border_width=1, border_color="black", corner_radius=5, progress_color="green")
        self.av_progress.grid(row=3, column=1, padx=20, pady=0, sticky="ew")

        # annotations json data progress bar
        self.json_progress_label = ctk.CTkLabel(self, text="Metadata Progress:")
        self.json_progress_label.grid(row=4, column=0, padx=10, pady=0, sticky="ew")
        self.json_progress = ctk.CTkProgressBar(self, mode='determinate', height=20, border_width=1, border_color="black", corner_radius=5, progress_color="green")
        self.json_progress.grid(row=4, column=1, padx=20, pady=0, sticky="ew")

        # reset progress bars
        self.reset()
        logger.debug("SaveProgress window layout created")

    def update_title_on_save(self):
        """Update the title of the save progress window when save is complete."""
        self.title(f"{self.name}: Progress Saved!!!")
        logger.info(f"Annotations saved for {self.name}")

    def update_video_progress(self, value):
        """
        Update the video progress bar.

        Args:
            value (float): Progress value between 0 and 1.
        """
        if value == 1.0: self.video_progress_label.configure(text="Video Progress: Done ✅")
        self.video_progress.set(value)

    def update_audio_progress(self, value):
        """
        Update the audio progress bar.

        Args:
            value (float): Progress value between 0 and 1.
        """
        if value == 1.0: self.audio_progress_label.configure(text="Audio Progress: Done ✅")
        self.audio_progress.set(value)

    def update_av_progress(self, value):
        """
        Update the audio-video progress bar.

        Args:
            value (float): Progress value between 0 and 1.
        """
        if value == 1.0: self.av_progress_label.configure(text="Audio-Video Progress: Done ✅")
        self.av_progress.set(value)

    def update_json_progress(self, value):
        """
        Update the metadata (JSON) progress bar.

        Args:
            value (float): Progress value between 0 and 1.
        """
        if value == 1.0: self.json_progress_label.configure(text="Metadata Progress: Done ✅")
        self.json_progress.set(value)

    def reset(self):
        """Reset all progress bars and the status label."""
        self.title(f"{self.name}: Saving Progress...")
        self.update_video_progress(0.0)
        self.update_audio_progress(0.0)
        self.update_av_progress(0.0)
        self.update_json_progress(0.0)
        self.status_label.configure(text="Status: Beginning Save Thread")
        logger.debug(f"Progress bars reset for {self.name}")

    def destroy_save_progress(self):
        """Destroy the save progress window and show the main window."""
        logger.info("Destroying SaveProgress window")
        self.destroy()
        self.root.deiconify()    # Show the main window
        logger.debug("Main window deiconified")

