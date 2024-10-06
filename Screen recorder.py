import os
import cv2
import numpy as np
import pyautogui
import pyaudio
import threading
import tkinter as tk
from tkinter import messagebox
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import wave
from datetime import datetime
import soundcard as sc
import soundfile as sf

final_file = ""
screen_size = pyautogui.size()
fourcc = cv2.VideoWriter_fourcc(*"XVID")
temp_recording_file = 'screen_recording.avi'
out = None
audio = pyaudio.PyAudio()
audio_stream = None
audio_frames = []
recording = False
record_audio = False
record_system_audio = False


def start_audio_recording():
    global audio_stream, audio_frames
    audio_frames = []
    audio_stream = audio.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=44100,
                              input=True,
                              frames_per_buffer=1024)
    while recording and record_audio:
        data = audio_stream.read(1024)
        audio_frames.append(data)


def start_system_audio_recording():
    global system_audio_frames
    system_audio_frames = []
    with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=44100) as mic:
        while recording and record_system_audio:
            data = mic.record(numframes=1024)
            system_audio_frames.append(data)


def save_audio():
    audio_filename = 'temp_audio.wav'
    wf = wave.open(audio_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    wf.writeframes(b''.join(audio_frames))
    wf.close()
    print(f"Audio saved as: {audio_filename}")
    return audio_filename


def save_system_audio():
    system_audio_filename = 'temp_system_audio.wav'
    sf.write(file=system_audio_filename, data=np.concatenate(system_audio_frames)[:, 0], samplerate=44100)
    print(f"System audio saved as: {system_audio_filename}")
    return system_audio_filename


def start_recording():
    global out, recording, record_audio, record_system_audio, final_file, fps
    now = datetime.now()
    final_file = now.strftime("%H-%M-%S--%d.%m.%Y") + ".avi"
    recording = True
    record_audio = mic_var.get() == 1
    record_system_audio = system_audio_var.get() == 1

    try:
        fps = int(fps_entry.get())
    except ValueError:
        fps = 20

    out = cv2.VideoWriter(temp_recording_file, fourcc, fps, screen_size)
    print(f"Recording started with {fps} FPS...")

    if record_audio:
        audio_thread = threading.Thread(target=start_audio_recording)
        audio_thread.start()

    if record_system_audio:
        system_audio_thread = threading.Thread(target=start_system_audio_recording)
        system_audio_thread.start()

    update_ui()

    while recording:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)


def stop_recording():
    global recording, audio_stream
    recording = False
    if out:
        out.release()

    audio_files = []

    if record_audio and audio_stream:
        audio_stream.stop_stream()
        audio_stream.close()
        audio_files.append(save_audio())

    if record_system_audio:
        audio_files.append(save_system_audio())

    merge_audio_video(audio_files, temp_recording_file, final_file)

    for file in audio_files:
        os.remove(file)
    os.remove(temp_recording_file)

    messagebox.showinfo("Screen Recorder", f"Recording saved as: {final_file}")
    update_ui()


def merge_audio_video(audio_files, video_file, final_file):
    video_clip = VideoFileClip(video_file)

    if audio_files:
        audio_clips = [AudioFileClip(audio_file) for audio_file in audio_files]
        final_audio = CompositeAudioClip(audio_clips)
        final_clip = video_clip.set_audio(final_audio)
    else:
        final_clip = video_clip

    final_clip.write_videofile(final_file, codec="libx264")
    print("Audio and video merged into final file.")


def start_recording_thread():
    threading.Thread(target=start_recording).start()


def update_ui():
    if recording:
        root.geometry("300x100")  # Make the window bigger when recording
        start_button.pack_forget()
        stop_button.pack(pady=10)
        mic_checkbox.pack_forget()
        system_audio_checkbox.pack_forget()
        fps_label.pack_forget()
        fps_entry.pack_forget()
    else:
        root.geometry("300x200")  # Return to original size when not recording
        stop_button.pack_forget()
        start_button.pack(pady=10)
        mic_checkbox.pack(pady=5)
        system_audio_checkbox.pack(pady=5)
        fps_label.pack(pady=5)
        fps_entry.pack(pady=5)


root = tk.Tk()
root.title("Screen Recorder")
root.geometry("300x200")  # Set initial window size

start_button = tk.Button(root, text="Start Recording", command=start_recording_thread)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Recording", command=stop_recording)

mic_var = tk.IntVar()
mic_checkbox = tk.Checkbutton(root, text="Enable Microphone", variable=mic_var)
mic_checkbox.pack(pady=5)

system_audio_var = tk.IntVar()
system_audio_checkbox = tk.Checkbutton(root, text="Enable System Audio", variable=system_audio_var)
system_audio_checkbox.pack(pady=5)

fps_label = tk.Label(root, text="FPS:")
fps_label.pack(pady=5)
fps_entry = tk.Entry(root)
fps_entry.insert(0, "20")
fps_entry.pack(pady=5)

root.mainloop()
audio.terminate()