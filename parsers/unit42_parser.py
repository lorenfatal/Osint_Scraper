from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for Unit42 Palo Alto site, inheriting from ParserBase
class Unit42Parser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('unit42.paloaltonetworks.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class
            current_class = 'main'
            article_main_class = soup.find('main', class_=current_class)
            if not article_main_class:
                logging.warning(f"Target class '{current_class}' related to article_main_class not found in the HTML.")
                return ''
            
            ## TITLE
            # Find title class
            current_class = 'ab__title'
            title_class = article_main_class.find('div', class_=current_class)
            if not title_class:
                logging.warning(f"Target class '{current_class}' related to title_class not found in the HTML.")
                return ''
            
            # Find title
            current_element =  'h1'
            article_title = title_class.find(current_element)
            if not article_title:
                logging.warning(f"Target element f{current_element} related to article_title not found in the HTML.")
                return ''
            
            # Extract title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            ## CONTENT
            # Find content class
            current_class = 'section blog-contents'
            article_content = article_main_class.find('section', class_=current_class)
            if not article_content:
                logging.warning(f"Target class '{current_class}' related to article_content not found in the HTML.")
                return ''
            

            # Extract full article content
            content = ''
            header_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
            list_types = ['ul', 'ol']

            unwanted_header_substrings = [
                "Indicators",
                "Samples",
                "References",
                "Mitigation",
                "Palo Alto",
                "Tags",
                "Related Articles",
                "Resources"
                ]
            unwanted_div_classes = ['be-related-articles', 'pa related-threat']

            # Initialize the skip flag
            skip_content = False
            
            elements = article_content.find_all(recursive=True)

            def is_inside_unwanted_div(element, unwanted_classes):
                """
                Determines if the element is nested within a <div> with any of the unwanted classes.

                Parameters:
                    element (Tag): The html Tag to check.
                    unwanted_classes (list): List of classes to exclude.

                Returns:
                    bool: True if the element is inside an unwanted <div>, False otherwise.
                """
                # Traverse up the parent hierarchy
                for parent in element.find_parents('div'):
                    parent_classes = parent.get('class', [])
                    # Check if any of the parent's classes are in the unwanted_classes list (case-insensitive)
                    if any(cls.lower() in [uc.lower() for uc in unwanted_classes] for cls in parent_classes):
                        return True
                return False

            # Find all elements
            for element in elements:
                # Skip non-element nodes (like strings or comments)
                if not hasattr(element, 'name'):
                    continue
                
                # Skip elements inside unwanted divs
                if is_inside_unwanted_div(element, unwanted_div_classes):
                    skip_content = True
                    continue

                # Skip all content below unwanted div
                if skip_content:
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
                
                # Skip all content below unwanted header
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
            
            # Combine title + content
            data = f"{title}\n\n{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs
        
# Register the parser instance with the registry
register_parser(Unit42Parser())