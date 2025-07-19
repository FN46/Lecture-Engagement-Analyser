import os
import librosa
import numpy as np
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import librosa.display
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from AudioProcessor import AudioProcessor
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class PlotManager:
    def __init__(self, y, sr, graph_frame, selected_graph, settings=None):
        """
        Initialises the PlotManager with audio data, sample rate, and GUI references.
        """
        self.y = y
        self.sr = sr
        self.graph_frame = graph_frame
        self.selected_graph = selected_graph
        self.canvas = None
        
        if not hasattr(PlotManager, "_global_settings"):
            PlotManager._global_settings = settings if settings is not None else {}
        self.settings = PlotManager._global_settings
        
        
    def update_settings(self, new_settings):
        """Update the global settings and ensure all instances use the updated settings."""
        PlotManager._global_settings.update(new_settings)
        self.settings = PlotManager._global_settings


    def plot_graph_in_thread(self):
        """
        Schedules the plotting to be done on the main thread using `Tk.after`.
        """
        self.graph_frame.after(0, self.plot_graph)


    def plot_selected_graph(self):
        """
        Clears previous plots and plots the selected graph type for the loaded audio file.
        """
        file_path = self.file_entry.get()
        
        if not self.file_exists(file_path):
            messagebox.showerror("Error", "File does not exist!")
            return

        audio, sample_rate = AudioProcessor.load_audio_file(file_path)
        
        if audio is None or sample_rate is None:
            return

        self.clear_canvas()
        graph_type = self.selected_graph_type.get()
        self.plot_graph_type(graph_type, audio, sample_rate)
        
        
    def plot_graph(self):
        """
        Handles the plotting of the selected graph type on the main thread.
        """
        self.clear_graph_frame()
        if self.selected_graph == "Waveform":
            self.plot_waveform()
        elif self.selected_graph == "Mel Spectrogram":
            self.plot_mel_spectrogram()
        elif self.selected_graph == "Fourier Transform":
            self.plot_fourier_transform()
        elif self.selected_graph == "Loudness and Pauses Over Time":
            self.plot_loudness_pauses()




    ########################## Individual Plotting Functions ###############################

    def plot_waveform(self):
        fig, ax = plt.subplots(figsize=(6, 1.5))
        ax.plot(np.linspace(0, len(self.y) / self.sr, len(self.y)), self.y)
        ax.set_title("Waveform", fontsize=8)
        ax.set_xlabel("Time (s)", fontsize=7)
        ax.set_ylabel("Amplitude", fontsize=7)
        ax.tick_params(axis='both', labelsize=6)
        self.display_and_save_plot(fig, "waveform")


    def plot_mel_spectrogram(self):
        fig, ax = plt.subplots(figsize=(6, 1.5))
        mel_spectrogram = librosa.feature.melspectrogram(y=self.y, sr=self.sr, n_mels=128)
        mel_spectrogram_db = librosa.power_to_db(mel_spectrogram, ref=np.max)
        img = librosa.display.specshow(mel_spectrogram_db, sr=self.sr, x_axis='time', y_axis='mel', ax=ax)
        fig.colorbar(img, ax=ax, format='%+2.0f dB').ax.tick_params(labelsize=6)
        ax.set_title("Mel Spectrogram", fontsize=8)
        ax.set_xlabel("Time (s)", fontsize=7)
        ax.set_ylabel("Mel Frequency", fontsize=7)
        ax.tick_params(axis='both', labelsize=6)
        self.display_and_save_plot(fig, "mel_spectrogram")


    def plot_fourier_transform(self):
        fig, ax = plt.subplots(figsize=(6, 1.5))
        fft = np.fft.fft(self.y)
        magnitude = np.abs(fft)
        frequency = np.fft.fftfreq(len(magnitude), 1 / self.sr)
        ax.plot(frequency[:len(frequency) // 2], magnitude[:len(magnitude) // 2])
        ax.set_title("Fourier Transform", fontsize=8)
        ax.set_xlabel("Frequency (Hz)", fontsize=7)
        ax.set_ylabel("Magnitude", fontsize=7)
        ax.tick_params(axis='both', labelsize=6)
        self.display_and_save_plot(fig, "fourier_transform")


    def plot_loudness_pauses(self, pause_threshold_factor=0.2):
        min_pause_duration = self.settings.get("pause_duration", 0.5)
        break_duration = self.settings.get("break_duration", 7.0)

        rms = librosa.feature.rms(y=self.y)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=self.sr)
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)

        fig, ax = plt.subplots(figsize=(6, 1.5))
        ax.plot(times, rms_db, label="Loudness (dB)", color="blue")

        pause_threshold = np.mean(rms) * pause_threshold_factor
        pause_indices = rms < pause_threshold
        pause_start = None

        for i, is_pause in enumerate(pause_indices):
            if is_pause and pause_start is None:
                pause_start = times[i]
            elif not is_pause and pause_start is not None:
                pause_duration = times[i] - pause_start
                if pause_duration >= min_pause_duration:
                    color = "red" if pause_duration >= break_duration else "orange"
                    ax.axvspan(pause_start, times[i], color=color, alpha=0.3)
                pause_start = None

        if pause_start is not None:
            pause_duration = times[-1] - pause_start
            if pause_duration >= min_pause_duration:
                color = "red" if pause_duration >= break_duration else "orange"
                ax.axvspan(pause_start, times[-1], color=color, alpha=0.3)

        ax.set_title("Loudness and Pauses Over Time", fontsize=8)
        ax.set_xlabel("Time (s)", fontsize=7)
        ax.set_ylabel("Loudness (dB)", fontsize=7)
        ax.tick_params(axis='both', labelsize=6)
        ax.legend(["Loudness (dB)", "Pause", "Break"], fontsize=6)
        
        self.display_and_save_plot(fig, "loudness_pauses")



    
    
    
    
    ########################## Helper Functions ###############################



    def plot_graph_type(self, graph_type, audio, sample_rate):
        """
        Plots the graph based on the selected graph type.
        """
        plot_functions = {
            "Waveform": self.plot_waveform,
            "Mel Spectrogram": self.plot_mel_spectrogram,
            "Fourier Transform": self.plot_fourier_transform,
            "Loudness and Pauses Over Time": self.plot_loudness_pauses,
        }
        plot_function = plot_functions.get(graph_type)
        if plot_function:
            plot_function(audio, sample_rate)


    def display_and_save_plot(self, fig, filename):
        """
        Displays the plot in the Tkinter frame and saves it as an image in the current directory.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, filename)
        self.display_plot(fig)
        fig.savefig(file_path, bbox_inches='tight')
        
        plt.close(fig)

    def display_plot(self, fig):
        """
        Embeds the plot in the Tkinter graph_frame and shrinks the navigation toolbar.
        """
        self.clear_graph_frame()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        
        self.canvas = canvas

    def clear_graph_frame(self):
        """
        Clears the graph frame of any existing plots or widgets.
        """
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

    def clear_canvas(self):
        """
        Clears any existing plot from the graph frame.
        """
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

    def _compute_rms(self, audio, sample_rate):
        """
        Computes RMS and converts it to dB over time for loudness analysis.
        """
        rms = librosa.feature.rms(y=audio)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sample_rate)
        return rms, rms_db, times


    def add_legend(self, ax):
        """
        Adds a legend to the plot, consolidating labels to avoid duplicates.
        """
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc="upper right")

    def file_exists(self, file_path):
        """
        Checks if the provided file path exists.
        """
        return os.path.exists(file_path)
