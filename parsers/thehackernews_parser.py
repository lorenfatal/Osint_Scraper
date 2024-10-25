from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for the hacker news site, inheriting from ParserBase
class ThehackernewsParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('thehackernews.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            ## TITLE
            # Find main class 'main clear'
            current_class = 'main clear'
            article_main = soup.find('main', class_=current_class)
            if not article_main:
                logging.warning(f"Target main element '{current_class}' not found in the HTML.")
                return ''
            
            # Find title class
            current_class = 'story-title'
            article_title = article_main.find('h1', class_=current_class)
            if not article_title:
                logging.warning(f"Target h1 '{current_class}' not found in the HTML.")
                return ''

            # Extract title
            title_tag = article_title.find('a')
            title = title_tag.get_text(strip=True) if title_tag else 'No Title Found'

            ## ARTICLE TEXT
            current_element = article_main

            # Define div classes names
            div_classes = ['main-box clear', 'main-left-right clear', 'left-box', 'content section', 'widget Blog', 'blog-posts clear', 'post', 'post-body', 'articlebody clear cf']

            # Traverse through each div level
            for i, class_name in enumerate(div_classes, start=1):
                current_element = current_element.find('div', class_=class_name)
                if not current_element:
                    logging.warning(f"Div level {i} with class '{class_name}' not found in the HTML.")
                    return ''
                
            # After traversing all div levels, find the <p> tag
            paragraphs = current_element.find_all('p')
            content = ''
            if not paragraphs:
                logging.warning("Target <p> tag not found in the HTML.")
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
register_parser(ThehackernewsParser())