from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for github site, inheriting from ParserBase
class GithubParser (ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('github.com')

    def fetch_data(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            ## FULL CONTENT
            # Find full content class
            current_element = 'article'
            current_class = 'markdown-body entry-content container-lg'
            current_fixed_class = current_class.replace(' ', '.')
            article_content = soup.select_one(f'{current_element}.{current_fixed_class}') # use CSS selector that targets a <div> element that has both classes
            if not article_content:
                logging.warning(f"Target {current_element} '{current_class}' related to article_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            list_types = ['ul', 'ol']

            elements = article_content.find_all(recursive=True)

            # Find all elements
            for element in elements:
                # Skip non-element nodes (like strings or comments)
                if not hasattr(element, 'name'):
                    continue
                
                # Process headers
                if element.name in header_tags:
                    current_title = element.get_text(strip=True)
                    # Only add non-empty paragraphs to content
                    if current_title.strip():
                        content += current_title + '\n\n' # Add newline after the title

                # Process paragraphs
                elif element.name == 'p':
                    current_paragraph = element.get_text(separator=' ', strip=True)
                    # Only add non-empty paragraphs to content
                    if current_paragraph.strip():
                        content += current_paragraph + '\n\n'  # Add two newlines between paragraphs

                # Process lists
                elif element.name in list_types:
                    list_items = element.find_all('li')
                    if list_items:
                        for li in list_items:
                            current_list_item = li.get_text(separator=' ', strip=True)
                            # Only add non-empty paragraphs to content
                            if current_list_item.strip():
                                content += current_list_item + '\n\n'
                else:
                    continue
            
            # Combine title + content
            data = f"{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs
        
# Register the parser instance with the registry
register_parser(GithubParser())