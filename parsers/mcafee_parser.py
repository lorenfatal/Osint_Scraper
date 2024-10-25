from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for McAfee site, inheriting from ParserBase
class McAfeeParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('mcafee.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class
            current_class = 'container-fluid p-0'
            article_main_class = soup.find('div', class_=current_class)
            if not article_main_class:
                logging.warning(f"Target class '{current_class}' related to article_main_class not found in the HTML.")
                return ''
            
            ## TITLE
            # Find title
            current_class = 'main-heading'
            article_title = article_main_class.find('h1', class_=current_class)
            if not article_title:
                logging.warning(f"Target class '{current_class}' related to article_title not found in the HTML.")
                return ''
            
            # Extract title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            ## CONTENT
            # Find content class
            current_class = 'the_content'
            article_content = article_main_class.find('div', class_=current_class)
            if not article_content:
                logging.warning(f"Target class '{current_class}' related to article_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            unwanted_headers = ['Indicators of Compromise', 'McAfee Mobile Security', 'Introducing McAfee+']
            unwanted_paragraphs = ['SHA256 Hash(es):', 'Domain(s):', 'Stay Updated', 'McAfee Labs is one of the leading sources for threat research, threat intelligence, and cybersecurity thought leadership. See our blog posts below for more information.']
            header_tags = ['h2', 'h6']
            list_types = ['ol', 'ul']
            elements = article_content.children

            # Find all elements
            for element in elements:
                # Skip non-element nodes (like strings or comments)
                if not hasattr(element, 'name'):
                    continue

                # Process paragraphs
                if element.name == 'p':
                    # Make a copy of the element to avoid modifying the original
                    p_copy = element.__copy__()
                    # Remove all <em> tags
                    for em in p_copy.find_all('em'):
                        em.decompose()
                    # Extract text from the modified element
                    paragraph_text = p_copy.get_text(separator=' ', strip=True)
                    if paragraph_text not in unwanted_paragraphs:
                        content += paragraph_text + '\n\n'  # Add two newlines between paragraphs
                    else:
                        pass
                
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
register_parser(McAfeeParser())