from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for ASEC site, inheriting from ParserBase
class AsecParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('asec.ahnlab.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class
            current_class = 'col-lg-12 col-md-12'
            article_main_class = soup.find('div', class_=current_class)
            if not article_main_class:
                logging.warning(f"Target class '{current_class}' related to article_main_class not found in the HTML.")
                return ''
            
            ## TITLE
            # Find title class
            current_class = 'post-title single_blog_inner__Title'
            article_title = article_main_class.find('h1', class_=current_class)
            if not article_title:
                logging.warning(f"Target class '{current_class}' related to article_title not found in the HTML.")
                return ''
            
            # Extract title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            ## CONTENT
            # Find content class
            current_class = 'entry-content clearfix'
            article_content = article_main_class.find('div', class_=current_class)
            if not article_content:
                logging.warning(f"Target class '{current_class}' related to article_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            header_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
            unwanted_headers = ['Tags:']
            unwanted_p_class = ['elementor-heading-title elementor-size-default'] # need to implement in for loop
            list_types = ['ul']
            elements = article_content.find_all(recursive=True)

            # Find all elements
            for element in elements:
                # Skip non-element nodes (like strings or comments)
                if not hasattr(element, 'name'):
                    continue

                # Process paragraphs
                if element.name == 'p':
                    # Extract text from the modified element
                    paragraph_text = element.get_text(separator=' ', strip=True)
                    content += paragraph_text + '\n\n'  # Add two newlines between paragraphs
                
                # Process headers
                elif element.name in header_tags:
                    current_title = element.get_text(strip=True)
                    if current_title not in unwanted_headers:
                        content += current_title + '\n' # Add newline after the title
                    else:
                        pass

                # Process lists
                elif element.name in list_types:
                    list_items = element.find_all('li')
                    if list_items:
                        for li in list_items:
                            list_item_text = li.get_text(separator=' ', strip=True)
                            content += list_item_text + '\n'
                else:
                    pass
            
            # Combine title + content
            data = f"{title}\n\n{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs
        
# Register the parser instance with the registry
register_parser(AsecParser())