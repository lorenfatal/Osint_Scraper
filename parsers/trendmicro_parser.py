from .parser_base import ParserBase
from . import register_parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

# Parser for Trend Micro site, inheriting from ParserBase
class TrendMicroParser(ParserBase):

    # Checks if this parser can handle the given URL
    def can_handle(self, url):
        domain = urlparse(url).netloc.lower()
        return domain.endswith('trendmicro.com')

    def fetch_data(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # Headers to mimic a browser
            response = requests.get(url, headers=headers, timeout=10)  # Make the HTTP request
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content

            ### Finding the required elements in the html
            # Find main class 'site-main'
            current_class = 'research-layout--wrapper row'
            article_main_class = soup.find('article', class_=current_class)
            if not article_main_class:
                logging.warning(f"Article class '{current_class}' related to article_main_class not found in the HTML.")
                return ''
            
            ## TITLE
            # Find title
            current_class = 'article-details__title'
            article_title = article_main_class.find('h1', class_=current_class)
            if not article_title:
                logging.warning(f"Target class '{current_class}' related to article_title not found in the HTML.")
                return ''
            
            # Extract title
            title = article_title.get_text(strip=True) if article_title else 'No Title Found'

            # Find sub-title
            current_class = 'article-details__description'
            article_sub_title = article_main_class.find('p', class_=current_class)
            if not article_sub_title:
                logging.warning(f"Target sub-class '{current_class}' related to article_sub_title not found in the HTML.")
                return ''
            
            # Extract sub-title
            sub_title = article_sub_title.get_text(strip=True) if article_sub_title else 'No Sub-Title Found'

            ## CONTENT
            # Find content class
            current_class = 'main--content col-xs-12 col-lg-8 col-lg-push-2'
            article_main_content = article_main_class.find('main', class_=current_class)
            if not article_main_content:
                logging.warning(f"Target class '{current_class}' related to article_main_content not found in the HTML.")
                return ''

            # Extract full article content
            content = ''
            summary_class = 'rich-text-li'
            unwanted_headers = ['Trend Micro Vision One Threat Intelligence', 'Hunting Queries', 'Indicators of Compromise (IOCs)']
            unwanted_paragraphs = ['Trend Micro Vision One Intelligence Reports App [IOC Sweeping]', 'Trend Micro Vision One Threat Insights App', 'MITRE ATT&CK® techniques']

            # Find all <h4> tags
            for h4 in article_main_content.find_all('h4'):
                current_title = h4.get_text(strip=True)
                if current_title not in unwanted_headers:
                    content += current_title + '\n' # Add newline after the title
                
                    # Find all <p> tags within the same section
                    next_node = h4.find_next_sibling()
                    while next_node and next_node.name != 'h4':
                        if next_node.name == 'p':
                            paragraph_text = next_node.get_text(separator=' ', strip=True)
                            if paragraph_text not in unwanted_paragraphs:
                                content += paragraph_text + '\n\n'  # Add two newlines between paragraphs
                            else:
                                pass
                        elif next_node.name == 'ul':
                        # Extract 'Summary' content
                            summary_paragraphs = next_node.find_all('li', class_=summary_class)
                            if summary_paragraphs:
                                for li in summary_paragraphs:
                                    summary_paragraph_text = li.get_text(separator=' ', strip=True)
                                    content += summary_paragraph_text + '\n\n'  # Add two newlines between items
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
register_parser(TrendMicroParser())