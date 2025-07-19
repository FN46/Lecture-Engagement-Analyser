import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD  
from RealTimeAudioAnalyser import RealTimeAudioAnalyser
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import matplotlib.pyplot as plt
import numpy as numpy
from PIL import Image, ImageTk
import cv2




class AudioAnalysisApp:
    def __init__(self, root):
        """
        Initialise the Audio Analysis Tool GUI.

        - Sets the main window (`root`) reference.
        - Configures the window, sets up styles, and builds the main menu.
        - Loads user-defined settings from a config file.
        - Instantiates the AudioProcessor and RealTimeAudioAnalyser for processing and feedback.
        """
        from AudioProcessor import AudioProcessor
        from RealTimeAudioAnalyser import RealTimeAudioAnalyser

        self.root = root
        self.configure_window()
        self.initialise_styles()
        self.create_main_menu()
        self.load_settings()

        self.processor = AudioProcessor(self.settings)
        self.analyser = RealTimeAudioAnalyser(self.root, self)

        self.face_analyser = None
        self.video_capture = None




    def load_settings(self):
        """
        Load audio analysis parameters from the config file.

        - Defines default values for key analysis parameters like pause thresholds, loudness, etc.
        - Tries to load overrides from 'config.txt' located in the ConfigFolder.
        - If found, replaces the default settings with values from the file.
        """
        
        self.settings = {
            "break_duration": 5.0,
            "pause_duration": 0.15,
            "loudness_threshold": -25.0,
            "pause_threshold_value": 0.001,
            "update_interval": 5.0,
            "silence_threshold": 0.012,
        }

        config_path = os.path.join("Code", "ConfigFolder", "config.txt")
        if os.path.exists(config_path):
            with open(config_path, "r") as file:
                for line in file:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if key in self.settings:
                            self.settings[key] = float(value)
        else:
            print("Config file not found")









    ########################## MENU PAGES ###############################
    
    
    
    
    ########################## Main Menu ###############################
    def create_main_menu(self):
        """
        Create the main application menu.

        - Clears the current UI and draws a centered menu with buttons for:
            - Real-Time Analysis
            - Batch Analysis
            - Settings
            - Help
            - Quit
        - Buttons are placed in a grid layout within a centered frame.
        """
        self.clear_window()

        menu_frame = tk.Frame(self.root, bg=self.colors["background"])
        menu_frame.pack(fill=tk.BOTH, expand=True)

        menu_inner_frame = tk.Frame(menu_frame, bg=self.colors["background"])
        menu_inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        menu_inner_frame.columnconfigure(0, weight=1)
        menu_inner_frame.columnconfigure(1, weight=1)
        menu_inner_frame.rowconfigure(0, weight=1)
        menu_inner_frame.rowconfigure(1, weight=1)
        menu_inner_frame.rowconfigure(2, weight=1)
        
        self.create_button(menu_inner_frame, "Real-Time Analysis", self.realtime_analysis_menu).grid(
            row=0, column=0, padx=30, pady=30, sticky="nsew"
        )
        self.create_button(menu_inner_frame, "Batch Analysis", self.batch_analysis_menu).grid(
            row=0, column=1, padx=30, pady=30, sticky="nsew"
        )
        self.create_button(menu_inner_frame, "Settings", self.settings_page).grid(
            row=1, column=0, padx=30, pady=30, sticky="nsew"
        )
        self.create_button(menu_inner_frame, "Help", self.help_page).grid(
            row=1, column=1, padx=30, pady=30, sticky="nsew"
        )
        self.create_button(menu_inner_frame, "Quit", self.quit_app).grid(
            row=2, column=0, padx=30, pady=30, sticky="nsew", columnspan=2
        )
    
    
    
    
    
    
    
    ########################## Real-time analysis ###############################
    
    

    def realtime_analysis_menu(self):
        from FaceAnalysis import FaceAnalysis
        self.face_analyser = FaceAnalysis()

        self.clear_window()
        self.create_header("Real-Time Analysis")

        container = tk.Frame(self.root, bg=self.colors["background"])
        container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container, bg=self.colors["background"])
        canvas.pack(side="left", fill="both", expand=True)

        content_frame = tk.Frame(canvas, bg=self.colors["background"])
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        left_frame = tk.Frame(content_frame, bg=self.colors["background"])
        left_frame.pack(side=tk.LEFT, padx=20, pady=10, fill="y")

        self.metric_labels = {}
        self.metric_graphs = {}
        metrics = ["Loudness", "Pitch", "Speech Rate", "Energy"]
        for metric in metrics:
            frame = tk.Frame(left_frame, bg=self.colors["background"])
            frame.pack(pady=5, fill="x")
            label = tk.Label(frame, text=metric, font=("Arial", 12, "bold"), bg=self.colors["background"], fg=self.colors["label"])
            label.pack()
            indicator = tk.Label(frame, text="●", font=("Arial", 20), fg="gray", bg=self.colors["background"])
            indicator.pack()
            fig, ax = plt.subplots(figsize=(4, 1.4), facecolor=self.colors["background"])
            ax.set_facecolor(self.colors["background"])
            ax.axis('off')
            ax.plot(numpy.linspace(0, 10, 100), numpy.sin(numpy.linspace(0, 10, 100)), color="black")
            canvas_graph = FigureCanvasTkAgg(fig, master=frame)
            canvas_graph.get_tk_widget().pack(pady=5, padx=10)
            canvas_graph.draw()
            self.metric_labels[metric] = indicator
            self.metric_graphs[metric] = (fig, ax, canvas_graph)

        right_frame = tk.Frame(content_frame, bg=self.colors["background"])
        right_frame.pack(side=tk.RIGHT, padx=10, pady=0, fill="y")

        self.create_section_header("Video Feed").pack(in_=right_frame)
        video_frame = tk.Frame(right_frame, bg=self.colors["background"])
        video_frame.pack(fill="both", expand=False)

        self.video_label = tk.Label(video_frame)
        self.video_label.pack(expand=True, fill="both")

        self.face_feedback_label = tk.Label(
            content_frame,
            text="Face Engagement: ",
            font=("Arial", 10),
            bg=self.colors["background"],
            fg="white"
        )
        self.face_feedback_label.pack(pady=5)

        self.feedback_text = tk.Text(
            content_frame,
            height=20,
            width=30,
            bg=self.colors["text_bg"],
            fg=self.colors["text_fg"],
            font=("Lexend", 12, "bold"),
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
        )
        self.feedback_text.pack(pady=15)

        # Start webcam 
        self.init_webcam()
        self.update_webcam_feed()
        self.current_webcam_frame = None  # Store the latest frame


        # CONTROL BUTTONS
        control_frame = tk.Frame(content_frame, bg=self.colors["background"])
        control_frame.pack(pady=12)

        # Group 1: Recording Controls
        record_frame = tk.Frame(control_frame, bg=self.colors["background"])
        record_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(record_frame, text="Recording", bg=self.colors["background"], fg="white", font=("Arial", 10, "bold")).pack()
        self.create_button(record_frame, "Start Recording", self.analyser.start_recording).pack(pady=3, fill="x")
        self.create_button(record_frame, "Stop Recording", self.analyser.stop_recording).pack(pady=3, fill="x")

        # Group 2: Playback Controls
        playback_frame = tk.Frame(control_frame, bg=self.colors["background"])
        playback_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(playback_frame, text="Playback", bg=self.colors["background"], fg="white", font=("Arial", 10, "bold")).pack()
        self.create_button(playback_frame, "Play", self.analyser.play_recording).pack(pady=3, fill="x")
        self.create_button(playback_frame, "Pause", self.analyser.pause_playback).pack(pady=3, fill="x")
        self.create_button(playback_frame, "Resume", self.analyser.resume_playback).pack(pady=3, fill="x")

        # Group 3: Seek Controls
        seek_frame = tk.Frame(control_frame, bg=self.colors["background"])
        seek_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(seek_frame, text="Seek", bg=self.colors["background"], fg="white", font=("Arial", 10, "bold")).pack()
        self.create_button(seek_frame, "15s Back", lambda: self.analyser.seek_playback(-15)).pack(pady=3, fill="x")
        self.create_button(seek_frame, "15s Forward", lambda: self.analyser.seek_playback(15)).pack(pady=3, fill="x")

        # Group 4: Download/Quit
        misc_frame = tk.Frame(control_frame, bg=self.colors["background"])
        misc_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(misc_frame, text="Other", bg=self.colors["background"], fg="white", font=("Arial", 10, "bold")).pack()
        self.create_button(misc_frame, "Download WAV", lambda: self.analyser.download_recording("recording.wav")).pack(pady=3, fill="x")
        self.create_button(misc_frame, "Back to Menu", self.create_main_menu).pack(pady=3, fill="x")

        
    
    def init_webcam(self):
        """
        Initializes the webcam using DirectShow backend to avoid MSMF errors.
        """
        import cv2
        self.video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.video_capture.isOpened():
            print("Error: Could not access the webcam.")
            self.video_capture = None
    

    def update_webcam_feed(self):
        """
        Continuously fetch and display raw webcam frames (no annotations).
        """
        import cv2
        from PIL import Image, ImageTk

        if self.video_capture and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)

                self.video_label.config(image=imgtk)
                self.video_label.image = imgtk  # prevent GC

                # Store the current frame for external access (in analyse_chunk)
                self.current_webcam_frame = frame

        self.root.after(30, self.update_webcam_feed)


            

    def update_feedback_text(self, feedback):
        """
        Replaces the feedback text box contents with new feedback.
        """
        if hasattr(self, 'feedback_text'):
            self.feedback_text.config(state=tk.NORMAL)
            self.feedback_text.delete(1.0, tk.END)     
            self.feedback_text.insert(tk.END, feedback + "\n")  
            self.feedback_text.see(tk.END)              
            self.feedback_text.config(state=tk.DISABLED)  
        else:
            print("Warning: feedback_text not initialized in AudioAnalysisApp")





    ########################## Offline Batch Analysis ###############################



    def batch_analysis_menu(self):
        """
        Display the offline batch analysis interface.

        This UI includes:
        - A left panel with controls to:
            * Browse and select an audio file
            * Start analysis on the selected file
            * Export analysis results to a PDF
            * Access settings and help pages
            * Return to the main menu
        - A middle panel showing:
            * A feedback text box with color-coded tags (info, success, error)
            * A visual engagement score meter with a gradient bar and a moving arrow
        - A right panel displaying:
            * A space for graph output (waveforms, spectrograms, etc.)

        This method sets up the full offline analysis UI, preparing all widgets and frames.
        """
        self.clear_window()
        self.create_header("Batch Analysis")

        content_frame = tk.Frame(self.root, bg=self.colors["background"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = tk.Frame(content_frame, bg=self.colors["background"])
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.create_section_header("Controls").pack(in_=left_panel, pady=10)

        self.file_entry = tk.Entry(
            left_panel,
            bg=self.colors["entry_bg"],
            fg=self.colors["entry_fg"],
            font=self.fonts["entry"],
            width=40,
        )
        self.file_entry.pack(pady=10)

        self.create_button(left_panel, "Browse", self.browse_file).pack(pady=None)
        self.create_button(left_panel, "Run Analysis", lambda: self.start_analysis()).pack(pady=50)
        self.create_button(left_panel, "Export to PDF", self.export_to_pdf).pack(pady=50)
        self.create_button(left_panel, "Settings", self.settings_page).pack(pady=50)
        self.create_button(left_panel, "Help", self.help_page).pack(pady=50)
        self.create_button(left_panel, "Back to Menu", self.create_main_menu).pack(pady=50)

        self.processing_label = tk.Label(left_panel, text="", bg=self.colors["background"], fg="red", font=self.fonts["text"])
        self.processing_label.pack(pady=10)

        middle_panel = tk.Frame(content_frame, bg=self.colors["background"])
        middle_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.create_section_header("Feedback Generation").pack(in_=middle_panel, pady=5)

        self.feedback_text = tk.Text(
            middle_panel,
            height=6,  
            width=80,
            bg=self.colors["text_bg"],
            fg=self.colors["text_fg"],
            font=("Lexend", 12),  
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
        )

        self.feedback_text.tag_config("info", foreground=self.colors["accent"])
        self.feedback_text.tag_config("success", foreground="green")
        self.feedback_text.tag_config("error", foreground="red")
        self.feedback_text.pack(padx=10, pady=10, fill=tk.Y, expand=True)

        right_panel = tk.Frame(content_frame, bg=self.colors.get("panel_bg", "white"), width=350)  
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        self.create_section_header("Engagement Score").pack(in_=middle_panel, pady=(20, 5))

        self.engagement_frame = tk.Frame(middle_panel, bg=self.colors.get("background", "white"))
        self.engagement_frame.pack(fill=tk.X, padx=10, pady=5)


        self.engagement_canvas = tk.Canvas(self.engagement_frame, width=600, height=40, bg=self.colors.get("background", "white"), highlightthickness=0)
        self.engagement_canvas.pack(anchor="center", pady=5)


        for i in range(200): 
            color = self.get_gradient_color(i / 2)  
            self.engagement_canvas.create_line(i * 3, 20, i * 3 + 3, 20, width=20, fill=color)


        self.arrow = self.engagement_canvas.create_polygon(0, 5, -5, 20, 5, 20, fill="black", outline="black")

        self.score_label = tk.Label(
            self.engagement_frame,
            text="0/100",
            font=("Lexend", 12, "bold"),
            bg=self.colors.get("background", "white"),
            fg=self.colors.get("text_fg", "black"),
        )
        self.score_label.pack(pady=(5, 0), anchor="center")

    
        self.create_section_header("Graph Display").pack(in_=right_panel, pady=5)

        self.graph_frame = tk.Frame(right_panel, bg=self.colors.get("graph_bg", "white")) 
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)







    def get_gradient_color(self, value):
        """
        Return a color hex code representing a gradient from red to green.

        Args:
            value (float): A number from 0 to 99 (representing a percentage).
        
        Returns:
            str: Hex color code for the appropriate color on the red-yellow-green scale.
        """
        if value < 50:
            red = 255
            green = int(255 * (value / 50))
        else:
            red = int(255 * ((100 - value) / 50))
            green = 255
        return f"#{red:02x}{green:02x}00"
        
        
    def update_engagement_score(self, score):
        """
        Update the engagement score meter based on a numeric value.

        This updates:
        - The arrow's position on the gradient bar.
        - The label showing score value.

        Args:
            score (int): Engagement score from 0 to 100.
        """
        score = max(0, min(100, score)) 
        x_pos = int((score / 100) * self.engagement_canvas.winfo_width())
        self.engagement_canvas.coords(self.arrow, x_pos, 5, x_pos - 5, 20, x_pos + 5, 20)
        self.score_label.config(text=f"{score}/100")







    def start_analysis(self):
        """
        Initiate the offline batch analysis process.

        - Displays a "Processing..." label to the user.
        - Starts analysis in a separate thread to prevent UI freezing.
        - Calls the core analysis and graph generation method.
        - Updates the UI when analysis is complete.
        """
        self.processing_label.config(
            text="Processing...",
            bg=self.colors["button_bg"],
            fg=self.colors["button_fg"]
        )

        def run_analysis():
            """Run analysis in a separate thread and update UI safely."""
            self.run_analysis_thread_and_generate_graphs(self.file_entry.get())
            self.root.after(0, lambda: self.processing_label.config(text="Analysis Finished!"))

        analysis_thread = Thread(target=run_analysis, daemon=True)
        analysis_thread.start()



    
        
        
        
        
        
    ########################## Help page ###############################
        
        
        
        
        
    def help_page(self):
        """
        Show a help page with detailed information about the application.

        This page includes multiple labeled sections providing:
        - A general introduction and overview of the tool
        - Instructions on getting started with both real-time and batch analysis
        - Helpful advice for optimal usage
        - Troubleshooting steps for common issues
        - A summary of default configuration values

        The layout uses two nested frames:
        - `help_frame` fills the window
        - `help_inner_frame` is centered inside it

        Content is dynamically generated from a list of help_sections,
        each containing a title and corresponding descriptive text.
        """
        self.clear_window()
        self.create_header("Help")

        help_frame = tk.Frame(self.root, bg=self.colors["background"])
        help_frame.pack(fill=tk.BOTH, expand=True)

        help_inner_frame = tk.Frame(help_frame, bg=self.colors["background"])
        help_inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        help_sections = [
            ("Welcome to the Speech Analysis Tool!", 
             "This application allows you to analyse audio in real-time or from pre-recorded files. "
             "It provides detailed feedback on various metrics such as loudness, pitch, speech rate, and energy."),
            
            ("Features Overview:", 
             "1. Real-Time Analysis: Analyze live audio streams with visual feedback.\n"
             "2. Batch Analysis: Upload audio files for detailed offline analysis.\n"
             "3. Graphical Insights: View waveform, spectrograms, and other visualizations.\n"
             "4. Feedback Generation: Receive actionable insights to improve your audio.\n"
             "5. Export Results: Save analysis results as a PDF for future reference."),
            
            ("Getting Started:", 
             "1. Main Menu: Choose between Real-Time Analysis, Batch Analysis, Settings, or Help.\n"
             "2. Real-Time Analysis:\n"
             "   - Click 'Start Recording' to begin analyzing live audio.\n"
             "   - Use the playback controls to pause, resume, or seek through recordings.\n"
             "   - Download recordings in WAV or MP3 format.\n"
             "3. Batch Analysis:\n"
             "   - Use the 'Browse' button to select an audio file.\n"
             "   - Click 'Run Analysis' to process the file and view results.\n"
             "   - Export results to a PDF using the 'Export to PDF' button."),
            
            ("Advice:", 
             "1. Ensure a quiet environment for real-time analysis to minimize background noise.\n"
             "2. Use high-quality audio files for batch analysis to improve accuracy.\n"
             "3. Adjust the 'Break Duration' in Settings to customize pause detection."),
            
            ("Troubleshooting:", 
             "1. Audio Not Detected: Ensure your microphone is properly connected and configured.\n"
             "2. File Not Loading: Verify the file format is supported (e.g., WAV, MP3, OGG, FLAC).\n"
             "3. Graphs Not Displaying: Ensure all dependencies (e.g., matplotlib) are installed."),
            
            ("Default Settings:", 
             "Break Duration: 7s\n"
             "Pitch Threshold: 120Hz\n"
             "Loudness Threshold: -25dB \n"
             "Pause Duration: 0.3s \n"
             "Speech Rate Threshold: 140wpm\n"
             "Pause Threshold: 0.005 \n"
             "Update Interval: 5s"),
        ]


        for title, content in help_sections:
            tk.Label(
                help_inner_frame,
                text=title,
                font=("Arial", 16, "bold"),
                bg=self.colors["background"],
                fg=self.colors["label"],
                anchor="w",
                justify="left",
            ).pack(pady=(10, 5), anchor="w")

            tk.Label(
                help_inner_frame,
                text=content,
                font=("Arial", 12),
                bg=self.colors["background"],
                fg=self.colors["text_fg"],
                anchor="w",
                justify="left",
                wraplength=800,
            ).pack(pady=(0, 10), anchor="w")


        footer_frame = tk.Frame(help_inner_frame, bg=self.colors["background"])
        footer_frame.pack(pady=15, fill=tk.X)
        self.create_button(footer_frame, "Back to Menu", self.create_main_menu).pack(side=tk.TOP, pady=10)

    
    
    
    
    
    ########################## settings page ###############################
    
    
    
    
    
    
    def settings_page(self):
        """
        Display the settings menu.

        This page allows users to customize key analysis parameters. These include:
        - Break duration
        - Pause duration
        - Loudness and silence thresholds
        - Update frequency for real-time analysis

        The function:
        - Displays labeled entry fields for each setting
        - Loads current values using `tk.StringVar`
        - Saves the updated configuration to `config.txt` when the user clicks 'Save Settings'
        - Notifies the user of success or input errors
        """
        self.clear_window()
        self.create_header("Settings")

        settings_frame = tk.Frame(self.root, bg=self.colors["background"])
        settings_frame.pack(pady=20, padx=20)

        settings_vars = {
            "break_duration": tk.StringVar(value=str(self.settings["break_duration"])),
            "pause_duration": tk.StringVar(value=str(self.settings["pause_duration"])), 
            "loudness_threshold": tk.StringVar(value=str(self.settings["loudness_threshold"])),  
            "pause_threshold_value": tk.StringVar(value=str(self.settings["pause_threshold_value"])),
            "update_interval": tk.StringVar(value=str(self.settings["update_interval"])),
            "silence_threshold": tk.StringVar(value=str(self.settings["silence_threshold"])),
        }

        def create_setting_entry(label_text, var_name):
            tk.Label(
                settings_frame,
                text=label_text,
                font=self.fonts["label"],
                bg=self.colors["background"],
                fg=self.colors["label"]
            ).pack(pady=5)
            entry = tk.Entry(
                settings_frame,
                textvariable=settings_vars[var_name],
                font=self.fonts["entry"],
                bg=self.colors["entry_bg"],
                fg=self.colors["entry_fg"],
                insertbackground=self.colors["entry_fg"],
                width=10,
                relief="flat"
            )
            entry.pack(pady=5)

        create_setting_entry("Break Duration (seconds):", "break_duration")
        create_setting_entry("Pause Duration (seconds):", "pause_duration")
        create_setting_entry("Loudness Threshold (dB):", "loudness_threshold")
        create_setting_entry("Pause Threshold (How loud for a pause):", "pause_threshold_value")
        create_setting_entry("Update Interval (How long for an update in realtime):", "update_interval")
        create_setting_entry("Silence Threshold (How silent for a real-time audio anlysis):", "silence_threshold")

        def save_settings():
            try:
                new_settings = {key: float(var.get()) for key, var in settings_vars.items()}
                self.settings.update(new_settings)
                with open("Code\ConfigFolder\config.txt", "w") as file:
                    for key, value in new_settings.items():
                        file.write(f"{key}={value}\n")
                messagebox.showinfo("Settings", "Settings saved successfully!")
            except ValueError:
                messagebox.showerror("Error", "Invalid number entered for one or more settings.")

        save_button = self.create_button(
            settings_frame,
            text="Save Settings",
            command=save_settings,
        )
        save_button.pack(pady=10)


        footer_frame = tk.Frame(self.root, bg=self.colors["background"])
        footer_frame.pack(pady=15)

        self.create_button(footer_frame, "Back to Menu", self.create_main_menu).pack(
            side=tk.LEFT, padx=20
        )











    ########################## GUI attributes ###############################




    def configure_window(self):
        """
        Configure the main application window.

        - Sets the window title.
        - Enables fullscreen mode by default.
        - Binds Escape to exit fullscreen and F11 to re-enter.
        - Applies a default white background color.
        """
        self.root.title("Speech Analysis Tool")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", lambda e: self.root.attributes("-fullscreen", True))
        self.root.config(bg="white")
        
        

    def initialise_styles(self):
        """
        Initialize global fonts and color themes for consistent UI styling.

        - Fonts are stored in `self.fonts` for buttons, labels, entries, and text.
        - Colors are defined in `self.colors` for buttons, text, backgrounds, etc.
        - Applies a custom ttk style for `TButton` with state-dependent colors.
        """
        font = ("Lexend", 14, "bold")

        self.fonts = {
            "button": ("Lexend", 12, "bold"),
            "label": font,
            "entry": font,
            "text": ("Lexend", 10, "bold")
        }

        self.colors = {
            "button_bg": "#4F8A8B",
            "button_fg": "#FFFFFF",
            "button_hover": "#397E7F",
            "button_active": "#2E6D6F",
            "entry_bg": "#f5f7f8",
            "entry_fg": "#333333",
            "text_bg": "#ffffff",
            "text_fg": "#000000",
            "accent": "#90C7C8",
            "label": "#333333",
            "highlight": "#e0e0e0",
            "background": "#fdfdfd",
        }

        style = ttk.Style()
        button_colors = self.colors

        style.configure("TButton",
            background=button_colors["button_bg"],
            foreground=button_colors["button_fg"],
            font=self.fonts["button"],
            padding=8,
            borderwidth=1,
            relief="solid",
            focuscolor=button_colors["button_bg"]
        )

        state_styles = [("pressed", "button_active"), ("active", "button_hover"), ("!disabled", "button_bg")]

        style.map("TButton",
            background=[(state, button_colors[key]) for state, key in state_styles],
            foreground=[(state, button_colors["button_fg"]) for state, _ in state_styles],
            relief=[("pressed", "sunken"), ("active", "raised"), ("!disabled", "flat")]
        )



    def create_header(self, text):
        """
        Display a main header label at the top of a page.

        Args:
            text (str): The header text to display.
        """
        tk.Label(
            self.root,
            text=text,
            font=("Arial", 20, "bold"),
            bg=self.colors["background"],
            fg=self.colors["label"],
        ).pack(pady=20)



    def create_section_header(self, text):
        """
        Return a consistent section header label.

        Args:
            text (str): The section title text.

        Returns:
            tk.Label: Configured label widget.
        """
        return tk.Label(
            self.root,
            text=text,
            font=self.fonts["label"],
            bg=self.colors["background"],
            fg=self.colors["label"],
        )



    def create_button(self, parent, text, command, **kwargs):
        """
        Create a custom styled button using CTkButton.

        Args:
            parent: The parent container for the button.
            text (str): Button label.
            command (callable): Function to be called when clicked.
            **kwargs: Additional keyword arguments for the button.

        Returns:
            CTkButton: Configured button instance.
        """
        return ctk.CTkButton(
            master=parent,
            text=text,
            command=command,
            corner_radius=10,
            fg_color=self.colors["button_bg"],
            hover_color=self.colors["button_hover"],
            text_color=self.colors["button_fg"],
            font=self.fonts["button"],
            width=160,    
            height=48,   
            **kwargs
        )


    def clear_window(self):
        """
        Remove all widgets from the root window.

        Useful when navigating between different pages/views.
        """
        for widget in self.root.winfo_children():
            widget.destroy()


    def browse_file(self):
        """
        Open a file dialog for selecting an audio file.

        Supported formats include WAV, MP3, OGG, and FLAC.
        Updates the `file_entry` widget with the selected file path.
        """
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.flac")],
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)








    ######################### Threading ###############################



    def run_analysis_thread_and_generate_graphs(self, file_path):
        """
        Process the audio file and generate analysis feedback and graphs in the UI.

        This function:
        - Loads the selected audio file using `AudioProcessor`
        - Performs feedback analysis and updates the engagement score
        - Displays textual feedback and various graphs:
            - Waveform
            - Mel Spectrogram
            - Fourier Transform
            - Loudness and Pauses Over Time

        The graph plotting is performed in a threaded fashion using `PlotManager`.
        """
        from AudioProcessor import AudioProcessor
        from PlotManager import PlotManager

        def background_analysis_and_generate_graphs():
            audio_processor = AudioProcessor()
            y, sr = audio_processor.load_audio_file(file_path, noise_suppression_factor=0.15) 
            if y is None or sr is None:
                self.update_feedback_with_highlights("Error processing the audio file.")
                return

            feedback = audio_processor.give_audio_feedback(y, sr)
            score = audio_processor.engagement_score  
            self.update_engagement_score(score)
            
            if not feedback:
                feedback = "No feedback could be generated for this audio file."
 
            self.update_feedback_with_highlights(feedback)
            
            graph_options = [
                "Waveform",
                "Mel Spectrogram",
                "Fourier Transform",
                "Loudness and Pauses Over Time",
            ]
            
            
            for widget in self.graph_frame.winfo_children():
                widget.destroy()
                
            for graph_type in graph_options:
                graph_frame_section = tk.Frame(self.graph_frame, bg=self.colors["background"])
                graph_frame_section.pack(pady=10, fill=tk.X)

                plot_manager = PlotManager(y, sr, graph_frame_section, graph_type)
                plot_manager.plot_graph_in_thread()
            

        background_analysis_and_generate_graphs()

        







    ########################## Feedback ###############################





    def update_feedback_with_highlights(self, feedback):
        """
        Update the feedback text box with color-highlighted keywords and interactive explanations.

        - Keywords in the feedback text are detected and styled with color using tags.
        - When a keyword is clicked, a tooltip/explanation is shown in a popup.
        - Highlight logic is based on pre-defined acoustic interpretations.
        """

        highlights = {
            "well-balanced": "Your loudness, pitch, and pauses are optimised for clear communication. This essentially means that for loudness, it fell between a category of -40 dB to -20 dB.",
            "quite loud": "The loudness exceeds typical conversational levels. Consider lowering the volume or stepping back from the microphone. This occurs when the loudness exceeds -20 dB, calculated in the analysis.",
            "very quiet": "The loudness is below the typical range. Try speaking closer to the microphone or projecting your voice more. This happens when the average loudness is below -40 dB.",
            "frequent short pauses": "Pauses are too brief and frequent, potentially interrupting the flow of speech. This reflects multiple pauses shorter than 7 seconds, identified during the pause analysis.",
            "long pauses": "Pauses may be too long, causing breaks in listener engagement. This means pauses lasting 7 seconds or more were detected.",
            "low pitch": "A low pitch may sound monotonous. Adding variation can improve engagement. This is determined when the average pitch is less than 100 Hz.",
            "pitch variation is quite low": "Minimal pitch variation can lead to a monotone delivery. Aim to vary your pitch dynamically. This corresponds to low standard deviation in pitch values.",
            "speech rate is a bit slow": "A slow speech rate can reduce energy and momentum. Consider speaking slightly faster. This happens when the rate of onsets divided by duration falls below typical conversational norms.",
            "speech rate is quite fast": "A fast speech rate might overwhelm the listener. Slow down to ensure clarity. This reflects an onset rate that significantly exceeds typical conversational norms.",
            "speech rate is well balanced": "Your speech rate is optimal for clear and engaging delivery. This means the calculated rate falls within the normal conversational range.",
            "vocal energy is quite low": "Low energy can make your speech sound flat. Emphasise your words to add impact. This corresponds to low average RMS energy values.",
            "vocal energy is quite high": "High energy is engaging but may tire you. Maintain a consistent yet powerful delivery. This reflects high average RMS energy values.",
            "vocal energy is balanced": "Your vocal energy is well-suited for engaging delivery. This is determined when RMS energy values fall within a balanced range.",
            "monotonous speech detected": "Monotonous speech lacks variation in tone, which may bore the listener. Add tonal changes for engagement. This happens when pitch variation is consistently low or average pitch remains static.",
            "good variation in tone": "Your tone is engaging and varied, keeping the audience attentive. Well done! This reflects adequate pitch variation detected in the analysis."
        }


        self.feedback_text.delete(1.0, tk.END)
        for line in feedback.splitlines():
            self.feedback_text.insert(tk.END, line + "\n")
            for key, explanation in highlights.items():
                if key in line:
                    start_idx = self.feedback_text.search(key, self.feedback_text.index(f"end-{len(line)}c"), tk.END, nocase=True)
                    if start_idx:
                        end_idx = f"{start_idx}+{len(key)}c"
                        tag_name = key.replace(" ", "_")

                        self.feedback_text.tag_add(tag_name, start_idx, end_idx)
                        self.feedback_text.tag_config(tag_name, foreground=self.colors["button_bg"], underline=False)

                        self.feedback_text.tag_bind(
                            tag_name,
                            "<Button-1>",
                            lambda event, exp=explanation: self.display_explanation(exp)
                        )


    def display_explanation(self, explanation):
        """
        Show a popup dialog box with the explanation for a highlighted term.

        Called when the user clicks a highlighted keyword in the feedback text.
        """
        messagebox.showinfo("Explanation", explanation)






    ########################## PDF export ###############################
    
    
    
    
    
    def export_to_pdf(self):
        """
        Export the feedback analysis text to a PDF file.

        - Validates whether an audio file path is selected.
        - Uses `PDFExporter` to convert feedback text to PDF format.
        """
        from PDFExporter import PDFExporter

        file_path = self.file_entry.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file first.")
            return

        pdf_exporter = PDFExporter(self.feedback_text)
        pdf_exporter.export_to_pdf()
        
        
        
    ########################## File Cleanup ###############################
    
    def cleanup_files(self):
        """
        Delete any previously generated image files used for graphs.

        This is called when the application exits to keep the working directory clean.
        """

        files_to_delete = [
            "loudness_pauses.png", 
            "mel_spectrogram.png", 
            "waveform.png", 
            "fourier_transform.png"
        ]
        
        current_directory = os.path.dirname(os.path.realpath(__file__))
        
        for file_name in files_to_delete:
            file_path = os.path.join(current_directory, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                pass




    ########################## Quit Application ###############################

    def quit_app(self):
        """
        Exit the application cleanly.

        - Cleans up temporary image files.
        - Releases webcam resources if active.
        - Properly shuts down the Tkinter window.
        """
        self.cleanup_files()

        if hasattr(self, "face_analyser"):
            self.face_analyser.cleanup()

        self.root.quit()
        self.root.destroy()



if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = AudioAnalysisApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()
