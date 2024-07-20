"""
player.py

This module handles video playback, annotation, and audio synchronization
for both annotating and watching annotated videos.
"""

# General Imports
import cv2, os, threading, queue, json, logging
import sounddevice as sd, time as t
from tqdm import tqdm
from tkinter import messagebox
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Hide pygame support prompt
from pygame import mixer
from moviepy.editor import VideoFileClip

# Local Imports
from data import Data
from config import config
from annotater.controller import ControlWindow

# Set up logging
logger = logging.getLogger('app')

class VideoPlayer:
    """
    VideoPlayer class for playing and annotating videos.

    Args:
        app (customtkinter.CTk): The main application window.
        file_name (str): Name of the video file to be played.
        done_event (threading.Event): Event to signal completion.
    """
    def __init__(self, app, file_name, done_event):
        # Class Variables
        self.app, self.file_name, self.done_event = app, file_name, done_event

        # Position and Dimention Variables
        self.frame_width, self.frame_height, self.screen_width, self.screen_height = None, None, None, None

        # VideoCapture Variables
        self.cap, self.frame, self.ret = None, None, None
        self.last_frame, self.last_frame_idx, self.curr_frame_idx = None, None, None
        self.start_counter, self.pause_frame = None, None

        # Data Object
        self._data = None

        # Control Variables
        self.control_window, self.paused = None, False

        # Annotation Variables
        self.drawing, self.last_point = False, None

        # Audio Variables
        self.samplerate, self.channels, self.frame_delay = 44100, 2, None

        # Command Queue
        self.command_queue = queue.Queue()

        # start the video player
        self.start()

    def start(self):
        """Start the video player."""
        # Check if the file exists
        if not os.path.exists(f"{config.in_path}/{self.file_name}"):
            logger.error(f"File not found: {self.file_name}")
            messagebox.showerror("Error", "File not found.")
            return

        # Create video capture object for the file
        self.cap = cv2.VideoCapture(f"{config.in_path}/{self.file_name}")
        if not self.cap.isOpened():
            logger.error(f"Failed to open video file: {self.file_name}")
            messagebox.showerror("Error", "Failed to open video file.")
            return

        # Get the last frame index and set the cpature to the last frame
        self.last_frame_idx = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.last_frame_idx)

        # Get the last frame and its dimensions
        _, self.last_frame = self.cap.read()
        self.frame_height, self.frame_width = self.last_frame.shape[:2]
        self.screen_width, self.screen_height = self.app.winfo_screenwidth(), self.app.winfo_screenheight()

        # Set the capture back to the first frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # Initialize the Data object
        self._data = Data(
            in_path=config.in_path, out_path=config.out_path,
            name=self.file_name,
            frame_width=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            frame_height=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=int(self.cap.get(cv2.CAP_PROP_FPS)),
            fc=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            sample_rate=self.samplerate, channels=self.channels
        )

        # Initialize the frame delay
        self.frame_delay = int((1 / self._data.frame_rate) * 1000)

        # Initialize the video thread and control window
        self.video_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.control_window = ControlWindow(self.app, self.file_name, self)
        self.video_thread.start()

        # Begin the main loop
        logger.info(f"VideoPlayer initialized with frame delay: {self.frame_delay} ms")
        self.control_window.mainloop()

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
        _annotation = self._data.get_last_annotation()
        largest_key = max(self._data.annotations.keys())

        # Sync the annotation with the last frame
        if _annotation is not None and abs(largest_key - self._data.get_frames_length) <= 5:
            command, (x, y) = _annotation

            # Draw the annotation based on the command
            if command == "start":
                self.start_point = (x, y)
            elif command == "move":
                cv2.line(self.frame, self.start_point, (x, y), (0, 0, 255), 3)
                self.start_point = (x, y)
            elif command == "end":
                cv2.line(self.frame, self.start_point, (x, y), (0, 0, 255), 3)
                self.start_point = None
                self.drawing = False
            logger.debug("Annotations drawn on frame")

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
                    start_time = t.time()
                    current_counter = t.perf_counter() - self.start_counter

                    self.curr_frame_idx = curr_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                    if curr_frame >= total_frames: curr_frame = total_frames - 1
                    
                    # update seeker
                    self.control_window.seek_var.set(curr_frame)

                    # Check for commands
                    try:
                        command = self.command_queue.get_nowait()

                        # Execute the command if available
                        if command == 'pause': self.toggle_pause()
                        elif isinstance(command, tuple) and command[0] == 'seek': self.seek(command[1])
                        elif command == 'restart': self.restart()

                    except queue.Empty:
                        pass
                    
                    # Check for pause
                    if not self.paused:
                        self.ret, self.frame = self.cap.read()
                        if not self.ret: 
                            self.pbar.total += 1
                            self.frame = self.last_frame.copy()
                        self.pause_frame = self.frame.copy()
                    else:
                        self.frame = self.pause_frame.copy()
                        self.pbar.total += 1
                        self._data.increment_max_frame()

                    if self.drawing: self.draw_annotations()

                    # Display the frame
                    cv2.imshow("Video Player", self.frame)

                    # add current frame to data
                    self._data.add_curr_frame(current_counter, curr_frame)

                    # Check for key press
                    key = cv2.waitKey(1) & 0xFF

                    # Update progress bar
                    self.pbar.update(1)

                    # Update frame delay
                    elapsed_time = t.time() - start_time
                    remaining_time = max(0, self.frame_delay / 1000 - elapsed_time)  # Convert frame_delay to seconds
                    if remaining_time > 0:
                        t.sleep(remaining_time)

                logger.info("Video processing completed")

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
        self._data.update(
            in_path=config.in_path, out_path=config.out_path,
            name=self.file_name, 
            frame_width=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
            frame_height=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), 
            fps=int(self.cap.get(cv2.CAP_PROP_FPS)), 
            fc=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            sample_rate=self.samplerate, channels=self.channels)
        
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
        if save: self._data.save_data(self.app)

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
    """
    def __init__(self, watch_file, meta_file):
        logger.info(f"Initializing AnnotatedPlayer for file: {watch_file}")

        # Update class variables
        self.watch_file = watch_file
        self.meta_file = meta_file

        # Check if the files exist
        if not os.path.exists(watch_file):
            logger.error(f"File not found: {watch_file}")
            messagebox.showerror("Error", "File not found.")
            return
        
        # Create video capture object for the file
        self.cap = cv2.VideoCapture(watch_file)
        if not self.cap.isOpened():
            logger.error(f"Failed to open watch file: {watch_file}")
            messagebox.showerror("Error", "Failed to open video file.")
            return

        if not os.path.exists(meta_file):
            logger.error(f"File metadata not found: {meta_file}")
            messagebox.showerror("Error", "File metadata not found.")
            return
        
        with open(meta_file, "r") as file:
            self.meta = json.load(file)

        # Extract and save audio using moviepy
        self.extract_audio(watch_file)

        # Initialize pygame mixer for audio playback
        mixer.init()
        mixer.music.load("tmp.mp3")
        mixer.music.play()

        # Annotation variables
        self.start_time = None
        self.last_point = None

        # Get video properties
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_rate = self.meta['metadata']['frame_rate']
        self.frame_delay = int((1 / self.frame_rate) * 1000)

        # Start the video player
        self.show()

    def extract_audio(self, video_file):
        """
        Extract audio from the video file.
        
        Args:
            video_file (str): The path to the video file.
        """
        video = VideoFileClip(video_file)
        audio = video.audio
        audio.write_audiofile('tmp.mp3', logger=None, verbose=False)
        audio.close()
        video.close()

    def show(self):
        """Show the annotated video with annotations."""
        # open video player and display annotations
        cv2.namedWindow("Annotater Player")
        logger.info(f"Started Annotated Player for file: {self.watch_file}")

        # play the video
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            
            # check if frame is available and get the frame number
            if ret:
                frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                
                # check if the frame has annotations
                if str(frame_number) in self.meta:
                    command, point = self.meta[str(frame_number)]

                    # check the command and draw the annotation
                    if command == "start":
                        self.last_point = tuple(point)
                    elif command == "move":
                        cv2.line(frame, self.last_point, tuple(point), (0, 0, 255), 3)
                        self.last_point = tuple(point)
                    elif command == "end":
                        cv2.line(frame, self.last_point, tuple(point), (0, 0, 255), 3)
                        self.last_point = None

                cv2.imshow("Annotater Player", frame)
                if cv2.waitKey(self.frame_delay) & 0xFF == ord('q'): break
            else: break

        self.close()
        logger.info("Annotater Player closed")

    def close(self):
        """Close the AnnotatedPlayer."""
        self.cap.release()
        mixer.music.stop()
        mixer.quit()
        os.remove("tmp.mp3")
        cv2.destroyAllWindows()
        messagebox.showinfo("Done", "File is done playing")
        logger.info("AnnotatedPlayer resources released and windows closed")