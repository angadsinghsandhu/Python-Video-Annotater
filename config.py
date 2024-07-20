"""
config.py

This module manages the configuration settings for the video annotation tool application.
"""

# General Imports
import os, time, logging
from tkinter import messagebox
from customtkinter import filedialog
from pathlib import Path

# Set up logging
logger = logging.getLogger('app')

class Config:
    """
    The Config class manages the configuration settings for the video annotation tool application.

    Args:
        cwd (str): The current working directory.
        in_path (str): The input video directory.
        out_path (str): The output video directory.
        files (list): The list of video files in the input directory.
        extension (str): The file extension for the video files
    """
    def __init__(self, cwd=None, in_path=None, out_path=None, files=[], extension=".mp4"):
        self._cwd = cwd
        self._in_path = in_path
        self._out_path = out_path
        self._files = files
        self._last_update = time.time()
        self.extension = extension
        logger.info(f"Config initialized with cwd={self._cwd}, in_path={self._in_path}, out_path={self._out_path}")

    # Getters and Setters

    @property
    def cwd(self) -> str:
        return self._cwd

    @cwd.setter
    def cwd(self, value: str):
        logger.debug(f"Setting Current Working Directory: {value}")
        self._cwd = self.convert_to_unix_style(value)

    @property
    def in_path(self) -> str:
        return self._in_path

    @in_path.setter
    def in_path(self, value: str):
        logger.debug(f"Setting input folder path to: {value}")
        self._in_path = self.convert_to_unix_style(value)

    @property
    def out_path(self) -> str:
        return self._out_path

    @out_path.setter
    def out_path(self, value: str):
        logger.debug(f"Setting output folder path to: {value}")
        self._out_path = self.convert_to_unix_style(value)

    @property
    def files(self) -> list:
        return self._files

    @files.setter
    def files(self, value: list):
        logger.debug(f"Setting Files: {value}")
        self._files = value

    @property
    def last_update(self) -> float:
        return self._last_update

    @last_update.setter
    def last_update(self, value: float):
        logger.debug(f"Setting last_update: {time.time()}")
        self._last_update = time.time()

    # METHODS TO GET DATA
    
    def __str__(self):
        """Returns a string representation of the Config object."""
        return f"Config: cwd={self.cwd}, in_path={self.in_path}, out_path={self.out_path}, files={self.files}, last_update={self.last_update}"
    
    def __repr__(self):
        """Returns a string representation of the Config object for debugging."""
        return self.__str__()
    
    @property
    def fetch_top_file(self):
        """Fetches the top file from the file list."""
        return self.files[0] if self.files else None

    # METHODS TO UPDATE

    def update(self, in_path=None, out_path=None, files=[]):
        """
        Updates the configuration paths and file list.
        
        Args:
            in_path (str): Input directory path.
            out_path (str): Output directory path.
            files (list): List of files.
        """
        self._cwd = self.convert_to_unix_style(os.getcwd())
        self._in_path = self.convert_to_unix_style(in_path)
        self._out_path = self.convert_to_unix_style(out_path)
        self._files = files
        self._last_update = time.time()
        logger.info(f"Config updated with in_path={self.in_path}, out_path={self.out_path}")

    def change_directory(self):
        """Choose the current working directory and change to it."""
        logger.info("Starting directory change")

        try:
            new_dir = ""
            while not new_dir: new_dir = filedialog.askdirectory(title="Select New Directory")
            if new_dir:
                os.chdir(new_dir)
                logger.info(f"Current working directory changed to: {new_dir}")
                self.cwd = new_dir      # Update the config
                in_path, out_path, files = self.file_setup()
                return in_path, out_path, files, new_dir
            else:
                logger.warning("No directory selected for change")
        except Exception as e:
            logger.error(f"An error occurred during directory change: {e}", exc_info=True)

    def file_setup(self):
        """Sets up input and output directories and fetches files."""
        logger.info("Starting file setup")

        try:
            if not self.cwd: self.cwd = filedialog.askdirectory(title="Select Root Directory", initialdir=self.convert_to_unix_style(os.path.join(os.path.expanduser('~'), 'Videos')))
            logger.debug(f"Current working directory: {self.cwd}")
            
            # Select Input Video Directory
            if not os.path.exists(f"{self.cwd}/data"):
                self.in_path = "."
                while len(self.in_path) == 1: self.in_path = filedialog.askdirectory(title="Select Input Directory", initialdir=self.cwd)
                logger.info(f"Input directory selected: {self.in_path}")
            else: 
                self.in_path = f"{self.cwd}/data"
                logger.debug(f"Default input directory used: {self.in_path}")

            # Select Output Directory
            if not os.path.exists(f"{self.cwd}/out"): 
                self.out_path = "."
                while len(self.out_path) == 1: self.out_path = filedialog.askdirectory(title="Select Output Directory", initialdir=self.cwd)
                logger.info(f"Output directory selected: {self.out_path}")
            else: 
                self.out_path = f"{self.cwd}/out"
                logger.debug(f"Default output directory used: {self.out_path}")

            # get list of names all mp4 files in self.file_path
            in_files = [f for f in os.listdir(self.in_path) if f.endswith(".mp4")]
            logger.info(f"Found {len(in_files)} MP4 files in the input directory")

            if not in_files:
                logger.warning("No MP4 files found in the input directory")
                messagebox.showerror("Error", "No MP4 files found in the input directory.")
            
            _ = config.refetch_files()

            return self.in_path, self.out_path, self.files
        except Exception as e:
            logger.error(f"An error occurred during file setup: {e}", exc_info=True)

    # METHODS TO EQUATE
    
    def __eq__(self, other):
        """Checks if two Config objects are equal."""
        if not isinstance(other, Config):
            return NotImplemented
        return (self.cwd == other.cwd and self.in_path == other.in_path and 
                self.out_path == other.out_path and self.files == other.files and 
                self.last_update == other.last_update)

    # HELPER FUBNCTIONS
    
    def remove_extension(self, file_name, extensions=[".mp4"]):
        """
        Removes the extension from a file name.
        
        Args:
            file_name (str): Name of the file.
            extensions (list): List of extensions to remove.
        
        Returns:
            (str): File name without extension.
        """
        for ext in extensions:
            if file_name.endswith(ext):
                return file_name[:-len(ext)]
        logger.debug(f"No extension removed from file '{file_name}'")
        return file_name
    
    def refetch_files(self, inp=None, out=None, extensions=[".mp4"]):
        """
        Refetches the list of files from the input and output directories.
        
        Args:
            inp (str): Input directory path.
            out (str): Output directory path.
            extensions (list): List of file extensions.
        
        Returns:
            (list): List of files to be processed.
        """
        try:
            # Check if input and output directories exist
            if inp is not None: 
                if not os.path.exists(inp): 
                    logger.error(f"Input directory '{inp}' does not exist")
                    return []
                else: self.in_path = inp

            # Check if output directory exists
            if out is not None:
                if not os.path.exists(out): 
                    logger.error(f"Output directory '{out}' does not exist")
                    return []
                else: self.out_path = out

            logger.debug(f"Removing extensions from files and filtering")
            in_files = [self.remove_extension(f, extensions) for f in os.listdir(self.in_path) if f.endswith(tuple(extensions))]
            out_files = [self.remove_extension(f, extensions) for f in os.listdir(self.out_path) if f.endswith(tuple(extensions))]
            
            files = [f"{f}{self.extension}" for f in in_files if f"{f}_annotated" not in out_files]

            self.update(self.in_path, self.out_path, files)
            logger.info(f"Refetched files: {files}")
            return files
        except Exception as e:
            logger.error(f"Error refetching files: {e}")
            raise e

    def convert_to_unix_style(self, path):
        """
        Converts a file path to Unix style.
        
        Args:
            path (str): File path.
        
        Returns:
            (str): Unix style file path.
        """
        return Path(path).as_posix()

    # METHODS TO SAVE

    def save_config(self, file_path):
        """
        Saves the configuration settings to a file.
        
        Args:
            file_path (str): Path to the configuration file.
        """
        try:
            with open(file_path, "w") as f:
                f.write(f"CWD: {self.cwd}\n")
                f.write(f"IN_PATH: {self.in_path}\n")
                f.write(f"OUT_PATH: {self.out_path}\n")
                f.write(f"FILES: {self.files}\n")
                f.write(f"LAST_UPDATE: {self.last_update}\n")
            logger.info(f"Configuration saved to file: {file_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to file: {e}")

# Create a global Config object
config = Config()
