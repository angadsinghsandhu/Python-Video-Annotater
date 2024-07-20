import cv2
import numpy as np
from scipy.io.wavfile import write
import sounddevice as sd
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog

# Initialize the drawing flag and last point
drawing = False
last_point = None

# Define the callback function for drawing annotations
def draw_annotation(event, x, y, flags, param):
    global last_point, drawing, last_frame, play
    if not play:  # Check if the video is paused
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            last_point = (x, y)
            # frames.append(last_frame.copy())
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            cv2.line(last_frame, last_point, (x, y), (0, 255, 0), 1)
            frames.append(last_frame.copy())
            last_point = (x, y)

            cv2.imshow(window_name, last_frame)  # Update the display
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            cv2.line(last_frame, last_point, (x, y), (0, 255, 0), 1)
            frames.append(last_frame.copy())
            cv2.imshow(window_name, last_frame)  # Final update after drawing

# Setup the GUI for file selection
root = tk.Tk()
root.withdraw()
video_path = filedialog.askopenfilename(title="Select the video file", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
if not video_path:
    exit("No video selected!")

# Video capture and window setup
cap = cv2.VideoCapture(video_path)
window_name = 'Video Player'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(window_name, draw_annotation)
cv2.resizeWindow(window_name, int(cap.get(3)), int(cap.get(4)))

# Audio and video setup
fps = cap.get(cv2.CAP_PROP_FPS)
frame_size = (int(cap.get(3)), int(cap.get(4)))
frames = []
samplerate = 44100
channels = 2
audio_data = []

# Function to handle audio recording
def audio_callback(indata, frames, time, status):
    audio_data.append(indata.copy())

# Main loop for video processing and annotation
frame_delay = int((1/fps)*1000)
with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
    play = True
    while cap.isOpened():
        if play:
            ret, frame = cap.read()
            if not ret:
                break
            last_frame = frame.copy()
            frames.append(last_frame)
            cv2.imshow(window_name, last_frame)
            key = cv2.waitKey(frame_delay) & 0xFF
        else:
            key = cv2.waitKey(1) & 0xFF  # Ensure responsiveness during pause

        if not play or key == 32:  # If the video is paused or if the space key was just pressed
            frames.append(last_frame)  # Ensure the possibly annotated frame is saved

        if key == 32:  # Space key to toggle play and pause
            play = not play
        elif key == 27:  # ESC key to exit
            break
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:  # Check if the window is closed
            break

    # Cleanup after the loop
    sd.stop()
    cap.release()
    cv2.destroyAllWindows()

# Save the annotated video along with recorded audio
output_video_filename = simpledialog.askstring("Output Video", "Enter the name for the output video file (without extension):", initialvalue="output_video")
output_audio_filename = simpledialog.askstring("Output Audio", "Enter the name for the audio file (without extension):", initialvalue="output_audio")
if not output_video_filename or not output_audio_filename:
    print("Output filename not specified.")
    exit()

output_video_path = f"{output_video_filename}.mp4"
output_audio_path = f"{output_audio_filename}.wav"

# Save video
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)
for frame in frames:
    out.write(frame)
out.release()

# Save audio
audio_array = np.concatenate(audio_data, axis=0)
write(output_audio_path, samplerate, audio_array)
audio_delay = -1
# Combine audio and video using FFmpeg
command = [
    'C:\\Program Files (x86)\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe',
    '-i', output_video_path,
    '-itsoffset', str(audio_delay),
    '-i', output_audio_path,
    '-map', '0:v',
    '-map', '1:a',
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-strict', 'experimental',
    # '-shortest',
    output_video_path.replace('.mp4', '_annotated.mp4')
]
subprocess.run(command)