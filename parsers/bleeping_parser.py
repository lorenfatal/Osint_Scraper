from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for Bleeping site, inheriting from ParserBase
class BleepingParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('bleepingcomputer.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find bc_main_content class
            current_class = 'bc_main_content'
            section = soup.find('section', class_=current_class)
            if not section:
                logging.warning(f"Target section '{current_class}' not found in the HTML.")
                return ''
            
            # Find article_section class
            current_class = 'article_section'
            article_section = section.find('div', class_=current_class)
            if not article_section:
                logging.warning(f"Target div '{current_class}' not found within the section.")
                return ''
            
            # Find articleBody class
            current_class = 'articleBody'
            article_body = article_section.find('div', class_=current_class)
            if not article_body:
                logging.warning(f"Target div '{current_class}' not found within the article section.")
                return ''
            
            # Extract article title
            title_tag = article_section.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else 'No Title Found'

            # Define unwanted element 'related articles'
            unwanted_class = 'cz-related-article-wrapp'

            # Extract article body content
            paragraphs = article_body.find_all('p')
            content = ''
            if not paragraphs:
                logging.warning("Target <p> tag not found in the HTML.")
                return ''
            else:
                for p in paragraphs:
                    # Check if the paragraph is inside an unwanted element
                    if p.find_parent(class_=unwanted_class):
                        continue  # Skip this paragraph
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
register_parser(BleepingParser())