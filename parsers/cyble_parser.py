from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for Cyble site, inheriting from ParserBase
class CybleParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('cyble.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class 'site-main'
            current_class = 'site-main'
            article_main = soup.find('main', class_=current_class, id = 'main')
            if not article_main:
                logging.warning(f"Main class '{current_class}' not found in the HTML.")
                return ''
            
            # Find class that contains all article data
            current_data_id = '4402e2e'
            article_container = article_main.find(
                                                            'div',
                                                            attrs={
                                                            'data-id': current_data_id,
                                                            'data-element_type': 'container'
                                                            })
            if not article_container:
                logging.warning(f"Target data-id: '{current_data_id}' related to article_container not found in the HTML.")
                return ''
            
            ## TITLE
            # Find title
            current_data_id = '3c220676'
            article_title = article_container.find(
                                                    'div',
                                                    attrs={
                                                    'data-id': current_data_id,
                                                    'data-element_type': 'widget',
                                                    'data-widget_type' : 'theme-post-title.default'
                                                    })
            if not article_title:
                logging.warning(f"Target data-id '{current_data_id}' related to article_title not found in the HTML.")
                return ''
            
            # Extract title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            # Find sub-title
            current_data_id = '1fcc1d6c'
            article_sub_title = article_container.find(
                                                    'div',
                                                    attrs={
                                                    'data-id': current_data_id,
                                                    'data-element_type': 'widget',
                                                    'data-widget_type' : 'theme-post-excerpt.default'
                                                    })
            if not article_sub_title:
                logging.warning(f"Target data-id '{current_data_id}' related to article_sub_title not found in the HTML.")
                return ''
            
            # Extract sub-title
            sub_title = article_sub_title.get_text(strip=True) if article_sub_title else 'No Sub-Title Found'

            ## CONTENT
            # Find content class
            current_data_id = '2907e1e2'
            article_content = article_container.find(
                                                    'div',
                                                    attrs={
                                                    'data-id': current_data_id,
                                                    'data-element_type': 'widget',
                                                    'data-widget_type' : 'theme-post-content.default'
                                                    })
            if not article_content:
                logging.warning(f"Target data-id '{current_data_id}' related to article_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            titles_class = 'wp-block-heading'
            unwanted_headers = ['Our Recommendations', 'Recommendations and Mitigation', 'MITRE ATT&CK® Techniques', 'Indicators of Compromise (IOCs)']

            # Find all <h2> tags
            for h2 in article_content.find_all('h2', class_=titles_class):
                current_title = h2.get_text(strip=True)
                if current_title not in unwanted_headers:
                    content += current_title + '\n' # Add newline after the title
                
                    # Find all <p> tags within the same section
                    next_node = h2.find_next_sibling()
                    while next_node and next_node.name != 'h2':
                        if next_node.name == 'p':
                            paragraph_text = next_node.get_text(separator=' ', strip=True)
                            content += paragraph_text + '\n\n'  # Add two newlines between paragraphs
                        elif next_node.name == 'ul':
                        # Extract 'key takeaways' content
                            key_paragraphs = next_node.find_all('li')
                            if key_paragraphs:
                                for li in key_paragraphs:
                                    key_paragraph_text = li.get_text(separator=' ', strip=True)
                                    content += key_paragraph_text + '\n\n'  # Add two newlines between items
                        next_node = next_node.find_next_sibling()
                pass
            
            # Combine title + content
            data = f"{title}\n{sub_title}\n\n{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs
        
# Register the parser instance with the registry
register_parser(CybleParser())