"""
player.py

This module handles video playback, annotation, and audio synchronization
for both annotating and watching annotated videos.
"""

# General Imports
import cv2
import os
import threading
import queue
import json
import logging
import datetime
import sounddevice as sd
import time as t
from tqdm import tqdm
from tkinter import messagebox
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Hide pygame support prompt
from pygame import mixer
from moviepy.editor import VideoFileClip

# Local Imports
from src.data import Data
from src.config import config
from src.controller import ControlWindow

# Set up logging
logger = logging.getLogger('app')

class VideoPlayer:
    """
    VideoPlayer class for playing and annotating videos.

    Args:
        app (customtkinter.CTk): The main application window.
        file_name (str): Name of the video file to be played.
        done_event (threading.Event): Event to signal completion.
        long_annotations (bool): Whether to allow long annotations.
    """
    def __init__(self, app, file_name, done_event, long_annotations=False):
        # Class Variables
        self.app, self.file_name, self.done_event = app, file_name, done_event

        # Initialize VideoPlayer with the `long_annotations` flag
        self.long_annotations = long_annotations
        self.annotation_chunk = []

        # VideoCapture Variables
        self.cap, self.frame = None, None

        # Annotation Variables
        self.last_frame, self.start_point = None, None
        self.paused, self.drawing = False, False
        self.curr_frame_idx = 0  # Initialize current frame index

        # Screen and Frame Variables
        self.screen_width, self.screen_height = self.app.winfo_screenwidth(), self.app.winfo_screenheight()
        self.frame_width, self.frame_height, self.frame_delay = None, None, None

        # Audio Variables
        self.samplerate, self.channels = 44100, 2

        # Command Queue
        self.command_queue = queue.Queue()

        # start the video player
        self.start()

    def start(self):
        """Start the video player."""
        if not self._validate_file(self.file_name):
            return
        
        self._initialize_video_capture()
        self._initialize_data_object()
        self._initialize_control_window()

        self.video_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.video_thread.start()

        # Begin the main loop
        logger.info(f"VideoPlayer initialized with frame delay: {self.frame_delay} ms")
        self.control_window.mainloop()

    def _validate_file(self, file_name):
        """Validate the existence of the video file."""
        file_path = os.path.join(config.in_path, file_name)
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_name}")
            messagebox.showerror("Error", "File not found.")
            return False
        return True
    
    def _initialize_video_capture(self):
        """Initialize video capture and related settings."""
        file_path = os.path.join(config.in_path, self.file_name)
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            logger.error(f"Failed to open video file: {self.file_name}")
            messagebox.showerror("Error", "Failed to open video file.")
            return

        self.last_frame_idx = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.last_frame_idx)
        _, self.last_frame = self.cap.read()

        self.frame_height, self.frame_width = self.last_frame.shape[:2]
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def _initialize_data_object(self):
        """Initialize the data object to handle video information."""
        self._data = Data(
            in_path=config.in_path, out_path=config.out_path,
            name=self.file_name,
            frame_width=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            frame_height=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=int(self.cap.get(cv2.CAP_PROP_FPS)),
            fc=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            sample_rate=self.samplerate, channels=self.channels
        )
        self.frame_delay = int((1 / self._data.frame_rate) * 1000)

    def _initialize_control_window(self):
        """Initialize the control window."""
        self.control_window = ControlWindow(self.app, self.file_name, self)

    def audio_callback(self, indata, frames, time, status) -> None:
        """
        Callback for recording audio.
        
        Args:
            indata (numpy.ndarray): The audio data.
            frames (int): The number of frames.
            time (sounddevice.CallbackTimeInfo): The time information.
            status (sounddevice.CallbackFlags): The callback flags.
        """
        if self.start_counter is None:
            self.start_counter = t.perf_counter()
        timestamp = t.perf_counter() - self.start_counter
        self._data.add_audio_data(timestamp, indata.copy())

    def mouse_callback(self, event, x, y, flags, param) -> None:
        """
        Callback for handling mouse events.
        
        Args:
            event (int): The event type.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            flags (int): The flags.
            param (Any): Additional parameters.
        """
        if event == cv2.EVENT_LBUTTONDOWN and not self.drawing:
            self.drawing = True
            self._data.add_annotation("start", (x, y))
            logger.debug("Started drawing annotation at: (%d, %d)", x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self._data.add_annotation("move", (x, y))
        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            self._data.add_annotation("end", (x, y))
            logger.debug("Ended drawing annotation at: (%d, %d)", x, y)

    def draw_annotations(self) -> None:
        """
        Draw annotations on the given frame based on the frame index."""
        # Get the last annotation
        annotation = self._data.get_last_anno()
        largest_key = max(self._data.annotations.keys())
        if annotation and abs(largest_key - self._data.get_frames_length) <= 5:
            command, point = annotation
            if command == "start":
                self.start_point = point
                self.annotation_chunk = [point]
            elif command == "move":
                self._draw_move_annotations(point)
            elif command == "end":
                self._finalize_annotation_chunk(point)

    def _draw_move_annotations(self, point):
        """Draw move annotations."""
        if self.long_annotations:
            self.annotation_chunk.append(point)
            for i in range(len(self.annotation_chunk) - 1): 
                cv2.line(self.frame, self.annotation_chunk[i], self.annotation_chunk[i + 1], (0, 0, 255), 3)
        else:
            if self.start_point: 
                cv2.line(self.frame, self.start_point, point, (0, 0, 255), 3)
            self.start_point = point

    def _finalize_annotation_chunk(self, point):
        """Finalize the annotation chunk."""
        if self.long_annotations:
            for i in range(len(self.annotation_chunk) - 1): 
                cv2.line(self.frame, self.annotation_chunk[i], self.annotation_chunk[i + 1], (0, 0, 255), 3)
        else:
            if self.start_point: 
                cv2.line(self.frame, self.start_point, point, (0, 0, 255), 3)
        self.annotation_chunk = []
        self.start_point = None

    def draw_timer(self, frame, elapsed_ms):
        """Draw the elapsed time on the video frame."""
        elapsed_time = datetime.timedelta(milliseconds=int(elapsed_ms))
        time_str = str(elapsed_time).split(".")[0]  # To display time as HH:MM:SS
        position = (frame.shape[1] - 75, frame.shape[0] - 20)  # Adjust to position the text in the bottom right corner
        cv2.putText(frame, time_str, position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return time_str

    def main_loop(self):
        """Main loop for video playback and annotation."""
        cv2.namedWindow("Video Player")
        cv2.setMouseCallback("Video Player", self.mouse_callback)

        total_frames = self._data.get_max_frames
        self.start_counter = t.perf_counter()  # Start high-resolution timer

        # Calculate the coordinates to center the frame
        mid_x = (self.screen_width - self.frame_width) // 2
        mid_y = (self.screen_height - self.frame_height) // 2

        # move window to the center
        cv2.moveWindow("Video Player", mid_x, mid_y)

        # start audio stream
        with sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=self.audio_callback):
            with tqdm(total=total_frames, desc="Processing Frames") as self.pbar:
                while self.cap.isOpened():
                    self._process_video_frame()

    def _process_video_frame(self):
        """Process each video frame."""
        start_time = t.time()
        self._handle_commands()

        # check if the video is paused
        if not self.paused:
            ret, self.frame = self.cap.read()
            # Check if video capture is at the last frame
            if not ret:
                self.frame = self.last_frame.copy()
                current_time = self.last_frame_time
            else:
                self.curr_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.pause_frame = self.frame.copy()
                self.control_window.seek_var.set(self.curr_frame_idx)

                # Capture the current time, but cache it in case it's the last frame
                current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC)
                self.last_frame_time = current_time  # Cache the last valid time
        else:
            self.frame = self.pause_frame.copy()
            current_time = self.last_frame_time  # Use cached time when paused

        if self.drawing:
            self.draw_annotations()

        time_str = self.draw_timer(self.frame, current_time)

        cv2.imshow("Video Player", self.frame)
        self._data.add_curr_frame(self.curr_frame_idx, self.pbar.n, self.pause_frame.copy(), time_str, t.perf_counter() - self.start_counter)

        key = cv2.waitKey(1) & 0xFF
        self.pbar.update(1)
        self._manage_frame_delay(start_time)

    def _handle_commands(self):
        """Handle commands from the command queue."""
        try:
            command = self.command_queue.get_nowait()
            if command == 'pause':
                self.toggle_pause()
            elif isinstance(command, tuple) and command[0] == 'seek':
                self.seek(command[1])
            elif command == 'restart':
                self.restart()
        except queue.Empty:
            pass

    def _manage_frame_delay(self, start_time):
        """Manage the delay between frames."""
        elapsed_time = t.time() - start_time
        remaining_time = max(0, self.frame_delay / 1000 - elapsed_time)
        if remaining_time > 0: 
            t.sleep(remaining_time)

    def toggle_pause(self):
        """Toggle the pause state of the video."""
        self.paused = not self.paused

    def seek(self, frame_number) -> None:
        """Seek to a specific frame.
        
        Args:
            frame_number (int): The frame number to seek to.
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self._data.update_curr_frame(frame_number)
        self.curr_frame_idx = frame_number

    def restart(self) -> None:
        """Restart the video."""
        # Reset the video player
        self.paused, self.drawing = False, False

        # reset cap to the first frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # clean data
        self._data.clean()

        self._data.update_max_frames(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        
        # clear command queue
        while not self.command_queue.empty():
            _ = self.command_queue.get()
        logger.info("Command queue cleared and video restarted")

        # Reset tqdm progress bar
        self.pbar.reset(total=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.pbar.refresh()

    def close(self, save=False):
        """Close the video player.
        
        Args:
            save (bool): Whether to save the data. Defaults to False.
        """
        # relese video capture and stop audio stream
        self.cap.release()
        sd.stop()

        # save data if required
        if save: 
            self._data.save_data(self.app)

        # close windows and threads
        cv2.destroyAllWindows()
        self.done_event.set()
        self.video_thread.join(1)
        self.control_window.quit()
        self.control_window.destroy()
        self.app.deiconify()
        logger.info("VideoPlayer closed")

class AnnotatedPlayer:
    """
    AnnotatedPlayer class for watching annotated videos.

    Args:
        watch_file (str): Path to the annotated video file.
        meta_file (str): Path to the metadata file for annotations.
        long_annotations (bool): Whether to allow long annotations.
    """
    def __init__(self, watch_file, meta_file, long_annotations=False):
        logger.info(f"Initializing AnnotatedPlayer for file: {watch_file}")
        # Update class variables
        self.watch_file = watch_file
        self.meta_file = meta_file

        # Initialize player with the `long_annotations` flag
        self.long_annotations = long_annotations
        self.annotation_chunk = []

        # Validate the files
        if not self._validate_files():
            logger.error(f"File validation failed: {watch_file}, {meta_file}")
            messagebox.showerror("Error", "File validation failed.")
            return
        
        # Load metadata and initialize audio
        self.meta = self._load_metadata(meta_file)

        # Initialize the video player
        self._initialize_video_capture()

        # Initialize audio
        self._initialize_audio(watch_file)

        # Initialize annotation variables
        self._initialize_annotation_variables()

        # Start the video player
        self.show()

    def _validate_files(self):
        """
        Validate the video and metadata files.
        """
        if not os.path.exists(self.watch_file):
            logger.error(f"File not found: {self.watch_file}")
            messagebox.showerror("Error", "File not found.")
            return False

        if not os.path.exists(self.meta_file):
            logger.error(f"File metadata not found: {self.meta_file}")
            messagebox.showerror("Error", "File metadata not found.")
            return False

        return True
    
    def _initialize_video_capture(self):
        """
        Initialize the video capture object.
        """
        self.cap = cv2.VideoCapture(self.watch_file)
        if not self.cap.isOpened():
            logger.error(f"Failed to open watch file: {self.watch_file}")
            messagebox.showerror("Error", "Failed to open video file.")
            return

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_rate = self.meta['metadata']['frame_rate']
        self.frame_delay = int((1 / self.frame_rate) * 1000)

    def _load_metadata(self, meta_file):
        """
        Load the metadata from the metadata file.

        Args:
            meta_file (str): The path to the metadata file.

        Returns:
            dict: The metadata dictionary
        """
        with open(meta_file, "r") as file:
            return json.load(file)

    def _initialize_audio(self, video_file):
        """
        Initialize the audio for the video file.
        
        Args:
            video_file (str): The path to the video file.
        """
        self.extract_audio(video_file)
        mixer.init()
        mixer.music.load("tmp.mp3")
        mixer.music.play()

    def extract_audio(self, video_file):
        """
        Extract audio from the video file.
        
        Args:
            video_file (str): The path to the video file.
        """
        with VideoFileClip(video_file) as video:
            video.audio.write_audiofile('tmp.mp3', logger=None, verbose=False)

    def _initialize_annotation_variables(self):
        self.start_time = None
        self.last_point = None

    def show(self):
        """Show the annotated video with annotations."""
        # open video player and display annotations
        cv2.namedWindow("Annotater Player")
        logger.info(f"Started Annotated Player for file: {self.watch_file}")

        # play the video
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self._process_frame(frame, frame_number)

            cv2.imshow("Annotater Player", frame)
            if cv2.waitKey(self.frame_delay) & 0xFF == ord('q'):
                break

        self.close()
        logger.info("Annotater Player closed")

    def _process_frame(self, frame, frame_number):
        if str(frame_number) in self.meta:
            frame_data = self.meta[str(frame_number)]
            if frame_data["anno"]: 
                self._draw_annotations(frame, frame_data["anno"])
            if frame_data["time_str"]: 
                self._draw_time(frame, frame_data["time_str"])

    def _draw_annotations(self, frame, anno):
        command, point = anno
        if command == "start":
            self.annotation_chunk = [tuple(point)]
        elif command == "move":
            self._draw_move_annotations(frame, point)
        elif command == "end":
            self._finalize_annotation_chunk(frame, point)

    def _draw_move_annotations(self, frame, point):
        if self.long_annotations:
            self.annotation_chunk.append(tuple(point))
            for i in range(len(self.annotation_chunk) - 1):
                cv2.line(frame, self.annotation_chunk[i], self.annotation_chunk[i + 1], (0, 0, 255), 3)
        else:
            if self.annotation_chunk:
                cv2.line(frame, self.annotation_chunk[-1], tuple(point), (0, 0, 255), 3)
            self.annotation_chunk = [tuple(point)]
        self.last_point = tuple(point)

    def _finalize_annotation_chunk(self, frame, point):
        if self.annotation_chunk:
            for i in range(len(self.annotation_chunk) - 1):
                cv2.line(frame, self.annotation_chunk[i], self.annotation_chunk[i + 1], (0, 0, 255), 3)
        self.annotation_chunk = []
        self.last_point = None

    def _draw_time(self, frame, time_str):
        cv2.putText(frame, time_str, (frame.shape[1] - 75, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    def close(self):
        """Close the AnnotatedPlayer."""
        self.cap.release()
        mixer.music.stop()
        mixer.quit()
        os.remove("tmp.mp3")
        cv2.destroyAllWindows()
        messagebox.showinfo("Done", "File is done playing")
        logger.info("AnnotatedPlayer resources released and windows closed")