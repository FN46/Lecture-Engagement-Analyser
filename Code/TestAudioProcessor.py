import unittest 
import numpy as np
from AudioProcessor import AudioProcessor

class TestAudioProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = AudioProcessor()
        self.sample_rate = 22050 
        self.test_signal = np.random.randn(self.sample_rate) 

    def test_analyse_loudness(self):
        loudness, feedback = self.processor.analyse_loudness(self.test_signal, self.sample_rate)
        self.assertIsInstance(loudness, float)
        self.assertTrue(any(word in feedback.lower() for word in ["loud", "quiet", "balanced"]))

    def test_analysis_pitch(self):
        pitch, pitch_values = self.processor.analyse_pitch(self.test_signal, self.sample_rate)
        self.assertIsInstance(pitch, float)
        self.assertGreaterEqual(pitch, 0)

    def test_analyse_speech_rate(self):
        speech_rate = self.processor.analyse_speech_rate(self.test_signal, self.sample_rate)
        self.assertIsInstance(speech_rate, float)
        self.assertGreater(speech_rate, 0)

    def test_analyse_vocal_energy(self):
        energy = self.processor.analyse_vocal_energy(self.test_signal, self.sample_rate)
        self.assertIsInstance(energy, float)
        self.assertGreaterEqual(energy, 0)

if __name__ == "__main__":
    unittest.main()
