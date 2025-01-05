from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse
import logging

# Parser for Kaspersky site securelist, inheriting from ParserBase
class SecurelistParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('securelist.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find title class
            current_element = 'h1'
            current_class = 'c-article__title'
            article_title = soup.find(current_element, class_=current_class)
            if not article_title:
                logging.warning(f"Target {current_element} '{current_class}' related to article_title not found in the HTML.")
                return ''

            # Extract article title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            ## CONTENT
            # Find content
            current_element = 'div'
            current_class = 'c-wysiwyg'
            article_content = soup.find(current_element, class_=current_class)
            if not article_content:
                logging.warning(f"Target {current_element} '{current_class}' related to article_content not found in the HTML.")
                return ''
            
            ## Extract full article content            
            # Initialize variables
            content = []
            skip_content = False
            header_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
            list_types = ['ul', 'ol']
            unwanted_header_substrings = ["Indicators"]

            # Handle unwanted data - script text that appears in a div class in Kapsersky articles
            unwanted_classes = [
                'crayon-syntax',
                'crayon-theme-classic',
                'crayon-font-monaco',
                'crayon-os-pc',
                'print-yes',
                'notranslate'
            ]

            # Remove unwanted divs before processing
            unwanted_class_selector = '.' + '.'.join(unwanted_classes)
            unwanted_divs = article_content.select(f'div{unwanted_class_selector}')

            for div in unwanted_divs:
                div.decompose()

            def process_element(element, skip_content, content):
                # Only process if element is a Tag
                if not isinstance(element, Tag):
                    return skip_content

                # Process headers
                if element.name in header_tags:
                    if not skip_content:
                        current_title = element.get_text(separator=' ', strip=True)
                        if any(substring in current_title for substring in unwanted_header_substrings):
                            skip_content = True  # Start skipping content
                        else:
                            skip_content = False
                            if current_title.strip():
                                content.append(current_title + '\n\n')  # Add newline after the title
                    # Do not process children of headers
                    return skip_content

                # Process paragraphs
                elif element.name == 'p':
                    if not skip_content:
                        paragraph_text = element.get_text(separator=' ', strip=True)
                        if paragraph_text.strip():
                            content.append(paragraph_text + '\n\n')  # Add two newlines between paragraphs
                    # Do not process children of paragraphs
                    return skip_content

                # Process lists
                elif element.name in list_types:
                    if not skip_content:
                        list_items = element.find_all('li', recursive=False)
                        for li in list_items:
                            list_item_text = li.get_text(separator=' ', strip=True)
                            if list_item_text.strip():
                                content.append(list_item_text + '\n\n')
                    # Do not process children of lists
                    return skip_content

                # Recursively process child elements
                for child in element.children:
                    skip_content = process_element(child, skip_content, content)

                return skip_content

            # Start processing from the root element
            process_element(article_content, skip_content, content)

            # Combine the extracted content
            final_content = ''.join(content)
            data = f"{title}\n\n{final_content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs

# Register the parser instance with the registry
register_parser(SecurelistParser())