import cv2

import customtkinter as ctk
from customtkinter import CTkImage
from tkinter import filedialog, messagebox, StringVar

from PIL import Image

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

import subprocess, time

# Global variables to store user input and media processing
user_name = ""
user_level = ""
frames = []  # To store video frames for annotations
audio_data = []  # To capture audio data
drawing = False  # Flag to check if drawing is active
last_point = None  # Store the last point for drawing
save_annotations_button = None  # Declare the save button globally

def validate_inputs(name, level):
    return bool(name) and level != "Select Level"

def save_info(name, level):
    global user_name, user_level
    user_name = name
    user_level = level
    messagebox.showinfo("Info", f"Name: {user_name}, Level: {user_level}")

def open_video():
    file_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
    if file_path:
        play_video(file_path)

def play_video(file_path):
    global last_frame, audio_data, frames
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        messagebox.showerror("Error", "Failed to open video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"FPS: {fps}")

    paused = False
    start_time = time.time()
    pause_time = None
    audio_stream = sd.InputStream(samplerate=44100, channels=2, callback=audio_callback)
    audio_stream.start()  # Start recording audio when video window opens

    def update_frame():
        nonlocal paused
        if not paused:
            ret, frame = cap.read()
            if ret:
                global last_frame
                last_frame = frame.copy()
                frames.append(last_frame.copy())  # Capture every frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                ctk_img = CTkImage(light_image=img, size=(frame.shape[1], frame.shape[0]))
                video_label.configure(image=ctk_img)
                video_label.image = ctk_img
                current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                seeker.set(current_frame)
                video_label.after(10, update_frame)
            else:
                cap.release()
                audio_stream.stop()

    def handle_pause_frames():
        nonlocal start_time, pause_time
        global frames

        diff = start_time - pause_time

        # calculate the number of frames to duplicate based on the time paused
        frames_to_duplicate = int(diff * fps)
        print(f"Frames to duplicate: {frames_to_duplicate}")
        print(f"Frames before: {len(frames)}")

        # add duplicated frames to frames list
        for i in range(frames_to_duplicate):
            frames.append(last_frame.copy())

        print(f"Frames after: {len(frames)}")

    def toggle_pause():
        nonlocal paused, fps, start_time, pause_time
        paused = not paused

        # Update the label of the button based on the current state after toggling
        play_pause_button.configure(text="Play" if paused else "Pause")
        if not paused: 
            start_time = time.time()
            if pause_time and start_time > pause_time: 
                handle_pause_frames()  # Add frames while paused
            update_frame()  # Resume capturing new frames
        else: 
            paused_time = time.time()

    def close_window(video_window, cap, audio_stream):
        cap.release()
        audio_stream.stop()  # Stop recording audio when window closes
        save_annotated_video_audio()  # Save video and audio on close
        video_window.destroy()

    def seek(value):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(value))
        update_frame()

    def on_mouse_click(event):
        global drawing, last_point
        if event.num == 1 and paused:  # Ensure this happens only if the video is paused
            drawing = True
            last_point = (event.x, event.y)
        elif not paused:
            drawing = False

    def on_mouse_move(event):
        global last_point
        if drawing and paused:
            x, y = event.x, event.y
            draw_annotation(last_point, (x, y))
            last_point = (x, y)

    video_window = ctk.CTkToplevel()
    video_window.title("Video Player")
    video_window.protocol("WM_DELETE_WINDOW", lambda: close_window(video_window, cap, audio_stream))  # Handle window close

    video_label = ctk.CTkLabel(video_window, text="")
    video_label.pack()
    video_label.bind("<Button>", on_mouse_click)
    video_label.bind("<B1-Motion>", on_mouse_move)

    control_frame = ctk.CTkFrame(video_window)
    control_frame.pack(pady=10)

    play_pause_button = ctk.CTkButton(control_frame, text="Pause", command=toggle_pause)
    play_pause_button.grid(row=0, column=0, padx=5)

    seeker = ctk.CTkSlider(control_frame, from_=0, to=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), command=seek)
    seeker.grid(row=0, column=1, padx=5, sticky="ew")

    video_window.columnconfigure(1, weight=1)
    update_frame()

def draw_annotation(start, end):
    """Draw annotation on the frame"""
    global last_frame, frames
    annotated_frame = last_frame.copy()
    cv2.line(annotated_frame, start, end, (0, 255, 0), 2)
    frames.append(annotated_frame)
    update_save_button_state()

def update_save_button_state():
    global save_annotations_button
    if frames:
        save_annotations_button.configure(state="normal")
    else:
        save_annotations_button.configure(state="disabled")

def audio_callback(indata, frames, time, status):
    """Callback function to capture audio"""
    audio_data.append(indata.copy())

def save_annotated_video_audio():
    """Function to save video and audio, and merge them using FFmpeg"""
    output_video_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
    if not output_video_path:
        return

    # Assume all frames are the same size as the first frame
    height, width, layers = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video_path, fourcc, 20, (width, height))  # Use actual frame size
    for frame in frames:
        out.write(frame)  # Ensure frames are in BGR format if necessary
    out.release()

    # Save audio
    audio_array = np.concatenate(audio_data, axis=0)
    output_audio_path = output_video_path.replace(".mp4", ".wav")
    write(output_audio_path, 44100, audio_array)

    # Combine video and audio
    subprocess.run([
        'ffmpeg', 
        '-i', 
        output_video_path, 
        '-i', 
        output_audio_path, 
        '-c:v', 
        'copy', 
        '-c:a', 
        'aac', 
        '-strict', 
        'experimental', 
        output_video_path.replace('.mp4', '_annotated.mp4')])

def run(app):
    global save_annotations_button
    # TODO : Startup Screen

    # TODO : Ask to select Video (save video name for reference later)
    # Create a frame for user inputs
    input_frame = ctk.CTkFrame(app)
    input_frame.pack(pady=20)

    # Name Label and Text Field
    name_label = ctk.CTkLabel(input_frame, text="Name:")
    name_label.grid(row=0, column=0, padx=10, pady=10)
    name_entry = ctk.CTkEntry(input_frame, width=200)
    name_entry.grid(row=0, column=1, padx=10, pady=10)

    # Level Label and Dropdown
    level_label = ctk.CTkLabel(input_frame, text="Level:")
    level_label.grid(row=1, column=0, padx=10, pady=10)
    level_var = StringVar(value="Select Level")
    level_dropdown = ctk.CTkOptionMenu(input_frame, variable=level_var, values=["Beginner", "Intermediate", "Advanced"])
    level_dropdown.grid(row=1, column=1, padx=10, pady=10)

    # Save Button
    save_button = ctk.CTkButton(input_frame, text="Save", state="disabled", command=lambda: save_info(name_entry.get(), level_var.get()))
    save_button.grid(row=2, columnspan=2, pady=20)

    # TODO : open video in a window (add play/pause button and seeker, record audio and annotations)
    # Video Button
    video_button = ctk.CTkButton(app, text="Open Video", command=open_video)
    video_button.pack(pady=20)

    # Save Annotations Button
    save_annotations_button = ctk.CTkButton(app, text="Save Annotated Video & Audio", command=save_annotated_video_audio, state="disabled")
    save_annotations_button.pack(pady=20)

    def check_validity(*args):
        if validate_inputs(name_entry.get(), level_var.get()):
            save_button.configure(state="normal")
        else:
            save_button.configure(state="disabled")
        update_save_button_state()

    # Bind validation check to name entry and level dropdown changes
    name_entry.bind("<KeyRelease>", check_validity)
    level_var.trace("w", check_validity)

    # TODO : Save annotations and audio with the orignal video using ffmpg (ask for save location)

# run main loop
if __name__ == "__main__":
    # Set the theme (optional)
    ctk.set_appearance_mode("Dark")  # Can be "Dark" or "Light"

    # Create the main application window
    app = ctk.CTk()

    app.title("CustomTkinter Example") # Set the title of the window

    # add default styling options
    ctk.set_default_color_theme("dark-blue")  # Set the default color theme
    # ctk.set_icon("path/to/icon.png")  # Set the icon of the window
    # ctk.set_font("Arial", 12)  # Set the default font and size
    # ctk.set_bg("black")  # Set the default background color
    # ctk.set_fg("white")  # Set the default foreground color
    # TODO : set geometry to the full screen
    app.geometry("600x350")  # Set the size of the window

    run(app)

    # Start the main application loop
    app.mainloop()