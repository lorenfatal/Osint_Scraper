from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for SOCRadar site, inheriting from ParserBase
class SocRadarParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('socradar.io')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find article content class
            current_class = 'editor-field flex flex-col gap-[2em]'
            article_content_class = soup.find('div', class_=current_class)
            if not article_content_class:
                logging.warning(f"Target class '{current_class}' related to article_content_class not found in the HTML.")
                return ''
            
            ## FULL CONTENT
            # Extract full article content
            content = ''
            header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            unwanted_header_substrings = [
                "IOC’s",
                "MITRE ATT&CK Tactics",
                "Mitigation",
                "Protection",
                "How to Secure",
                "SOCRadar"
                ]
            list_types = ['ul', 'ol']

            # Initialize the skip flag
            skip_content = False
            
            elements = article_content_class.find_all(recursive=True)

            # Find all elements
            for element in elements:
                # Skip non-element nodes (like strings or comments)
                if not hasattr(element, 'name'):
                    continue
                
                # Process headers
                if element.name in header_tags:
                    current_title = element.get_text(strip=True)
                    # Check if any unwanted substring is in the current header
                    if any(substring in current_title for substring in unwanted_header_substrings):
                        skip_content = True
                        continue # Skip adding the unwanted header text
                    else:
                        skip_content = False
                        content += current_title + '\n' # Add newline after the title
                
                if skip_content:
                    continue

                # Process paragraphs
                if element.name == 'p':
                    # Extract text from the modified element
                    paragraph_text = element.get_text(separator=' ', strip=True)
                    content += paragraph_text + '\n\n'  # Add two newlines between paragraphs

                # Process lists
                elif element.name in list_types:
                    list_items = element.find_all('li')
                    if list_items:
                        for li in list_items:
                            list_item_text = li.get_text(separator=' ', strip=True)
                            content += list_item_text + '\n'
                else:
                    continue
            
            data = f"{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs
        
# Register the parser instance with the registry
register_parser(SocRadarParser())