"""
data.py

This module defines the Data class used for storing and processing video, audio data, and annotations.
"""

# General Imports
import subprocess, cv2, json, os, logging
import numpy as np
from typing import List, Tuple, Dict, Union
from functools import lru_cache, cached_property
from customtkinter import filedialog
from tkinter import messagebox
from scipy.io.wavfile import write

# Custom Imports
from screens import SaveProgress

# Set up logging
logger = logging.getLogger('app')

class Data:
    """
    Class to store video and audio data, and annotations.

    Args:
        in_path (str): Path to the input video file.
        out_path (str): Path to save the processed video and audio files.
        name (str): Name of the video file.
        frame_rate (float): Frames per second of the video.
        frame_count (int): Total number of frames in the video.
        frame_width (int): Width of each frame in pixels.
        frame_height (int): Height of each frame in pixels.
        sample_rate (int): Audio sample rate.
        channels (int): Number of audio channels.
    """
    def __init__(self, in_path, out_path, name, frame_width, frame_height, fps=30, fc=10225, sample_rate=44100, channels=2):
        self.in_path = in_path      # Path to the video file selected
        self.out_path = out_path    # Path where the video file will be saved
        self.name = name            # Default name of the file (same name as selected file)

        # Full path to the selected video file
        self.in_file_path = os.path.join(in_path, name)
        self.out_file_path = os.path.join(out_path, name)
        # self.out_file_path = os.path.join(out_path, name.replace(".mp4", "_annotated.mp4"))

        # Video properties
        self.frame_rate = fps               # Frames per second of the selected video
        self.frame_count = fc               # Frame count of the selected video
        self.frame_width = frame_width      # Width of the frame
        self.frame_height = frame_height    # Height of the frame

        # Data storage
        self.frames: List[Tuple[float, int]] = []                               # List of (timestamp, frame) tuples
        self.audio_data: List[Tuple[float, np.ndarray]] = []                    # List of (timestamp, audio_chunk) tuples
        self.annotations: Dict[int, List[Union[str, Tuple[int, int]]]] = {}     # Dictionary of annotations with frame index as key

        # Frame and audio data
        self.curr_frame = 0     # Current frame index
        self.max_frames = fc    # Maximum frame index

        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_name = self.name.replace(".mp4", ".wav")
        self.audio_path = os.path.join(self.out_path, self.audio_name)

        # Log data object initialization
        self.print_data_object_info(log=True)
        logger.info(f"Data object for {name} initialized")

    # METHODS TO PRINT DATA

    def print_data_object_info(self, log=False):
        table_data = [
            ["Description", "Value"],
            ["Data Object Created for", self.name],
            ["Input Path", self.in_path],
            ["Output Path", self.out_path],
            ["Name", self.name],
            ["FPS", self.frame_rate],
            ["Frame Count", self.frame_count],
            ["Frame Width", self.frame_width],
            ["Frame Height", self.frame_height],
            ["Sample Rate", self.sample_rate],
            ["Channels", self.channels]
        ]
        
        if log:
            _str = "| "
            for row in range(1, len(table_data)): _str +=  str(table_data[row][0]) + " ==> " + str(table_data[row][1]) + " | "
            logger.debug(_str.rstrip())
        else:
            column_width = max(len(str(item)) for row in table_data for item in row) + 2
            separator = "+" + "-" * (column_width * 2 + 1) + "+"

            print(separator)
            for row in table_data:
                print("|" + "|".join(str(item).center(column_width) for item in row) + "|")
                print(separator)

    # METHODS TO GET DATA

    @lru_cache(maxsize=128)
    def get_audio_data(self, index: int) -> Tuple[float, np.ndarray]:
        """
        Returns the audio data at the specified index.
        
        Args:
            index (int): Index of the audio data.

        Returns:
            (Tuple[float, np.ndarray]): Timestamp and audio data at the specified index.
        """
        return self.audio_data[index]
    
    @lru_cache(maxsize=128)
    def get_audio_data(self, index):
        """
        Returns the audio data at the specified index.

        Args:
            index (int): Index of the audio data.

        Returns:
            (Tuple[float, np.ndarray]): Timestamp and audio data at the specified index.
        """
        return self.audio_data[index]
    
    def get_annotation(self, frame_idx: int) -> Union[None, List[Union[str, Tuple[int, int]]]]:
        """
        Returns the annotation for the specified frame index.
        
        Args:
            frame_idx (int): Frame index to get the annotation for.
            
        Returns:
            (Union[None, List[Union[str, Tuple[int, int]]]]): Annotation data for the specified frame index.
        """
        return self.annotations.get(frame_idx)
    
    @cached_property
    def get_curr_frame(self) -> int:
        """
        Returns the current frame index.

        Returns:
            (int): Current frame index
        """
        return self.curr_frame
    
    def get_last_annotation(self) -> Union[None, List[Union[str, Tuple[int, int]]]]:
        """
        Returns the last annotation if available.

        Returns:
            (Union[None, List[Union[str, Tuple[int, int]]]]): Last annotation data if available.
        """
        if self.get_frames_length == 0 or self.get_annotations_length == 0:
            return None
        return self.get_annotation(max(self.annotations.keys()))
    
    @property
    def get_max_frames(self) -> int:
        """
        Returns the maximum number of frames.

        Returns:
            (int): Maximum number of frames.
        """
        return self.max_frames
    
    # MOTHODS TO GET DATA LENGTH

    @property
    def get_frames_length(self) -> int:
        """
        Returns the number of frames stored.

        Returns:
            (int): Number of frames stored.
        """
        return len(self.frames)

    @property
    def get_audio_data_length(self) -> int:
        """
        Returns the length of audio data stored.

        Returns:
            (int): Length of audio data stored.
        """
        return len(self.audio_data)

    @property
    def get_annotations_length(self) -> int:
        """
        Returns the number of annotations stored.
        
        Returns:
            (int): Number of annotations stored.
        """
        return len(self.annotations)

    # METHODS TO ADD DATA

    def add_curr_frame(self, timestamp: float, frame: int) -> None:
        """
        Adds the current frame to the frames list.

        Args:
            timestamp (float): Timestamp of the frame.
            frame (int): Frame index
        """
        if frame >= self.frame_count:
            logger.warning(f"Frame index {frame} is out of range.")
        self.frames.append((timestamp, frame))

    def add_audio_data(self, timestamp: float, audio: np.ndarray) -> None:
        """
        Adds audio data to the audio data list.
        
        Args:
            timestamp (float): Timestamp of the audio data.
            audio (np.ndarray): Audio data.
        """
        self.audio_data.append((timestamp, audio))

    def add_annotation(self, command: str, annotation: Tuple[int, int]) -> None:
        """
        Adds annotations with timestamp.

        Args:
            command (str): Command for the annotation (start, move, end).
            annotation (Tuple[int, int]): The annotation data.
        """
        if self.get_frames_length == 0:
            logger.error("No frames to annotate.")
            return

        frame_idx = self.get_frames_length - 1
        if frame_idx in self.annotations and self.annotations[frame_idx][0] == "start":
            self.annotations[frame_idx] = ["start", list(annotation)]
        else:
            self.annotations[frame_idx] = [command, list(annotation)]

        logger.debug(f"Added annotation at frame {frame_idx} with command {command}")

    # METHODS TO UPDATE DATA

    def update(self, in_path: str, out_path: str, name: str, frame_width: int, frame_height: int,
               fps: float, fc: int, sample_rate: int, channels: int) -> None:
        """
        Updates the data attributes with new values.

        Args:
            in_path (str): Path to the input video file.
            out_path (str): Path to save the processed video and audio files.
            name (str): Name of the video file.
            frame_width (int): Width of each frame in pixels.
            frame_height (int): Height of each frame in pixels.
            fps (float): Frames per second of the video.
            fc (int): Total number of frames in the video.
            sample_rate (int): Audio sample rate.
            channels (int): Number of audio channels.
        """
        self.in_path = in_path
        self.out_path = out_path
        self.name = name

        self.in_file_path = os.path.join(in_path, name)
        self.out_file_path = os.path.join(out_path, name)

        self.frame_rate = fps
        self.frame_count = fc
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.sample_rate = sample_rate
        self.channels = channels

        logger.info(f"Data() updated for {name}: in_path={in_path}, out_path={out_path}, "
                    f"frame_width={frame_width}, frame_height={frame_height}")

    def update_curr_frame(self, frame: int) -> None:
        """
        Updates the current frame index.

        Args:
            frame (int): Frame index to update to.
        """
        self.curr_frame = frame

    def update_max_frames(self, frame: int) -> None:
        """
        Updates the maximum number of frames.

        Args:
            frame (int): Maximum number of frames.
        """
        self.max_frames = frame

    def increment_max_frame(self) -> None:
        """Increments the maximum frame count by one."""
        self.max_frames += 1

    # METHODS TO COMBINE DATA

    def identify_video_gaps(self, threshold: float = 0.1) -> List[Tuple[float, float]]:
        """
        Identifies gaps in video frames where the time difference exceeds the threshold.

        Args:
            threshold (float): Time threshold to identify gaps.

        Returns:
            (List[Tuple[float, float]]): List of video gaps identified.
        """
        video_gaps = []
        for i in range(1, len(self.frames)):
            previous_time, _ = self.frames[i - 1]
            current_time, _ = self.frames[i]
            if current_time - previous_time > threshold:
                video_gaps.append((previous_time, current_time))
        return video_gaps

    def combined_audio(self) -> np.ndarray:
        """
        Combines all audio data into a single array, removing audio during video gaps.

        Returns:
            (np.ndarray): Combined audio data.
        """
        video_gaps = self.identify_video_gaps()

        synced_audio = []
        current_audio_index = 0

        for gap_start, gap_end in video_gaps:
            # Add audio before the gap
            while current_audio_index < len(self.audio_data) and self.audio_data[current_audio_index][0] < gap_start:
                synced_audio.append(self.audio_data[current_audio_index][1])
                current_audio_index += 1

            # Skip audio during the gap
            while current_audio_index < len(self.audio_data) and self.audio_data[current_audio_index][0] < gap_end:
                current_audio_index += 1

        # Add remaining audio after the last gap
        while current_audio_index < len(self.audio_data):
            synced_audio.append(self.audio_data[current_audio_index][1])
            current_audio_index += 1

        if synced_audio:
            combined_audio = np.concatenate(synced_audio, axis=0)
            logger.debug("Combined audio data successfully")
            return combined_audio

        logger.error("Synced audio is empty or invalid.")
        return np.array([])

    # METHODS TO SAVE DATA

    def process_video_data(self, progress: SaveProgress = None) -> None:
        """
        Process video data and save it to the output file.

        Args:
            progress (SaveProgress): Progress window to update the progress.
        """
        if not self.frames:
            messagebox.showerror("Error", "No frames to save.")
            logger.error("No frames to save")
            return

        # open the video file
        cap = cv2.VideoCapture(self.in_file_path)

        # check if the video file is opened
        if not cap.isOpened():
            messagebox.showerror("Error", "Failed to open video file.")
            logger.error("Failed to open video file")
            return
        
        # read the video file frame by frame
        vid = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            vid.append(frame)

        # Get original video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Assert that the original properties match the given values
        assert original_fps == self.frame_rate, f"FPS mismatch: {original_fps} != {self.frame_rate}"
        assert original_width == self.frame_width, f"Frame width mismatch: {original_width} != {self.frame_width}"
        assert original_height == self.frame_height, f"Frame height mismatch: {original_height} != {self.frame_height}"
        assert len(vid) == self.frame_count, "Frame count mismatch"

        cap.release()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.out_file_path, fourcc, self.frame_rate, (self.frame_width, self.frame_height))

        # Write frames to the output video in the specified order
        last_index = len(self.frames) - 1
        for timestamp, index in self.frames:
            if index < len(vid):
                out.write(vid[index])
                if progress: progress.update_video_progress(index / last_index)
            else:
                logger.warning(f"Frame index {index} is out of range.")

        logger.info(f"Video data processed and saved to {self.out_file_path}")

    def process_audio_data(self, progress: SaveProgress = None) -> None:
        """
        Processes and saves audio data to a file.
        
        Args:
            progress (SaveProgress): Progress window to update the progress.
        """
        # Check if audio data and annotations are present
        if len(self.audio_data) > 0:
            write(self.audio_path, self.sample_rate, self.combined_audio())
            logger.info(f"Audio data saved to {self.audio_path}")
            if progress: progress.update_audio_progress(1.0)
        else: logger.warning("No audio data to save")

    def save_av_and_clean(self, progress: SaveProgress = None) -> None:
        """
        Merges audio and video data using FFmpeg and cleans up temporary files.
        
        Args:
            progress (SaveProgress): Progress window to update the progress.
        """
        subprocess.run([
            'ffmpeg',
            '-hide_banner',
            '-y',
            '-i', self.out_file_path,
            '-i', self.audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            self.out_file_path.replace('.mp4', '_annotated.mp4')
        ])

        if progress: 
            progress.update_video_progress(1.0)
            progress.update_av_progress(1.0)
        logger.info(f"Audio and video merged and saved to {self.out_file_path.replace('.mp4', '_annotated.mp4')}")

        # delete the audio and video data at self.out_file_path and self.audio_path
        if os.path.exists(self.out_file_path):
            os.remove(self.out_file_path)
            logger.debug(f"Deleted temporary video file {self.out_file_path}")
        if os.path.exists(self.audio_path):
            os.remove(self.audio_path) 
            logger.debug(f"Deleted temporary audio file {self.audio_path}")

    def save_annotations(self, progress: SaveProgress = None) -> None:
        """
        Saves annotations to a JSON file.
        
        Args:
            progress (SaveProgress): Progress window to update the progress.
        """
        self.annotations["metadata"] = {
            "video_name": self.name,
            "frame_rate": self.frame_rate,
            "frame_count": self.max_frames,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "sample_rate": self.sample_rate,
            "channels": self.channels
        }

        # Save annotations to a JSON file
        try:
            with open(self.out_file_path.replace('.mp4', '_annotated.json'), "w") as file:
                json.dump(self.annotations, file)

            if progress: progress.update_json_progress(1.0)
            logger.info(f"Annotations saved to {self.out_file_path.replace('.mp4', '_annotated.json')}")
        except Exception as e: logger.error(f"Error saving annotations: {e}")

    def save_data(self, app) -> None:
        """
        Saves video, audio, and annotations data, and merges them using FFmpeg.
        
        Args:
            app (customtkinter.CTk): The main application window.
        """
        if not self.out_path:
            self.out_path = filedialog.askdirectory(filetypes=[("MP4 files", "*.mp4")])

        logger.info(f"Saving data for {self.name} to {self.out_path}")

        # Create progress window
        progress = SaveProgress(app, self.name)
        progress.update()

        self.process_video_data(progress=progress)      # Save video data
        self.process_audio_data(progress=progress)      # Save audio data
        self.save_av_and_clean(progress=progress)       # Merge audio and video data
        self.save_annotations(progress=progress)        # Save annotations

        # update progress window title
        progress.update_title_on_save()
        logger.info(f"Data for {self.name} saved successfully")

    # METHODS TO DELETE DATA

    def clean(self) -> None:
        """Function to clean the data object"""
        self.frames = []
        self.audio_data = []
        self.annotations = {}
        self.curr_frame = 0
        self.max_frame = 0
        logger.debug("Data object cleaned")