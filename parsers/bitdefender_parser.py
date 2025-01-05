from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for Bitdefender site, inheriting from ParserBase
class BitdefenderParser (ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('bitdefender.com')

    def fetch_data(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find title class
            current_element = 'h1'
            current_class = 'tw-text-3xl tw-font-bold md:tw-text-4xl md:tw-leading-tight xl:tw-text-5xl xl:tw-leading-tight' # in this case there are six classes separated by spaces
            current_fixed_class = current_class.replace(' ', '.')
            final_fixed_class = current_fixed_class.replace(':', '\\:')
            article_title = soup.select_one(f'{current_element}.{final_fixed_class}') # use CSS selector that targets a <div> element that has all classes
            if not article_title:
                logging.warning(f"Target {current_element} '{current_class}' related to article_title not found in the HTML.")
                return ''

            # Extract article title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            ## CONTENT
            # Find content class
            current_element = 'div'
            current_class = 'content tw-mb-12 tw-text-lg tw-text-black' # in this case there are four classes separated by spaces
            current_fixed_class = current_class.replace(' ', '.')
            article_content = soup.select_one(f'{current_element}.{current_fixed_class}') # use CSS selector that targets a <div> element that has both classes
            if not article_content:
                logging.warning(f"Target {current_element} '{current_class}' related to article_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            header_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
            list_types = ['ul', 'ol']

            unwanted_header_substrings = [
                "How to protect",
                "How to prevent",
                "Recommendations",
                "Indicators",
                "IP Addresses",
                "Hashes",
                "File Paths",
                "Domain",
                "best practices",
                "Malicious hashes",
                "Malicious Domains",
                "Worried"
                ]
            
            # Define unwanted substrings in paragraphs
            unwanted_paragraph_substrings = [
                "Bitdefender Scamio",
                "mitigate",
                "recommendations",
                "Bitdefender security solutions",
                "Figure",
                "Indicators",
                "Malicious hashes",
                "Malicious Domains",
                "Domain",
                "File Paths"
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
                        content += current_title + '\n\n' # Add newline after the title

                # Process paragraphs
                elif element.name == 'p':
                    if not skip_content:
                        paragraph_text = element.get_text(separator=' ', strip=True)

                        # Check if paragraph contains any unwanted substrings
                        if any(substring in paragraph_text for substring in unwanted_paragraph_substrings):
                            skip_content = True  # Start skipping content
                            continue  # Skip this paragraph

                        # Only add non-empty paragraphs to content
                        if paragraph_text.strip():
                            content += paragraph_text + '\n\n'  # Add two newlines between paragraphs
                    else:
                        continue

                # Process lists
                elif element.name in list_types:
                    if not skip_content:
                        list_items = element.find_all('li')
                        if list_items:
                            for li in list_items:
                                list_item_text = li.get_text(separator=' ', strip=True)
                                # Check if list item contains any unwanted substrings
                                if any(substring in list_item_text for substring in unwanted_paragraph_substrings):
                                    skip_content = True  # Start skipping content
                                    continue  # Skip this list item
                                content += list_item_text + '\n\n'
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
register_parser(BitdefenderParser())