# src/utils/converters.py
import fitz  # PyMuPDF
from markdownify import markdownify as md
import mwparserfromhell
import pypandoc
from utils.log import log_message

def convert_pdf_to_markdown(pdf_path, config):
    output_path = pdf_path.replace('.pdf', '.md')
    document = fitz.open(pdf_path)
    full_text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        full_text += page.get_text("text")
    markdown_text = md(full_text)
    with open(output_path, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_text)
    log_message(f"Converted {pdf_path} to Markdown and saved as {output_path}")

def convert_mediawiki_to_markdown(mediawiki_path, config):
    with open(mediawiki_path, 'r', encoding='utf-8') as file:
        mediawiki_text = file.read()
    wikicode = mwparserfromhell.parse(mediawiki_text)
    html_text = wikicode.strip_code()
    markdown_text = pypandoc.convert_text(html_text, 'md', format='html')
    output_path = mediawiki_path.replace('.mediawiki', '.md')
    with open(output_path, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_text)
    log_message(f"Converted {mediawiki_path} to Markdown and saved as {output_path}")
