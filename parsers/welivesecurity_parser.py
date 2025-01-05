from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for welivesecurity (by eset) site, inheriting from ParserBase
class WelivesecurityParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain == 'welivesecurity.com' or domain.endswith('.welivesecurity.com')

    def fetch_data(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class
            current_element = 'div'
            current_class = 'container article-page py-5' # in this case there are three classes separated by spaces
            current_fixed_class = current_class.replace(' ', '.')
            article_main_class = soup.select_one(f'{current_element}.{current_fixed_class}') # use CSS selector that targets a <div> element that has both classes
            if not article_main_class:
                logging.warning(f"Target {current_element} '{current_class}' related to article_main_class not found in the HTML.")
                return ''
            
            ## TITLE
            # Find headers class
            current_element = 'div'
            current_class = 'article-header'
            headers_class = article_main_class.find(current_element, class_=current_class)
            if not headers_class:
                logging.warning(f"Target {current_element} '{current_class}' related to headers_class not found in the HTML.")
                return ''

            # Find title class
            current_element = 'h1'
            current_class = 'page-headline'
            title_class = headers_class.find(current_element, class_=current_class)
            if not title_class:
                logging.warning(f"Target {current_element} '{current_class}' related to title_class not found in the HTML.")
                return ''
            
            # Extract title
            title = title_class.get_text(strip=True) if title_class else 'No Title Found'

            # Find sub-title class
            current_element = 'p'
            current_class = 'sub-title'
            sub_title_class = headers_class.find(current_element, class_=current_class)
            if not sub_title_class:
                logging.warning(f"Target {current_element} '{current_class}' related to sub_title_class not found in the HTML.")
                return ''
            
            # Extract sub-title
            sub_title = sub_title_class.get_text(strip=True) if sub_title_class else 'No sub-title Found'

            ## CONTENT
            # Find content class
            current_element = 'div'
            current_class = 'article-body'
            article_content = article_main_class.find(current_element, class_=current_class)
            if not article_content:
                logging.warning(f"Target {current_element} '{current_class}' related to article_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            header_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
            list_types = ['ul', 'ol']

            unwanted_header_substrings = [
                "MITRE",
                "Network",
                "Files",
                "IoCs",
                "Certificate",
                "file paths",
                "Commands",
                "Appendix",
                "Prevention"
                ]
            
            # Define unwanted substrings in paragraphs
            unwanted_paragraph_substrings = [
                "Table"
                ]
            
            # Define unwanted substrings in blockquotes
            unwanted_blockquotes_substrings = ["For any inquiries"]
            
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
                        # Check if the paragraph has class 'download-text'
                        if 'download-text' in element.get('class', []):
                            continue  # Skip this paragraph

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

                # Process blockquotes
                elif element.name == 'blockquote':
                    if not skip_content:
                        # Process div inside the blockquote
                        div_in_blockquote = element.find('div', recursive=False)
                        if div_in_blockquote:
                            # Extract text from div
                                div_text = div_in_blockquote.get_text(separator=' ', strip=True)
                                # Check if list item contains any unwanted substrings
                                if any(substring in div_text for substring in unwanted_blockquotes_substrings):
                                    skip_content = True  # Start skipping content
                                    continue  # Skip this list item
                                if div_text.strip():
                                    content += div_text + '\n\n'
                else:
                    continue
            
            # Combine title + content
            data = f"{title}\n{sub_title}\n\n{content}"

            # Remove any leading/trailing whitespace and get the full article text
            return data.strip()
            
        except Exception as e:
            self.handle_error(e)  # Handle any exceptions using the base class method
            return ''  # Return an empty string if an error occurs
        
# Register the parser instance with the registry
register_parser(WelivesecurityParser())