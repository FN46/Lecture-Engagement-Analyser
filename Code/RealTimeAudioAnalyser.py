import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import threading
import queue
import time
import wave
from tkinter import messagebox
import librosa
from FaceAnalysis import FaceAnalysis


class RealTimeAudioAnalyser:
    def __init__(self, root, app):
        """
        Initialise the real-time audio analyser.

        Parameters:
        - root: The main Tkinter window.
        - app: Reference to the parent application instance for accessing settings.

        Sets up:
        - Audio buffers and state flags
        - Analysis queue for threading
        - Graph plotting figures and canvases for visualising metrics
        - Playback controls and defaults
        """
        self.root = root
        self.app = app  
        self.is_recording = False
        self.audio_buffer = []
        self.sr = 44100
        self.analysis_queue = queue.Queue()
        self.current_webcam_frame = None

        self.update_interval = app.settings.get("update_interval", 5.0)
        self.silence_threshold = app.settings.get("silence_threshold", 0.008)


        self.last_update_time = time.time() 

        self.fig, self.ax = plt.subplots(figsize=(10, 1))
        self.canvas_agg = None

        self.figures = {}
        self.canvases = {}

        self.current_playback_index = 0
        self.is_paused = False
        self.playback_thread = None

        metrics = ["Loudness", "Pitch", "Speech Rate", "Energy"]
        for metric in metrics:
            fig, ax = plt.subplots(figsize=(4, 3))
            self.figures[metric] = (fig, ax)
            self.canvases[metric] = None
            
    def update_from_settings(self):
        """
        Refresh analyser parameters based on the latest application settings.

        This method retrieves the `update_interval` and `silence_threshold` from the app's settings
        and prints out their current values for debugging purposes.
        """
        self.update_interval = self.app.settings.get("update_interval", 5.0)
        self.silence_threshold = self.app.settings.get("silence_threshold", 0.005)
        print(f"Updated update_interval: {self.update_interval}")
        print(f"Updated silence_threshold: {self.silence_threshold}")


    def should_update(self):
        """
        Determine whether it's time to trigger a new analysis update.

        Returns:
        - True if the time since the last update exceeds the configured interval.
        - False otherwise.
        """
        current_time = time.time()

        if current_time - self.last_update_time >= self.update_interval:
            print(f"Applying new update interval: {self.update_interval}") 
            self.last_update_time = current_time  
            return True  
        return False  









    ########################## Recording buttons ###############################



    def start_recording(self):
        """
        Start recording audio and initiate analysis processing.

        Launches two background threads:
        - One for recording live audio.
        - One for processing the recorded chunks asynchronously.
        """
        self.is_recording = True
        self.audio_buffer = []
        threading.Thread(target=self.record_audio).start()
        threading.Thread(target=self.process_audio).start()

    def stop_recording(self):
        """
        Stop the audio recording process.
        """
        self.is_recording = False

    def record_audio(self):
        """
        Continuously record incoming audio in chunks.

        - Buffers audio until a full second is captured.
        - Pushes it into a queue for background analysis.
        - Stores the full stream in `audio_buffer` for playback or saving.
        """
        buffer = []  
        self.audio_buffer = []  

        def callback(indata, frames, time, status):
            if self.is_recording:
                buffer.append(indata.copy())
                self.audio_buffer.append(indata.copy())  

                if len(buffer) * frames >= self.sr:
                    full_chunk = np.concatenate(buffer, axis=0)
                    self.analysis_queue.put(full_chunk) 
                    buffer.clear()  

        with sd.InputStream(samplerate=self.sr, channels=1, callback=callback):
            while self.is_recording:
                sd.sleep(100)

    def play_recording(self):
        """
        Play the most recently recorded audio in a separate thread.
        """
        if self.audio_buffer:
            audio_array = np.concatenate(self.audio_buffer, axis=0)
            self.current_playback_index = 0
            self.is_paused = False
            self.playback_thread = threading.Thread(target=self._play_audio, args=(audio_array,), daemon=True)
            self.playback_thread.start()

    def _play_audio(self, audio_array):
        """
        Internal method to handle audio playback.

        Plays from the current playback index and tracks progress.
        """
        try:
            self.is_paused = False
            self.start_time = time.time()  
            
            sd.play(audio_array[self.current_playback_index:], samplerate=self.sr, blocking=False)
            self._track_playback_progress(len(audio_array)) 
            sd.wait()  

            self.current_playback_index = len(audio_array) 
        except Exception as e:
            print(f"Error during audio playback: {e}")

    def pause_playback(self):
        """
        Pause current playback and store the resume position.
        """
        if not self.audio_buffer or self.is_paused:
            return 

        self.is_paused = True
        sd.stop() 


        try:
            stream = sd.get_stream()
            elapsed_time = stream.time if stream.active else 0 
        except Exception as e:
            print(f"Error getting stream time: {e}")
            elapsed_time = 0  

        self.current_playback_index = int(elapsed_time * self.sr) 


    def resume_playback(self):
        """
        Resume playback from where it was paused.
        """

        self.is_paused = False 
        audio_array = np.concatenate(self.audio_buffer, axis=0) 


        if self.current_playback_index < 0 or self.current_playback_index >= len(audio_array):
            self.current_playback_index = 0  


        sd.play(audio_array[self.current_playback_index:], samplerate=self.sr, blocking=False)


        self.start_time = time.time()
        self.playback_thread = threading.Thread(
            target=self._track_playback_progress, args=(len(audio_array),), daemon=True
        )
        self.playback_thread.start()


    def _track_playback_progress(self, total_samples):
        """
        Track playback progress to update index accurately.

        This method runs in the background during playback.
        """
        start_time = time.time()

        while not self.is_paused and self.current_playback_index < total_samples:
            elapsed_time = time.time() - start_time
            self.current_playback_index = int(elapsed_time * self.sr)

            if self.current_playback_index >= total_samples:
                self.current_playback_index = total_samples
                break

            time.sleep(0.1) 


                

    def seek_playback(self, seconds):
        """
        Seek the recording forward or backward by a given number of seconds.

        Parameters:
        - seconds (float): Number of seconds to skip (positive or negative).
        """
        if self.audio_buffer:
            self.is_paused = True  
            sd.stop()  
            audio_array = np.concatenate(self.audio_buffer, axis=0)
            new_index = self.current_playback_index + int(seconds * self.sr)
            self.current_playback_index = max(0, min(new_index, len(audio_array)))
            self.is_paused = False  
            self.playback_thread = threading.Thread(target=self._play_audio, args=(audio_array,), daemon=True)
            self.playback_thread.start()



    def download_recording(self, filename):
        """
        Save the latest recording as a WAV file to disk.

        Parameters:
        - filename (str): Desired output filename (should end in .wav).
        """
        if self.audio_buffer:
            audio_array = np.concatenate(self.audio_buffer, axis=0).flatten()
            audio_array = (audio_array / np.max(np.abs(audio_array))) * 32767  
            audio_array = audio_array.astype(np.int16) 

            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  
                wf.setframerate(self.sr)
                wf.writeframes(audio_array.tobytes())
            

            messagebox.showinfo("Download Complete", "Recording downloaded successfully!")
    











    ########################## Audio and Face Processing ###############################




    def process_audio(self):
        """
        Continuously retrieve and analyse audio chunks from the analysis queue.

        This function runs in a loop while recording is active or until all queued
        chunks have been processed. Each chunk is passed to `analyse_chunk()`.
        """
        while self.is_recording or not self.analysis_queue.empty():
            if not self.analysis_queue.empty():
                chunk = self.analysis_queue.get()
                self.analyse_chunk(chunk)


    def analyse_chunk(self, chunk):
        from AudioProcessor import AudioProcessor  
        processor = AudioProcessor()  
        sr = self.sr
        y = np.concatenate(chunk)

        frame_rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        avg_rms = np.mean(frame_rms)

        if avg_rms < self.silence_threshold:
            self.root.after(0, lambda: self.app.update_feedback_text(
                "Below the silence threshold, no analysis is being performed."
            ))
            return

        current_time = time.time()

        if current_time - self.last_update_time >= self.update_interval:
            # Process speech feedback first.
            full_feedback = processor.give_realtime_audio_feedback(y, sr)
            if isinstance(full_feedback, str):
                self.root.after(0, lambda: self.app.update_feedback_text(full_feedback))

            # Process face analysis feedback using the stored webcam frame.
            if self.current_webcam_frame is not None and hasattr(self, 'face_analyser'):
                try:
                    face_data = self.face_analyser.analyse_single_frame(self.current_webcam_frame)
                    print("🧠 Face data:", face_data)
                    print("📷 Current frame shape:", self.current_webcam_frame.shape)
                    if face_data:
                        summary = []
                        for face in face_data:
                            emotion = face['emotion']
                            state = face['state']
                            engagement = face['engagement']
                            summary.append(f"{emotion} ({state}), {engagement}%")
                        face_feedback = "Face Engagement: " + " | ".join(summary)
                        self.root.after(0, lambda: self.app.update_face_feedback_text(face_feedback))
                        print("✅ Updating GUI with:", face_feedback)
                except Exception as e:
                    print(f"Face analysis in analyse_chunk failed: {e}")
            else:
                print("No webcam frame available for face analysis or face_analyser not initialized.")

            # Process and update metric graphs for speech analysis.
            metrics = {
                "Loudness": processor.analyse_loudness(y, sr)[0],
                "Pitch": processor.analyse_pitch(y, sr)[0],
                "Speech Rate": processor.analyse_speech_rate(y, sr),
                "Energy": processor.analyse_vocal_energy(y, sr)
            }

            for metric, value in metrics.items():
                if isinstance(value, np.ndarray):
                    try:
                        metrics[metric] = float(np.mean(value))
                    except Exception as e:
                        print(f"Error converting {metric} to float: {e}")
                        metrics[metric] = 0.0

            thresholds = {
                "Loudness": (-30, -26),
                "Pitch": (1100, 1200),
                "Speech Rate": (20, 30),
                "Energy": (0.004, 0.005)
            }

            for metric, value in metrics.items():
                fig, ax, canvas = self.app.metric_graphs[metric]
                history_attr = f"{metric.lower()}_history"
                if not hasattr(self, history_attr):
                    setattr(self, history_attr, [])
                history = getattr(self, history_attr)
                history.append(value)
                if len(history) > 50:
                    history.pop(0)

                ax.clear()
                if len(history) > 3:
                    x = np.linspace(0, len(history) - 1, len(history))
                    x_smooth = np.linspace(x.min(), x.max(), 300)
                    y_smooth = make_interp_spline(x, history)(x_smooth)
                    ax.plot(x_smooth, y_smooth, color="black")
                else:
                    ax.plot(history, color="black")

                ax.set_xticks([])
                ax.set_yticks([])
                canvas.draw()

                low, high = thresholds[metric]
                color = "red" if value < low else "green" if value > high else "yellow"
                self.root.after(0, lambda m=metric, c=color: self.app.metric_labels[m].config(fg=c))

            self.last_update_time = current_time



