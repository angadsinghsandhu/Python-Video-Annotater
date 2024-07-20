
"""
controller.py

This module provides controls for the VideoPlayer, including play, pause,
seek, restart, and stop functionalities.
"""

# General imports
import cv2, logging
import customtkinter as ctk
from tkinter import DoubleVar

# Custom imports
from annotater.setup import align_window

# Set up logging
logger = logging.getLogger('app')

class ControlWindow(ctk.CTkToplevel):
    """
    ControlWindow class for providing video controls.

    Args:
        app (customtkinter.CTk): The main application window.
        file_name (str): Name of the video file being controlled.
        video_player (VideoPlayer): The VideoPlayer instance to control.
    """
    def __init__(self, app, file_name, video_player, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.video_player = video_player
        self.title(f"Video Controls: {file_name}")

        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(pady=10)
        
        self.play_pause_button = ctk.CTkButton(self.control_frame, text="▐▐", command=self.toggle_pause)
        self.play_pause_button.grid(row=0, column=0, padx=5)
        
        self.seek_var = DoubleVar()
        self.seeker = ctk.CTkSlider(self.control_frame, variable=self.seek_var, from_=0, to=int(self.video_player.cap.get(cv2.CAP_PROP_FRAME_COUNT)), width=500, command=self.seek)
        self.seeker.grid(row=0, column=1, padx=5, sticky="ew")

        self.restart_button = ctk.CTkButton(self.control_frame, text="⟳", command=self.restart)
        self.restart_button.grid(row=0, column=2, padx=5)

        self.stop_button = ctk.CTkButton(self.control_frame, text="⏹", command=lambda: self.close(save=True))
        self.stop_button.grid(row=0, column=3, padx=5)

        self.columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", lambda: self.close())

        # align the control window
        (self.mid_x, self.mid_y), (self.window_width, self.window_height), _ = align_window(self, 970, 50, horizontal="left", vertical="bottom")
        
        # Make the control window screen topmost
        self.attributes("-topmost", True)
        logger.info(f"Control window configuration completed for file: {file_name}")

    def add_to_queue(self, command):
        """
        Add a command to the video player's command queue.
        
        Args:
            command (tuple): The command to add to the queue
        """
        self.video_player.command_queue.put(command)
        logger.debug("Added command to queue: %s", command)

    def toggle_pause(self):
        """Toggle the pause state of the video."""
        self.play_pause_button.configure(text="▐▐" if self.video_player.paused else "▶")
        logger.info(f"Toggled pause state to {not self.video_player.paused}")
        self.add_to_queue('pause')

    def seek(self, value):
        """
        Seek to the specified frame number.
        
        Args:
            value (int): The frame number to seek to.
        """
        frame_number = int(value)
        self.add_to_queue(('seek', frame_number))
        self.seek_var.set(frame_number)
        logger.info(f"Seeked to frame number: {frame_number}")

    def restart(self):
        """Restart the video from the beginning."""
        self.add_to_queue('restart')
        self.play_pause_button.configure(text="▐▐")
        self.seek_var.set(0)
        logger.info("Restarted video")

    def close(self, save=False):
        """Save and close the video player."""
        self.video_player.close(save=save)
        self.video_player.done_event.set()
        logger.info("Saved and closed the video player")