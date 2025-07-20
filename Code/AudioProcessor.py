import os
import librosa
import numpy as np
import tkinter as tk
import math
from AudioAnalysisApp import AudioAnalysisApp
import librosa
import numpy as np





class AudioProcessor:
    
    def __init__(self, settings=None):
        """
        Initialise the AudioProcessor with optional global settings.

        Parameters:
        - settings (dict, optional): Configuration dictionary for global settings.
        """
        self.engagement_score = 0
        
        if not hasattr(AudioProcessor, "_global_settings"):
            AudioProcessor._global_settings = settings if settings is not None else {}
        self.settings = AudioProcessor._global_settings

    def update_settings(self, new_settings):
        """
        Update and apply global settings to all AudioProcessor instances.

        Parameters:
        - new_settings (dict): Dictionary of new settings to merge with the existing ones.
        """
        AudioProcessor._global_settings.update(new_settings)
        self.settings = AudioProcessor._global_settings
    
    def reset_engagement_score(self):
        """
        Reset the internal engagement score to zero.
        """
        self.engagement_score = 0






    ########################## Audio Processing ###############################


    def noise_suppression(self, audio, sr, noise_suppression_factor=0.15):
        """
        Apply simple noise suppression using spectral gating.

        Parameters:
        - audio (np.ndarray): Audio signal (1D array).
        - sr (int): Sample rate of the audio.
        - noise_suppression_factor (float): Scaling factor for noise threshold (default 0.15).

        Returns:
        - np.ndarray: Denoised audio signal.
        """
        noise_suppression_factor = 0.15 if noise_suppression_factor is None else noise_suppression_factor
            
        stft = librosa.stft(audio)
        magnitude, phase = librosa.magphase(stft)
        noise_profile = np.mean(magnitude[:, :int(sr)], axis=1)
        noise_threshold = noise_profile * noise_suppression_factor
        noise_reduced_magnitude = np.maximum(magnitude - noise_threshold[:, np.newaxis], 0)
        cleaned_stft = noise_reduced_magnitude * phase
        cleaned_audio = librosa.istft(cleaned_stft).astype(np.float32)
        return cleaned_audio


    @staticmethod
    def load_audio_file(file_path, noise_suppression_factor=0.15):
        """
        Load an audio file from disk, optionally applying noise suppression.

        Parameters:
        - file_path (str): Path to the audio file.
        - noise_suppression_factor (float): Strength of noise suppression (default 0.15).

        Returns:
        - Tuple[np.ndarray, int]: Tuple of audio chunks and sample rate,
          or (None, None) if loading fails.
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            y, sr = librosa.load(file_path, sr=None, dtype=np.float32)

            if not isinstance(y, np.ndarray) or y.ndim != 1:
                raise ValueError("Invalid audio data format. Expected a numerical 1D NumPy array.")


            if noise_suppression_factor > 0:
                y = AudioProcessor().noise_suppression(y, sr, noise_suppression_factor)

            audio_chunks, _ = AudioProcessor.load_audio_in_chunks(y, sr=sr)
        
            return audio_chunks, sr

        except Exception as e:
            print(f"Error while loading file: {e}")
            return None, None


        
    @staticmethod
    def load_audio_in_chunks(filename, chunk_size=10.0, sr=None):
        """
        Split an audio signal or file into chunks of fixed duration.

        Parameters:
        - filename (Union[str, np.ndarray]): Audio file path or preloaded 1D NumPy array.
        - chunk_size (float): Duration of each chunk in seconds.
        - sr (int): Sample rate (required if input is a NumPy array).

        Returns:
        - Tuple[np.ndarray, int]: Tuple of concatenated audio chunks and sample rate,
          or (None, None) if loading fails.
        """
        try:
            if isinstance(filename, str):
                y, sr = librosa.load(filename, sr=sr)
            elif isinstance(filename, np.ndarray): 
                if sr is None:
                    raise ValueError("Sampling rate (sr) must be provided for numpy arrays.")
                y = filename
            else:
                raise ValueError("Invalid input: Must be a file path or a 1D numpy array.")

            if not isinstance(y, np.ndarray) or y.ndim != 1:
                raise ValueError("Input audio must be a 1D numpy array.")

            total_duration = len(y) / sr
            num_chunks = math.floor(total_duration / chunk_size)

            chunk_samples = int(chunk_size * sr)
            chunks = [y[i * chunk_samples:(i + 1) * chunk_samples] for i in range(num_chunks)]

            final_chunk = y[num_chunks * chunk_samples:]
            if len(final_chunk) > 0:
                chunks.append(final_chunk)

            chunks = [np.atleast_1d(chunk) for chunk in chunks]

            return np.concatenate(chunks), sr
        except Exception as e:
            print(f"Error loading audio in chunks: {e}")
            return None, None









    ########################## Analysis ###############################

    def analyse_loudness(self, y, sr):
        """
        Analyse the average loudness of the audio signal and provide qualitative feedback.

        Parameters:
        - y (np.ndarray): Audio time series.
        - sr (int): Sampling rate of the audio.

        Returns:
        - Tuple[float, str]: Average loudness in dB and a qualitative feedback string.
        """
        rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=512)[0]
        avg_loudness = np.mean(librosa.amplitude_to_db(rms, ref=np.max))

        threshold = self.settings.get("loudness_threshold", -25.0)

        if avg_loudness > threshold + 8:
            feedback = f"Loud: {avg_loudness:.2f} dB"
        elif avg_loudness < threshold - 8:
            feedback = f"Quiet: {avg_loudness:.2f} dB"
        else:
            feedback = f"Balanced: {avg_loudness:.2f} dB"
        return float(avg_loudness), feedback


    def analyse_pauses(self, y, sr):
        """
        Detect pauses and breaks in the speech based on RMS energy levels.

        Parameters:
        - y (np.ndarray): Audio time series.
        - sr (int): Sampling rate of the audio.

        Returns:
        - Tuple[int, float, str]: Number of pauses, total duration of pauses in seconds, and feedback string.
        """
        min_pause_duration = self.settings.get("pause_duration", 0.3)
        break_duration = self.settings.get("break_duration", 7.0)
        pause_threshold = self.settings.get("pause_threshold_value", 0.001)


        rms = librosa.feature.rms(y=y)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
        frame_duration = times[1] - times[0]
        frame_duration = max(frame_duration, 0.01)

        min_pause_frames = int(min_pause_duration / frame_duration)
        break_frames = int(break_duration / frame_duration)

        pauses = []
        breaks = []
        pause_start = None
        count = 0

        for i, value in enumerate(rms):
            if value < pause_threshold:
                if pause_start is None:
                    pause_start = times[i]
                    count = 1
                else:
                    count += 1
            else:
                if pause_start is not None and count >= min_pause_frames:
                    pause_end = times[i]
                    pause_duration = pause_end - pause_start
                    if count >= break_frames:
                        breaks.append((pause_start, pause_end, pause_duration))
                    else:
                        pauses.append((pause_start, pause_end, pause_duration))
                pause_start = None
                count = 0

        if pause_start is not None and count >= min_pause_frames:
            pause_end = times[-1]
            pause_duration = pause_end - pause_start
            if count >= break_frames:
                breaks.append((pause_start, pause_end, pause_duration))
            else:
                pauses.append((pause_start, pause_end, pause_duration))

        total_pause_time = sum([p[2] for p in pauses])
        feedback = f"Detected {len(pauses)} pauses (total {total_pause_time:.2f} sec) and {len(breaks)} breaks."

        return len(pauses), total_pause_time, feedback


    def analyse_pitch(self, y, sr):
        """
        Estimate average pitch from the audio using pitch tracking.

        Parameters:
        - y (np.ndarray): Audio signal.
        - sr (int): Sample rate.

        Returns:
        - Tuple[float, np.ndarray]: Average pitch and array of pitch values.
        """
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[magnitudes > np.median(magnitudes)]

        if len(pitch_values) == 0:
            return 0, np.array([])
        avg_pitch = np.mean(pitch_values)
        return avg_pitch, pitch_values


    def analyse_prosody(self, y, sr):
        """
        Analyse prosody characteristics: average and variability of pitch.

        Parameters:
        - y (np.ndarray): Audio signal.
        - sr (int): Sample rate.

        Returns:
        - Tuple[float, float]: Mean and standard deviation of pitch values.
        """
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[magnitudes > np.median(magnitudes)]
        
        return np.mean(pitch_values), np.std(pitch_values)


    def analyse_speech_rate(self, y, sr):
        """
        Estimate the speech rate based on zero-crossing rate features.

        Parameters:
        - y (np.ndarray): Audio signal.
        - sr (int): Sample rate.

        Returns:
        - float: Estimated speech rate (units: speech frames per second).
        """
        zcr = librosa.feature.zero_crossing_rate(y, frame_length=2048, hop_length=512)[0]
        threshold = np.mean(zcr) + 0.005
        speech_frames = np.sum(zcr > threshold)
        duration = librosa.get_duration(y=y, sr=sr)
        speech_rate = speech_frames / duration if duration > 0 else 0.0

        return speech_rate



    def analyse_vocal_energy(self, y, sr):
        """
        Compute the average vocal energy of the audio using RMS.

        Parameters:
        - y (np.ndarray): Audio signal.
        - sr (int): Sample rate.

        Returns:
        - float: Mean RMS value representing vocal energy.
        """
        rms = librosa.feature.rms(y=y)[0]

        return float(np.mean(rms))


    def analyse_monotony(self, y, sr):
        """
        Assess monotony in speech based on pitch variability.

        Parameters:
        - y (np.ndarray): Audio signal.
        - sr (int): Sample rate.

        Returns:
        - str: Qualitative assessment of pitch monotony.
        """
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[magnitudes > np.median(magnitudes)]
        pitch_values = pitch_values[(pitch_values > 50) & (pitch_values < 500)]

        if len(pitch_values) == 0:
            return "Monotony: No valid pitch"

        pitch_std = np.std(pitch_values)
        avg_pitch = np.mean(pitch_values)
        threshold = max(0.05 * avg_pitch, 10)

        if pitch_std < threshold:
            return "Monotony: Low variation"
        return "Monotony: Good variation"


    
    
    
    
    

    ########################## Feedback ###############################

    def give_audio_feedback(self, y, sr):
        """
        Run a full suite of audio analyses and generate structured feedback and improvement advice.

        Parameters:
        - y (np.ndarray): Audio time series.
        - sr (int): Sampling rate of the audio.

        Returns:
        - str: Combined analysis results and tailored advice as a single formatted string.
        """
        try:
            self.reset_engagement_score()
            
            avg_loudness, loudness_feedback = self.analyse_loudness(y, sr)
            pause_count, avg_pause_duration, pause_feedback = self.analyse_pauses(y, sr)
            avg_pitch, pitch_values = self.analyse_pitch(y, sr)
            avg_prosody, pitch_variation = self.analyse_prosody(y, sr)
            speech_rate = self.analyse_speech_rate(y, sr)
            avg_energy = self.analyse_vocal_energy(y, sr)
            monotony_feedback = self.analyse_monotony(y, sr)

            feedback = (
                f"Loudness Analysis:\n{loudness_feedback}\n\n"
                f"Pause Analysis:\n{pause_feedback}\n\n"
                f"Pitch Analysis:\nAverage Pitch: {avg_pitch:.2f} Hz\n\n"
                f"Prosody Analysis:\nMean Pitch: {avg_prosody:.2f} Hz, Variation: {pitch_variation:.2f}\n\n"
                f"Speech Rate Analysis:\nSpeech Rate: {speech_rate:.2f} syllables/second\n\n"
                f"Vocal Energy Analysis:\nAverage Vocal Energy: {avg_energy:.2f}\n\n"
                f"Monotony Analysis:\n{monotony_feedback}\n\n"
            )

            advice = self.generate_advice(avg_loudness, pause_count, avg_pause_duration, avg_pitch, pitch_variation, speech_rate, avg_energy, monotony_feedback)
            
            return feedback + advice
        except MemoryError:
            print("Memory issue while plotting Fourier Transform. Try using a smaller sample size.")
        except Exception as e:
            print("An error occurred while plotting feedback", e)
            

    def generate_advice(self, avg_loudness, pause_count, avg_pause_duration, avg_pitch, pitch_variation, speech_rate, avg_energy, monotony_feedback):
        """
        Generate improvement advice based on audio analysis metrics.

        Parameters:
        - avg_loudness (float): Average loudness in dB.
        - pause_count (int): Number of detected pauses.
        - avg_pause_duration (float): Total duration of pauses.
        - avg_pitch (float): Average pitch in Hz.
        - pitch_variation (float): Standard deviation of pitch.
        - speech_rate (float): Estimated speech rate.
        - avg_energy (float): Average RMS vocal energy.
        - monotony_feedback (str): Result from monotony analysis.

        Returns:
        - str: Tailored advice string based on analysis outcomes.
        """
        advice = "\n\nAdvice:\n"
        score = 0

        # Loudness
        if avg_loudness > -20:
            advice += "Your speech is quite loud. Consider lowering your volume or moving slightly away from the microphone.\n\n"
        elif avg_loudness < -40:
            advice += "Your speech is very quiet. Try increasing your volume or moving closer to the microphone.\n\n"
        else:
            advice += "Your loudness is well-balanced. Keep it up!\n\n"
            score += 16.7

        # Pauses
        if pause_count == 0:
            advice += "Consider adding pauses to give your listeners time to absorb key points.\n\n"
        elif avg_pause_duration < 0.3:
            advice += "You have frequent short pauses. Try linking thoughts more fluidly.\n\n"
        elif avg_pause_duration > 1.5:
            advice += "Some pauses may be too long. Try reducing long pauses to keep the listener engaged.\n\n"
        else:
            advice += "Your pause length is balanced. Keep incorporating pauses naturally.\n\n"
            score += 16.7

        # Pitch / variation
        if avg_pitch < 100:
            advice += "Your pitch is relatively low, which could indicate monotony. Try varying your pitch to engage listeners more effectively.\n\n"
        elif pitch_variation < 10:
            advice += "Your speech pitch variation is quite low. Aim for more dynamic shifts in pitch to keep the audience engaged.\n\n"
        else:
            advice += "Your pitch variation is good. Keep using that dynamic range to maintain listener interest.\n\n"
            score += 16.7

        # Speech rate
        if speech_rate < 2.0:
            advice += "Your speech rate is a bit slow. Consider speeding up slightly to maintain energy in your delivery.\n\n"
        elif speech_rate > 4.0:
            advice += "Your speech rate is quite fast. You might want to slow down to allow your audience to follow better.\n\n"
        else:
            advice += "Your speech rate is well balanced. Keep it up!\n\n"
            score += 16.7

        # Energy
        if avg_energy < 0.05:
            advice += "The vocal energy is quite low. Try to put more emphasis into your speech for a stronger delivery.\n\n"
        elif avg_energy > 0.15:
            advice += "Your vocal energy is quite high, which is great for engagement, but be mindful not to tire yourself out.\n\n"
        else:
            advice += "Your vocal energy is balanced. Continue maintaining this level for a clear and engaging delivery.\n\n"
            score += 16.7

        # Monotony
        if 'Monotony: Monotonous speech detected' in monotony_feedback:
            advice += "Your speech might sound monotonous. Varying your pitch and speed can add more emotion and keep the audience's attention.\n\n"
        else:
            advice += "Your speech has a good variation in tone, making it engaging for listeners. Keep it up!\n\n"
            score += 16.7

        self.engagement_score = round(score, 1)
        return advice

    
    
    
    
    def give_realtime_audio_feedback(self, y, sr):
        """
        Provide streamlined, real-time feedback on vocal delivery aspects.

        Parameters:
        - y (np.ndarray): Audio signal for a short segment.
        - sr (int): Sampling rate.

        Returns:
        - str: Real-time advice string based on current speaking metrics.
        """
        try:
            avg_loudness, loudness_feedback = self.analyse_loudness(y, sr)
            avg_prosody, pitch_variation = self.analyse_prosody(y, sr)
            speech_rate = self.analyse_speech_rate(y, sr)
            avg_energy = self.analyse_vocal_energy(y, sr)

            advice = self.generate_realtime_advice(avg_loudness, pitch_variation, speech_rate, avg_energy)
            return advice or "No feedback available for this segment."
        
        except MemoryError:
            print("Memory issue while plotting Fourier Transform. Try using a smaller sample size.")
        except Exception as e:
            print("An error occurred while plotting feedback", e)
    
    
        
    def generate_realtime_advice(self, avg_loudness, pitch_variation, speech_rate, avg_energy):
        """
        Generate simplified real-time speaking advice based on core metrics.

        Parameters:
        - avg_loudness (float): Average loudness in dB.
        - pitch_variation (float): Pitch standard deviation.
        - speech_rate (float): Estimated speech rate.
        - avg_energy (float): Average vocal energy.

        Returns:
        - str: Quick feedback on volume, pitch, speed, and energy.
        """
        advice = ""
        score = 0

        if avg_loudness > 0:
            advice += "Volume: Too loud, try backing away.\n\n\n"
        elif avg_loudness < -30:
            advice += "Volume: Too quiet, speak up a bit.\n\n\n"
        else:
            advice += "Volume: Just right.\n\n\n"
            score += 1

        if pitch_variation < 900:
            advice += "Pitch: Add more variation.\n\n\n"
        else:
            advice += "Pitch: Good variation.\n\n\n"
            score += 1
            
        if speech_rate < 24.0:
            advice += "Speed: Speak a little faster.\n\n\n"
        elif speech_rate > 50.0:
            advice += "Speed: Slow down slightly.\n\n\n"
        else:
            advice += "Speed: Balanced.\n\n\n"
            score += 1

            
        if avg_energy < 0.004:
            advice += "Energy: Be more expressive.\n\n\n"
        elif avg_energy > 0.015:
            advice += "Energy: High — keep it up!\n\n\n"
            score += 2
        else:
            advice += "Energy: Well balanced.\n\n\n"
            score += 1
            

        if score >= 4:
            advice += f"Engagement: You're being engaging!\n\n\n"
        elif score >= 2:
            advice += f"Engagement: You're being somewhat engaging.\n\n\n"
        else:
            advice += f"Engagement: You're being less engaging.\n\n\n"
        
        return advice



    def run_gui(self):
        """
        Initialise and run the Tkinter-based GUI for audio analysis.
        """
        root = tk.Tk()
        app = AudioAnalysisApp(root)
        root.mainloop()


if __name__ == "__main__":
    app = AudioProcessor()
    app.run_gui()