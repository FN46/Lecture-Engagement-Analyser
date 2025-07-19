import os
from tkinter import filedialog, messagebox
import webbrowser
from fpdf import FPDF


class PDFExporter:
    def __init__(self, feedback_text_widget):
        """
        Initialises the PDFExporter with a text widget containing feedback.
        """
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.feedback_text_widget = feedback_text_widget


    def export_to_pdf(self):
        """
        Prompts the user to select a save location and exports the content
        of the feedback text widget along with plots to a PDF.
        """
        pdf_path = self.get_save_path()
        if not pdf_path:  
            return

        self.create_pdf(pdf_path)
        self.show_export_success_message()
        self.open_pdf_in_viewer(pdf_path)


    def save_plot(self, figure, filename):
        """
        Saves a matplotlib figure as a PNG file.
        """
        figure.savefig(filename, format='png', bbox_inches='tight')


    def get_save_path(self):
        """
        Opens a file dialog for the user to specify the PDF save path.
        """
        return filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            title="Save PDF as"
        )


    def create_pdf(self, pdf_path):
        """
        Generates the PDF document with the feedback text and plots.
        """
        self.pdf.add_page()
        self.add_pdf_title()
        self.add_feedback_text()
        self.add_plots_to_pdf()
        self.pdf.output(pdf_path)


    def add_pdf_title(self):
        """
        Adds the title to the PDF document.
        """
        self.pdf.set_font("Arial", 'B', 16)
        self.pdf.cell(0, 10, 'Audio Analysis Report', ln=True, align='C')
        self.pdf.ln(10)


    def add_feedback_text(self):
        """
        Adds the feedback text to the PDF document.
        """
        self.pdf.set_font("Arial", '', 12)
        feedback_content = self.feedback_text_widget.get("1.0", "end").strip()
        self.pdf.multi_cell(0, 10, feedback_content)
        self.pdf.ln(10)


    def add_plots_to_pdf(self):
        """
        Adds plot images to the PDF document if they exist.
        """
        plot_filenames = [
            'Code\waveform.png',
            'Code\mel_spectrogram.png',
            'Code\\fourier_transform.png',
            'Code\loudness_pauses.png'
        ]

        for plot_filename in plot_filenames:
            self.add_plot_if_exists(plot_filename)


    def add_plot_if_exists(self, plot_filename):
        """
        Adds a single plot image to the PDF if the file exists.
        """
        if os.path.exists(plot_filename):
            self.pdf.image(plot_filename, x=10, w=180)


    def show_export_success_message(self):
        """
        Displays a message box indicating that the PDF was created successfully.
        """
        messagebox.showinfo("Export Successful", "PDF has been created successfully!")


    def open_pdf_in_viewer(self, pdf_path):
        """
        Opens the exported PDF file in the default PDF viewer.
        """
        webbrowser.open(pdf_path)
