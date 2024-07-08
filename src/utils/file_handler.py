import requests
import os
import json
import fitz  # PyMuPDF
from markdownify import markdownify as md
import mwparserfromhell
import pypandoc
import datetime
from utils.log import log_message


def get_run_start_time (config):
    return datetime.datetime.now().strftime(config['metadata']['timestamp_format'])
    
def download_file(url, path, is_pdf, is_mediawiki, config):
    response = requests.get(url)
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as file:
        file.write(response.content)
    log_message(f'Downloaded file: {path}',  config['logging']['log_file'])
    
    if is_pdf:
        convert_pdf_to_markdown(path, config)
    if is_mediawiki:
        convert_mediawiki_to_markdown(path, config)

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
    log_message(f"Converted {pdf_path} to Markdown and saved as {output_path}", config['logging']['log_file'])

def convert_mediawiki_to_markdown(mediawiki_path, config):
    with open(mediawiki_path, 'r', encoding='utf-8') as file:
        mediawiki_text = file.read()
    wikicode = mwparserfromhell.parse(mediawiki_text)
    html_text = wikicode.strip_code()
    markdown_text = pypandoc.convert_text(html_text, 'md', format='html')
    output_path = mediawiki_path.replace('.mediawiki', '.md')
    with open(output_path, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_text)
    log_message(f"Converted {mediawiki_path} to Markdown and saved as {output_path}", config['logging']['log_file'])

def save_metadata(metadata, start_time, config):
    file_name = os.path.join(config['metadata']['output_directory'], f"{config['metadata']['file_name_prefix']}_{start_time}.json")
    log_message(f'Saving metadata to {file_name}...', config['logging']['log_file'])
    if not os.path.exists(config['metadata']['output_directory']):
        os.makedirs(config['metadata']['output_directory'])
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(metadata, file, indent=4)
    log_message('Metadata saved.',  config['logging']['log_file'])