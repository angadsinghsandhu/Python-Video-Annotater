# Annotater: Advanced Video Annotation Tool

Annotater is a sophisticated video annotation tool designed for detailed and precise marking of video content. It integrates robust video and audio processing capabilities to provide a seamless annotation experience. Based on Python, the tool uses libraries like CustomTkinter for its UI, OpenCV for video processing, and PyAudio for audio manipulation, ensuring a comprehensive environment for users to work with video data.

## Prerequisites

1. Python 3.8+
2. Knowledge of video formats and codecs
3. Basic understanding of threading and concurrent programming in Python

## Key Features

- **Video Playback Controls**: Play, pause, seek, and stop functionalities for thorough video review.
- **Audio Processing**: Integrated audio playback synchronized with video.
- **Dynamic Annotation**: Users can draw and save annotations directly on the video frame.
- **Multi-threading**: Utilizes threading for non-blocking video processing.
- **Comprehensive Logging**: Detailed logs for debugging and tracking application processes.

## Important Links

- [Tutorial Video](https://livejohnshopkins-my.sharepoint.com/:f:/g/personal/asandhu9_jh_edu/EqDDvLH7cRdLtwuIQk6TABwB9nD0e7UoKNdjALV_RTnEtg?e=Nq0M4p)
- [Application Download](https://livejohnshopkins-my.sharepoint.com/:f:/g/personal/asandhu9_jh_edu/Eh60kxJUMFZAgpDcLsQO2l0BQiqQNZ7frvEp0rdNiEJvBA?e=7hmr37)

## Metadata

| Attribute         | Value                                          |
|-------------------|------------------------------------------------|
| Name              | Annotater                                      |
| Version           | 1.1.1                                          |
| Compatibility     | Windows 10, Ubuntu 20.04                       |
| License           | MIT License                                    |
| Release Date      | 2024-01-24                                     |
| Last Updated      | 2024-07-18                                     |

## How to Install

1. Clone the repository to your local machine using the following command:

```bash
git clone git
```

1. Install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```

## HOW TO USE

link to file : [HOW_TO_USE](https://github.com/angadsinghsandhu/Python-Video-Annotater/blob/main/HOW_TO_USE.pdf)

Run application on command line using following command:

```bash
python -m main
```

## Documentation

### Overview

Annotater is built to facilitate detailed annotations of video files, offering tools to mark and comment on video content for educational, research, or editing purposes. The application supports various video formats and provides an interface to manage video playback, audio synchronization, and annotation storage.

### Modules and Code Structure

**`main.py`**:

- This is the entry point of the application. It sets up the main application window, initializes logging based on a configuration file, and handles the application's closing event.

**`config.py`**:

- Manages the application configuration, including paths and logging settings. It dynamically updates these settings during runtime based on user interactions.

**`data.py`**:

- Handles data storage for videos, audio, and annotations. It implements methods to add, update, and retrieve data elements tied to specific video frames.

**`screens.py`**:

- Contains the UI elements for the splash screen and the save progress screen. These screens inform the user of ongoing processes and ensure the application remains responsive during lengthy operations.

**`logging_config.yaml`**:

- Configures different logging handlers and formats, including file and console outputs tailored to different logging levels (DEBUG, INFO, ERROR).

### Advanced Features

- **Multi-threaded Processing**: Ensures video playback and annotation processes run smoothly without interrupting the user interface.
- **Customizable UI**: Thanks to CustomTkinter, the UI can be easily modified to match user preferences or specific requirements.

## Directions of Use

1. **Starting the Application**:
   - Run `main.py` to open the application. A splash screen appears initially, followed by the main annotation interface.

2. **Opening a Video**:
   - Use the file dialog to select a video file for annotation. The video will load, and playback controls will appear.

3. **Annotating a Video**:
   - Play the video and pause at the frame you want to annotate. Use the mouse to draw annotations directly on the video frame. Annotations can be saved and will be associated with the specific frame.

4. **Saving Annotations**:
   - Once annotation is complete, use the save option to store annotations. The application supports exporting annotations in JSON format, which includes metadata about the video and the annotations.

5. **Reviewing and Editing Annotations**:
   - Load an annotated video file to review annotations. Annotations can be edited by navigating to the specific frames and modifying the existing marks.

## Building the Application

To build the application, use the following command:

```bash
pyinstaller --onefile --windowed --name Annotater --icon=imgs/tool.ico main.py
```

This command packages the application into a single executable file named `Annotater` with a custom icon. The resulting executable can be distributed and run on compatible systems.

Use the following command to build the application with required non-py files (images, yaml, etc.):

```bash
pyinstaller Annotater.spec
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
