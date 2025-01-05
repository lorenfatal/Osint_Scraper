# To manually check access for specific URLs, run the script from this path C:\Users\yourusername\Osint_Scraper in the command line:
# python -m utils.access_checker

import urllib.robotparser
from urllib.parse import urlparse
import requests
import random
from .user_agents import USER_AGENTS  # Import user_agents file
from .logger import setup_logger
import sys
import logging

# Initialize logger
logger = setup_logger(__name__)

# Initialize user agent
user_agent = random.choice(USER_AGENTS)

def test_robotparser():
    robots_txt = """
    User-agent: *
    Disallow: /media/
    Disallow: /blog/wp-admin/
    Disallow: /wp-admin/
    """

    rp = urllib.robotparser.RobotFileParser()
    rp.parse(robots_txt.splitlines())

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                 " Chrome/115.0.0.0 Safari/537.36 OPR/101.0.0.0"
    path_allowed = "/"
    path_disallowed = "/media/"

    allowed = rp.can_fetch(user_agent, path_allowed)
    disallowed = rp.can_fetch(user_agent, path_disallowed)

    print(f"Can fetch '{path_allowed}': {allowed}")       # Expected: True
    print(f"Can fetch '{path_disallowed}': {disallowed}") # Expected: False

# Test test_robotparser
'''
test_robotparser()
exit()
'''

def can_fetch(url, user_agent):
    """
    Checks if the specified user_agent can fetch the given URL based on robots.txt.

    Parameters:
        url (str): The URL to check.
        user_agent (str): The user agent string to identify the crawler.

    Returns:
        bool: True if fetching is allowed, False otherwise.
    """
    # Parse the robots.txt URL from the target url.
    parsed_url = urlparse(url)

    # Validate parsed URL
    if not parsed_url.scheme or not parsed_url.netloc:
        logger.error(f"Invalid URL parsed: scheme='{parsed_url.scheme}', netloc='{parsed_url.netloc}'")
        return False

    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    logger.debug(f"Constructed robots.txt URL: {robots_url}")

    # Determine if fetching is allowed
    try:
        response = requests.get(robots_url, headers={'User-Agent': user_agent}, timeout=10)
        response.raise_for_status()
        robots_content = response.text
        logger.debug(f"Fetched robots.txt from {robots_url}:\n{robots_content}")
        
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch robots.txt from {robots_url}: {e}")
        return False
    
    # Extract the path from the URL
    path = parsed_url.path or '/'
    logger.debug(f"Extracted path from URL: {path}")

    # Log the outcome
    is_allowed = rp.can_fetch(user_agent, url)
    logger.debug(f"can_fetch result for {url} with user-agent '{user_agent}': {is_allowed}")

    if is_allowed:
        logger.info(f"Allowed to scrape: {url}")
    else:
        logger.info(f"Not allowed to scrape: {url}")

    return is_allowed

# Test for can_fetch
'''
url = "url"
# In your access checker script
user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
allowed = can_fetch(url, user_agent)
print(f"Can fetch '{url}' with user-agent '{user_agent}': {allowed}")
exit()
'''

def test_access(url, user_agent):
    """
    Tests access to the given URL by making a GET request with custom headers.

    Parameters:
        url (str): The URL to test.
        user_agent (str): The user agent string to identify the crawler.

    Returns:
        bool: True if access is successful (status code 200), False otherwise.
    """

    # Set up custom headers to mimic a real browser
    headers = {
        'User-Agent': user_agent,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/' 
    }

    # Make a GET request with a timeout of 30 seconds
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)

        logger.debug(f"Response headers for {url}: {response.headers}")
        logger.debug(f"Response content for {url} (first 500 characters): {response.text[:500]}")

        # Check the Content-Type to ensure it's HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            logger.warning(f"Unexpected Content-Type for {url}: {content_type}")
            return False

        logger.info(f"Access to {url} successful with status code {response.status_code}.")
        return True

    # Check for HTTP errors & unexpected content and logs the outcome
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while accessing {url}: {http_err}")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred while accessing {url}.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Error occurred while accessing {url}: {req_err}")

    return False

def is_scraping_allowed(url, user_agent):
    """
    Combines robots.txt compliance and a test HTTP request to determine if scraping is allowed.

    Parameters:
        url (str): The URL to check.
        user_agent (str): The user agent string to identify the crawler.

    Returns:
        bool: True if scraping is allowed and accessible, False otherwise.
    """
    
    logger.info(f"Starting scraping check for: {url} with User-Agent: {user_agent}")

    # Call can_fetch to check robots.txt
    if not can_fetch(url, user_agent):
        logger.info(f"Scraping disallowed by robots.txt for {url}.")
        return False
    
    logger.info(f"robots.txt allows scraping for {url}. Proceeding to test access.")

    # If allowed, call test_access to verify accessibility
    if not test_access(url, user_agent):
        logger.info(f"Access to {url} is blocked or returned unexpected content.")
        return False
    
    logger.info(f"Scraping is allowed and access is confirmed for {url}.")

    # Return True only if both checks pass
    return True

def main():
    """
    Main function to perform access checks on provided URLs.
    """
    # Prompt user to enter URLs separated by spaces or commas
    input_urls = input("Enter URLs separated by spaces or commas: ").strip()

    if not input_urls:
        print("No URLs provided. Exiting.")
        sys.exit(1)

    # Split the input into a list of URLs
    if ',' in input_urls:
        urls = [url.strip() for url in input_urls.split(',') if url.strip()]
    else:
        urls = [url.strip() for url in input_urls.split() if url.strip()]

    if not urls:
        print("No valid URLs provided. Exiting.")
        sys.exit(1)

    logger.info(f"Using User-Agent: {user_agent}")

    for url in urls:
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            # Try HTTPS first
            test_https = f"https://{url}"
            try:
                resp = requests.head(test_https, timeout=5)
                if resp.status_code < 400:
                    url = test_https
                    logger.debug(f"HTTPS is supported. Updated URL to: {url}")
                else:
                    url = f"http://{url}"
                    logger.debug(f"HTTPS responded with status {resp.status_code}. Falling back to HTTP: {url}")
            except requests.exceptions.RequestException:
                # If HTTPS fails, fall back to HTTP
                url = f"http://{url}"
                logger.debug(f"HTTPS request failed. Falling back to HTTP: {url}")
        logger.info(f"Checking access for URL: {url}")
        allowed = is_scraping_allowed(url, user_agent)
        if allowed:
            print(f"Allowed to scrape: {url}")
        else:
            print(f"Not allowed to scrape: {url}")

if __name__ == "__main__":
    main()
