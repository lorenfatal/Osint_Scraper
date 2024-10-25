from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
from urllib.parse import urlparse
import logging

# Parser for HackRead site, inheriting from ParserBase
class HackReadParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('hackread.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class
            current_class = 'cs-site-primary'
            article_main = soup.find('main', class_=current_class)
            if not article_main:
                logging.warning(f"Target main '{current_class}' related to article_main not found in the HTML.")
                return ''
            
            # Find article title class
            current_class = 'cs-entry__title cs-entry__title-line'
            article_title = article_main.find('h1', class_=current_class)
            if not article_title:
                logging.warning(f"Target h1 '{current_class}' related to article_title not found in the HTML.")
                return ''
            
            # Extract article title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            # Find article content class
            current_class = 'entry-content'
            article_content = article_main.find('div', class_=current_class)
            if not article_content:
                logging.warning(f"Target div '{current_class}' related to article_content not found in the HTML.")
                return ''

            ## Handle duplicate text
            # Define the list of wanted nested tags
            wanted_nested_tags = ['em']

            paragraphs = article_content.find_all('p')
            content = ''
            if not paragraphs:
                logging.warning("Target <p> tag not found in the HTML.")
                return ''
            else:
                for p in paragraphs:
                    paragraph_text_parts = []
                    for child in p.contents:
                        if isinstance(child, NavigableString):
                            paragraph_text_parts.append(child.strip())
                        elif isinstance(child, Tag):
                            if child.name in wanted_nested_tags:
                                # Include text from wanted nested tags
                                paragraph_text_parts.append(child.get_text(separator=' ', strip=True))
                            else:
                                # Skip tags not in wanted_nested_tags
                                continue
                    paragraph_text = ' '.join(paragraph_text_parts).strip()
                    if paragraph_text:
                        content += paragraph_text + '\n\n'  # Add two newlines between paragraphs

            # Combine title + content
            data = f"{title}\n\n{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs

# Register the parser instance with the registry
register_parser(HackReadParser())