
import fitz  # PyMuPDF

def read_pdf_character_by_character(pdf_path):
    char_font_dict = {}

    try:
        # Open the PDF file using PyMuPDF
        pdf_document = fitz.open(pdf_path)

        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)

            current_font_size = None
            current_font_text = []

            # Get the text and font size information for each character in the page
            for block in page.get_text("dict")["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        if "spans" in line:
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

def find_heading_font(char_font_dict):
    predefined = ['education', 'skills', 'experience', 'professional summary', 'languages', 'work experience', 'personal information', 'referees']

    for font_size, text_list in char_font_dict.items():
        for text in text_list:
            # Split the text into words
            words = text.split()

            # Check if the text is one or two words and if it matches the predefined list
            if 1 <= len(words) <= 2 and any(word.lower() in predefined for word in words):
                return font_size

    # Return None if no matching font size is found
    return None


def read_pdf_sections(pdf_path, char_font_dict):
    sections = {}
    try:
        # Open the PDF file using PyMuPDF
        pdf_document = fitz.open(pdf_path)

        current_font_size = None
        current_text = []

        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)

            # Get the text and font size information for each character in the page
            for block in page.get_text("dict")["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        if "spans" in line:
                            for span in line["spans"]:
                                font_size = span["size"]
                                text = span["text"]

                                # Check if the current font size matches the heading font size
                                if font_size == find_heading_font(char_font_dict):
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

# Flask integration
from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    sections = {}

    if request.method == 'POST':
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename != '':
                # Save the uploaded file temporarily
                pdf_path = 'uploaded.pdf'
                pdf_file.save(pdf_path)

                # Read the PDF character by character and group characters by font size
                char_font_dict = read_pdf_character_by_character(pdf_path)

                # Read the PDF and create sections based on the second largest font size
                sections = read_pdf_sections(pdf_path, char_font_dict)

                # Remove the temporary PDF file
                os.remove(pdf_path)

    return render_template('index.html', sections=sections)

if __name__ == '__main__':
    app.run(debug=True)
