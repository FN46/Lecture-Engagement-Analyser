import unittest
import numpy as np
from RealTimeAudioAnalyser import RealTimeAudioAnalyser  


class TestAudioRecording(unittest.TestCase):
    def setUp(self):
        """Set up the test environment""" 
        self.real_time_processor = RealTimeAudioAnalyser()  
        self.real_time_processor.sr = 44100  
        self.real_time_processor.is_recording = False  
        self.real_time_processor.audio_buffer = []

    def test_start_recording(self):
        """Test that the start_recording method works correctly"""
        self.real_time_processor.start_recording()
        self.assertTrue(self.real_time_processor.is_recording)  

    def test_stop_recording(self):
        """Test that the stop_recording method stops recording"""
        self.real_time_processor.start_recording()
        self.real_time_processor.stop_recording()
        self.assertFalse(self.real_time_processor.is_recording)  

    def test_play_recording(self):
        """Test that play_recording plays the audio correctly"""
        self.real_time_processor.audio_buffer = [np.array([0.1, 0.2, 0.3])]
        self.real_time_processor.play_recording()
        self.assertEqual(self.real_time_processor.current_playback_index, 0) 

    def test_pause_playback(self):
        """Test that pause_playback correctly pauses the playback"""
        self.real_time_processor.audio_buffer = [np.array([0.1, 0.2, 0.3])]
        self.real_time_processor.play_recording()
        self.real_time_processor.pause_playback()
        self.assertTrue(self.real_time_processor.is_paused) 
        self.assertEqual(self.real_time_processor.current_playback_index, 0)  

    def test_resume_playback(self):
        """Test that resume_playback resumes from the correct position"""
        self.real_time_processor.audio_buffer = [np.array([0.1, 0.2, 0.3])]
        self.real_time_processor.current_playback_index = 1
        self.real_time_processor.resume_playback()
        self.assertFalse(self.real_time_processor.is_paused)  

    def test_seek_playback(self):
        """Test that seek_playback correctly seeks to a given position"""
        self.real_time_processor.audio_buffer = [np.array([0.1, 0.2, 0.3])]
        self.real_time_processor.seek_playback(1)
        self.assertEqual(self.real_time_processor.current_playback_index, 1) 

    def test_download_recording(self):
        """Test that download_recording works correctly"""
        self.real_time_processor.audio_buffer = [np.array([0.1, 0.2, 0.3])]
        self.real_time_processor.download_recording('test.wav')


    def test_process_audio(self):
        """Test that process_audio works correctly"""
        self.real_time_processor.is_recording = True
        self.real_time_processor.analysis_queue.put(np.array([0.1, 0.2, 0.3]))
        self.real_time_processor.process_audio()


    def test_analyse_chunk_with_silence(self):
        """Test that silence is handled properly in analyse_chunk"""
        self.real_time_processor.analyse_chunk(np.array([0.0, 0.0, 0.0]))



if __name__ == '__main__':
    unittest.main()
