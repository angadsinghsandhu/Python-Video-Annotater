"""
anno.py

This module contains functions for managing directory changes, refreshing file lists, 
annotating videos, and watching annotated videos in the video annotation tool application.
"""

# General Imports
import threading
import logging
import customtkinter as ctk
import os
from tkinter import filedialog

# Local Imports
from src.setup import align_window, resource_path
from src.player import VideoPlayer, AnnotatedPlayer
from src.config import config

# Set up logging
logger = logging.getLogger('app')

def change(app, labels):
    """
    Changes the working directory and updates labels with new paths.

    Args:
        app (ctk.CTk): The main application window.
        labels (dict): Dictionary containing label widgets.
    """
    try:
        config.change_directory()
        labels['in_path'].configure(text=f"Input Dir: {config.in_path}")
        labels['file'].configure(text=f"Current File to be Annotated: {config.fetch_top_file}")
        labels['out_path'].configure(text=f"Output Dir: {config.out_path}")
        logger.info("Directory changed successfully")
    except Exception as e:
        logger.exception(f"Error changing directory: {e}")

def refresh(labels):
    """
    Refreshes the list of files and updates the corresponding label.

    Args:
        labels (dict): Dictionary containing label widgets.
    """
    try:
        _ = config.refetch_files()
        labels['file'].configure(text=f"Current File to be Annotated: {config.fetch_top_file}")
        logger.info("File list refreshed successfully")
    except Exception as e:
        logger.exception(f"Error refreshing file list: {e}")

def update_annotation_text(var, checkbox):
    """
    Updates the annotation mode text based on the checkbox selection.

    Args:
        var (ctk.BooleanVar): The variable linked to the checkbox.
        checkbox (ctk.CTkCheckBox): The checkbox to update based on the checkbox value.
    """
    if var.get(): # if checkbox is checked text is long annotations
        checkbox.configure(text="Mode: Long Annotations")
    else: # if checkbox is unchecked text is short annotations
        checkbox.configure(text="Mode: Short Annotations")

def update_annotation_label(var, label):
    """
    Updates the annotation mode label based on the checkbox selection.

    Args:
        var (ctk.BooleanVar): The variable linked to the checkbox.
        label (ctk.CTkLabel): The label to update based on the checkbox value.
    """
    if var.get():
        label.configure(text="Mode: Long Annotations")
    else:
        label.configure(text="Mode: Short Annotations")

def annotate(app, labels, long_annotations=False):
    """
    Starts the annotation process for the top file in the list.

    Args:
        app (ctk.CTk): The main application window.
        labels (dict): Dictionary containing label widgets.
        long_annotations (ctk.BooleanVar): The variable linked to the annotation mode checkbox.
    """
    file_name = config.fetch_top_file
    if not file_name:
        labels['file'].configure(text="All files have been annotated.")
        logger.debug("All files have been annotated.")
    else:
        logger.info(f"Starting annotation for file: {file_name}, with long annotations: {long_annotations}")
        done_event = threading.Event()

        try:
            player = VideoPlayer(app, file_name, done_event=done_event, long_annotations=long_annotations)
            done_event.wait()
            _ = config.refetch_files()
            labels['file'].configure(text=f"Current File to be Annotated: {config.fetch_top_file}")
            logger.info(f"Annotation completed for file: {file_name}")
        except Exception as e:
            logger.exception(f"Error during annotation for file: {file_name}: {e}")

def watch(long_annotations=False):
    """Starts the video player to watch the annotated video."""
    try:
        # get which file to watch
        watch_file = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")], title="Select a file to watch", initialdir=config.out_path)
        if watch_file:
            meta_file = watch_file.replace("_annotated.mp4", "_annotated.json")
            logger.info(f"Started watching file: {watch_file}")
            AnnotatedPlayer(watch_file, meta_file, long_annotations=long_annotations)
        else:
            logger.warning("No file selected for watching")
    except Exception as e:
        logger.exception(f"Error during watching: {e}")

# Functions
def create_annotater(app):
    """
    Sets up the annotation tool user interface and starts the main application loop.

    Args:
        app (ctk.CTk): The main application window.
    """
    logger.info("Creating annotater")
    try:
        # check if file exists
        if os.path.exists("./imgs/tool.ico"):
            app.iconbitmap("./imgs/tool.ico")
            logger.debug("Icon set from local file")
        elif os.path.exists(resource_path("./imgs/tool.ico")):
            app.iconbitmap(resource_path("./imgs/tool.ico"))
            logger.debug("Icon set from resource path")
        elif os.path.exists(os.path.join(os.path.expanduser('~'), 'Dektop', 'App', 'imgs', 'tool.ico')):
            app.iconbitmap(os.path.join(os.path.expanduser('~'), 'Dektop', 'App', 'imgs', 'tool.ico'))
            logger.debug("Icon set from desktop path")

        # add default styling options
        ctk.set_default_color_theme("dark-blue")  # Set the default color theme
        app.option_add("*Font", "Courier 12")  # Set the default font and size
        logger.debug("Default styling options set")

        # Set geometry 
        _, _, _= align_window(app, 700, 250)
        app.minsize(700, 250)
        app.resizable(True, False)

        # Setup Files
        config.file_setup()
        logger.info("File setup completed")

        # Layout Configuration
        app.grid_rowconfigure(0, weight=1)
        app.grid_rowconfigure(4, weight=1)  # Add weight to the checkbox row
        app.grid_columnconfigure(0, weight=1)
        app.grid_columnconfigure(1, weight=1)
        app.grid_columnconfigure(2, weight=1)
        app.grid_columnconfigure(3, weight=1)
        app.grid_columnconfigure(4, weight=1)
        app.grid_columnconfigure(5, weight=1)

        # dict to store labels to send as arguements
        labels = {}
        
        # Add a label to the window
        change_dir_button = ctk.CTkButton(app, text="Change Directory", command=lambda: change(app, labels))
        change_dir_button.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # Button to refresh files
        refresh_button = ctk.CTkButton(app, text="Refresh Files", command=lambda: refresh(labels))
        refresh_button.grid(row=0, column=3, columnspan=3, padx=10, pady=5, sticky="ew")

        # Add a label current input path
        current_in_path_label = ctk.CTkLabel(app, text=f"Input Dir: {config.in_path}")
        current_in_path_label.grid(row=1, column=0, columnspan=6, padx=10, pady=5, sticky="ew")
        labels["in_path"] = current_in_path_label

        # Add label for the current file name
        current_file_label = ctk.CTkLabel(app, text=f"Current File to be Annotated: {config.fetch_top_file}")
        current_file_label.grid(row=2, column=0, columnspan=6, padx=10, pady=5, sticky="ew")
        labels["file"] = current_file_label

        # Add a label current output path
        current_out_path_label = ctk.CTkLabel(app, text=f"Output Dir: {config.out_path}")
        current_out_path_label.grid(row=3, column=0, columnspan=6, padx=10, pady=5, sticky="ew")
        labels["out_path"] = current_out_path_label

        # Create a BooleanVar for the checkbox
        long_annotations_var = ctk.BooleanVar(value=False)

        # Add a checkbox for selecting annotation mode
        annotation_checkbox = ctk.CTkCheckBox(app, text="Mode: Short Annotations", variable=long_annotations_var,
                                              command=lambda: update_annotation_text(long_annotations_var, annotation_checkbox))
        # annotation_checkbox.grid(row=4, column=0, columnspan=4, padx=10, pady=5, sticky="ew")
        annotation_checkbox.grid(row=4, column=0, columnspan=6)

        # Open Video Player Button
        video_button = ctk.CTkButton(app, text="Begin Annotating", command=lambda: annotate(app, labels, long_annotations_var.get()))
        video_button.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

        watch_button = ctk.CTkButton(app, text="Watch Annotated Video", command=lambda: watch(long_annotations_var.get()))
        watch_button.grid(row=5, column=3, columnspan=3, padx=10, pady=10, sticky="ew")

        logger.info("Annotater UI setup completed")

        # Start the main application loop
        app.mainloop()
        logger.info("Main application loop started")
    except Exception as e:
        logger.exception(f"An error occurred during annotater creation: {e}")