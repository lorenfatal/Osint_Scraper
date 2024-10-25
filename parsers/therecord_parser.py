from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for The Record news site, inheriting from ParserBase
class TherecordParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('therecord.media')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class 'sidebar-page-main'
            current_class = 'sidebar-page-main'
            main_element = soup.find('main', class_=current_class)
            if not main_element:
                logging.warning(f"Main element '{current_class}' not found in the HTML.")
                return ''
            
            # Find 'article__content' class
            current_class = 'article__content'
            article_content = main_element.find('div', class_=current_class)
            if not article_content:
                logging.warning(f"Target class '{current_class}' not found in the HTML.")
                return ''
            
            # Find title class
            article_title = article_content.find('h1')
            if not article_title:
                logging.warning("Target h1 not found in the HTML.")
                return ''

            # Extract article title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            # Find 'wysiwyg-parsed-content' class
            current_class = 'wysiwyg-parsed-content'
            parsed_content = article_content.find('span', class_=current_class)
            if not parsed_content:
                logging.warning(f"Target class '{current_class}' not found in the HTML.")
                return ''

            # Extract article body content
            current_class = 'paragraph'
            paragraphs = parsed_content.find_all('p', class_=current_class)
            content = ''
            if not paragraphs:
                logging.warning(f"Target <p> tag & class '{current_class}' not found in the HTML.")
                return ''
            else:
                for p in paragraphs:
                    paragraph_text = p.get_text(separator=' ', strip=True)
                    content += paragraph_text + '\n\n'  # Add two newlines between paragraphs  

            # Combine title + content
            data = f"{title}\n\n{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs

# Register the parser instance with the registry
register_parser(TherecordParser())