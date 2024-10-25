# This file defines the base class ParserBase that all individual parsers inherit from

import logging
from abc import ABC, abstractmethod
from urllib.parse import urlparse

# Configures the logging system to output messages with a timestamp, severity level, and message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

# The base class for all parsers. It defines the interface and common methods.
class ParserBase(ABC): 

    # Abstract method to fetch data from a given URL
    @abstractmethod
    def fetch_data(self):
        raise NotImplementedError("Subclasses must implement the fetch_data method.")
    
    # Determines if the parser can handle the given URL
    @abstractmethod
    def can_handle(self, url):
        pass

    # Handles errors that occur during data fetching
    def handle_error(self, error):
        logging.error(f"Error in {self.__class__.__name__}: {error}")