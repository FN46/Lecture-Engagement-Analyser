import unittest
from unittest.mock import MagicMock, patch
from AudioAnalysisApp import AudioAnalysisApp
import tkinter as tk



class TestAudioAnalysisApp(unittest.TestCase): 


    def setUp(self, MockAudioProcessor, MockRealTimeAudioAnalyser):
        """Set up test case and mock dependencies."""
        # Create a root window mock object
        self.root = MagicMock(spec=tk.Tk)
        
        # Create the app instance
        self.app = AudioAnalysisApp(self.root)

        # Mock the AudioProcessor and RealTimeAudioAnalyser to avoid actual processing
        self.processor_mock = MockAudioProcessor.return_value
        self.analyser_mock = MockRealTimeAudioAnalyser.return_value


    def test_load_settings(self, mock_open, mock_exists):
        """Test if settings are loaded correctly from the config file."""
        # Mock os.path.exists to return True, simulating the presence of the config file
        mock_exists.return_value = True

        # Mock file reading (simulating the content of config.txt)
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.readlines.return_value = [
            "break_duration=10.0\n",
            "pitch_threshold=150.0\n",
        ]
        mock_open.return_value = mock_file

        # Call the load_settings method
        self.app.load_settings()

        # Check if the settings are updated correctly
        self.assertEqual(self.app.settings["break_duration"], 10.0)
        self.assertEqual(self.app.settings["pitch_threshold"], 150.0)

    def test_configure_window(self):
        """Test if the window is configured correctly."""
        self.app.configure_window()

        # Check if the window title and fullscreen attributes are set correctly
        self.root.title.assert_called_with("Speech Analysis Tool")
        self.root.attributes.assert_called_with('-fullscreen', True)

    def test_initialisation(self):
        """Test if the app initializes with correct attributes."""
        # Check if the processor and analyser are initialized correctly
        self.assertIsInstance(self.app.processor, MagicMock)
        self.assertIsInstance(self.app.analyser, MagicMock)
        self.assertFalse(self.app.is_recording)
        self.assertEqual(self.app.sr, 44100)

    def test_update_feedback_text(self):
        """Test if feedback text is updated correctly."""
        # Mock the feedback_text widget
        self.app.feedback_text = MagicMock()

        feedback = "Test feedback"
        self.app.update_feedback_text(feedback)

        # Check if the feedback_text widget was updated
        self.app.feedback_text.config.assert_called_with(state=tk.NORMAL)
        self.app.feedback_text.delete.assert_called_with(1.0, tk.END)
        self.app.feedback_text.insert.assert_called_with(tk.END, feedback + "\n")
        self.app.feedback_text.config.assert_called_with(state=tk.DISABLED)

    
    def test_create_main_menu(self, mock_create_button):
        """Test if the main menu is created correctly."""
        self.app.create_main_menu()

        # Check if the buttons were created
        mock_create_button.assert_called_with(self.root, 'Quit', self.app.quit_app, height=7, width=82)

    
    def test_start_analysis(self, mock_run_analysis):
        """Test if analysis starts in a separate thread."""
        # Mock the file entry widget
        self.app.file_entry = MagicMock()
        self.app.file_entry.get.return_value = "test_audio_file.wav"
        
        # Call start_analysis
        self.app.start_analysis()

        # Check if analysis was run in a separate thread
        mock_run_analysis.assert_called_with("test_audio_file.wav")

    
    def test_show_online_analysis(self, mock_show_online_analysis):
        """Test if the online analysis screen is displayed correctly."""
        self.app.show_online_analysis()

        # Check if the function to show online analysis was called
        mock_show_online_analysis.assert_called_once()


    def test_show_offline_analysis(self, mock_show_offline_analysis):
        """Test if the offline analysis screen is displayed correctly."""
        self.app.show_offline_analysis()

        # Check if the function to show offline analysis was called
        mock_show_offline_analysis.assert_called_once()


if __name__ == '__main__':
    unittest.main()
