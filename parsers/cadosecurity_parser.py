from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for Cadosecurity site, inheriting from ParserBase
class CadosecurityParser (ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain == 'cadosecurity.com' or domain.endswith('.cadosecurity.com')

    def fetch_data(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            ## TITLE
            # Find title class
            current_element = 'h1'
            current_class = 'title'
            title_class = soup.find(current_element, class_=current_class)
            if not title_class:
                logging.warning(f"Target {current_element} '{current_class}' related to title_class not found in the HTML.")
                return ''
            
            # Extract title
            title = title_class.get_text(strip=True) if title_class else 'No Title Found'

            ## CONTENT
            # Find content
            current_element = 'div'
            current_class = 'body'
            article_content = soup.find(current_element, class_=current_class)
            if not article_content:
                logging.warning(f"Target {current_element} '{current_class}' related to article_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            list_types = ['ul', 'ol']

            unwanted_header_substrings = [
                "IOCs",
                "Detection",
                "MITRE ATTACK",
                "ATT&CK",
                "Yara",
                "Indicators",
                "Paths"
                ]
            
            unwanted_paragraph_substrings = [
                "Yara",
                "To read more",
                "Want to learn more",
                "Buzzword Bingo",
                "Want to see how",
                "incident response plan",
                "Interested in more research"
                ]
            
            elements = article_content.find_all(recursive=True)
            skip_content = False

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
                        skip_content = True  # Start skipping content
                        continue  # Skip processing this header
                    else:
                        skip_content = False
                        # Only add non-empty paragraphs to content
                        if current_title.strip():
                            content += current_title + '\n\n' # Add newline after the title

                # Process paragraphs
                elif element.name == 'p':
                    if not skip_content:
                        current_paragraph = element.get_text(separator=' ', strip=True)
                        # Check if any unwanted substring is in the current paragraph
                        if any(substring in current_paragraph for substring in unwanted_paragraph_substrings):
                            skip_content = True  # Start skipping content
                            continue  # Skip processing this paragraph
                        else:
                            skip_content = False
                            # Only add non-empty paragraphs to content
                            if current_paragraph.strip():
                                content += current_paragraph + '\n\n'  # Add two newlines between paragraphs
                    else:
                        continue

                # Process lists
                elif element.name in list_types:
                    if not skip_content:
                        list_items = element.find_all('li')
                        if list_items:
                            for li in list_items:
                                current_list_item = li.get_text(separator=' ', strip=True)
                                # Only add non-empty paragraphs to content
                                if current_list_item.strip():
                                    content += current_list_item + '\n\n'
                    else:
                        continue
                else:
                    continue
            
            # Combine title + content
            data = f"{title}\n\n{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs
        
# Register the parser instance with the registry
register_parser(CadosecurityParser())