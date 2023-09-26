import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request

app = Flask(__name__)

def read_pdf_character_by_character(pdf_path):
    char_font_dict = {}

    try:
        # Open the PDF file using PyMuPDF
        pdf_document = fitz.open(pdf_path)

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)

            current_font_size = None
            current_font_text = []

            # Get the text and font size information for each character in the page
            for block in page.get_text("dict")["blocks"]:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_size = span["size"]
                        text = span["text"]

                        # Iterate through each character in the text
                        for char in text:
                            # Check if the current character has the same font size as the previous one
                            if font_size == current_font_size:
                                current_font_text.append(char)
                            else:
                                # Store the characters with the same font size
                                if current_font_size is not None:
                                    if current_font_size in char_font_dict:
                                        char_font_dict[current_font_size].append(''.join(current_font_text))
                                    else:
                                        char_font_dict[current_font_size] = [''.join(current_font_text)]
                                current_font_size = font_size
                                current_font_text = [char]

            # Store the characters from the last font size encountered on the page
            if current_font_size is not None:
                if current_font_size in char_font_dict:
                    char_font_dict[current_font_size].append(''.join(current_font_text))
                else:
                    char_font_dict[current_font_size] = [''.join(current_font_text)]

        pdf_document.close()
    except Exception as e:
        print(f"Error: {str(e)}")

    return char_font_dict

def read_pdf_sections(pdf_path, char_font_dict, sorted_font_sizes):
    sections = {}
    try:
        # Open the PDF file using PyMuPDF
        pdf_document = fitz.open(pdf_path)

        current_font_size = None
        current_text = []

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)

            # Get the text and font size information for each character in the page
            for block in page.get_text("dict")["blocks"]:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_size = span["size"]
                        text = span["text"]

                        # Check if the current font size matches the second largest font size
                        if font_size == sorted_font_sizes[1]:
                            if current_font_size != font_size and current_text:
                                # Start of a new section
                                sections[current_text[0]] = " ".join(current_text[1:])
                                current_text = []

                        current_text.append(text)
                        current_font_size = font_size

        # Add the last section if there's any remaining text
        if current_text:
            sections[current_text[0]] = " ".join(current_text[1:])

        pdf_document.close()
    except Exception as e:
        print(f"Error: {str(e)}")

    return sections

@app.route('/', methods=['GET', 'POST'])
def upload_cv():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return render_template('index.html', error='No file part')

        file = request.files['file']

        # Check if the file has a name and it has a .pdf extension
        if file.filename == '' or not file.filename.endswith('.pdf'):
            return render_template('index.html', error='Invalid file format')

        # Save the uploaded file to a temporary location
        cv_path = os.path.join('uploads', 'cv.pdf')
        file.save(cv_path)

        # Read the PDF character by character and group characters by font size
        char_font_dict = read_pdf_character_by_character(cv_path)

        # Sort font sizes in descending order
        sorted_font_sizes = sorted(char_font_dict.keys(), reverse=True)

        # Read the PDF and create sections based on the second largest font size
        sections = read_pdf_sections(cv_path, char_font_dict, sorted_font_sizes)

        return render_template('index.html', sections=sections)

    return render_template('index.html', sections=None, error=None)

if __name__ == '__main__':
    app.run(debug=True)