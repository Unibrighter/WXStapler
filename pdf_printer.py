import os
import json
import requests
import pdfkit

def load_articles(file_path='articles.json'):
    """
    Load the articles from the specified file.

    :param file_path: The file path to load the articles from.
    :return: A list of article dictionaries.
    """
    with open(file_path, 'r', encoding='utf8') as f:
        articles = json.load(f)
    return articles

def sanitize_html(html):
    """
    Apply required replacements to the HTML content to render it correctly.

    :param html: The input HTML content.
    :return: The sanitized HTML content.
    """
    html = html.replace('visibility: hidden;', 'visibility: visible;')
    html = html.replace('\"//', '\"https://')
    html = html.replace('data-src', 'src')
    return html

def create_pdf(article, output_dir):
    """
    Fetch the article HTML and convert it to a PDF file.

    :param article: The article dictionary containing the title and URL.
    :param output_dir: The output directory for the PDF files.
    """
    url = article['url']
    title = article['title']
    date = article['date']
    title_with_date = date + title

    response = requests.get(url)
    html = sanitize_html(response.text)

    # Set the options for wkhtmltopdf
    options = {
        '--enable-plugins': '',
        '--enable-forms': '',
        '--enable-local-file-access': '',
        '--no-background': '',
        '--image-dpi': '1200',
    }

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save the HTML as a PDF
    pdf_path = os.path.join(output_dir, f"{title_with_date}.pdf")
    pdfkit.from_string(html, pdf_path, options=options)
    print(f"Generated PDF: {pdf_path}")

def remove_duplicate_articles(articles):
    """
    Remove duplicate articles based on their titles.

    :param articles: A list of article dictionaries.
    :return: A list of unique article dictionaries.
    """
    unique_articles = []
    seen_titles = set()

    for article in articles:
        if article['title'] not in seen_titles:
            seen_titles.add(article['title'])
            unique_articles.append(article)

    return unique_articles

def main():
    articles = load_articles()
    artciles = remove_duplicate_articles(articles)
    output_dir = "pdf_output"

    for article in articles:
        create_pdf(article, output_dir)

if __name__ == "__main__":
    main()
