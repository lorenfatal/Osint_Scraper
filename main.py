# This file includes the scraping process using the parsers

from openai import AzureOpenAI
import httpx
import requests
import datetime
import json
import os
import re
import logging
import yaml
from parsers import parser_registry

# Load files from the configuration folder
def load_config(config_file_path):
    try:
        with open(config_file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logging.error(f"Error reading configuration file: {e}")
        return {}

# Read URLs from a text file
def read_links_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            links_file_content = file.read()

        # Extract URLs (assuming they are separated by spaces or newlines)
        links_list = re.findall(r'https?://\S+', links_file_content)
        return links_list

    except Exception as e:
        logging.error(f"Error reading links from file: {e}")
        return []

# Find a parser that can handle the given URL
def find_parser_for_url(url):
    for parser in parser_registry:
        if parser.can_handle(url):
            return parser
    return None

# Load the prompt template from a text file
def load_prompt(prompt_file_path):
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as file:
            prompt_template = file.read()
        return prompt_template
    except Exception as e:
        logging.error(f"Error reading prompt from file: {e}")
        return ""

# Load GPT API key from a text file
def load_gpt_api(gpt_file_path):
    try:
        with open(gpt_file_path, 'r', encoding='utf-8') as file:
            gpt_api_key = file.read()
        return gpt_api_key
    except Exception as e:
        logging.error(f"Error reading GPT API key from file: {e}")
        return ""

def main():
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("scraper.log"),
            logging.StreamHandler()
        ]
    )

    ## Configurations
    # Load configuration
    config_file_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    config = load_config(config_file_path)

    # Get the prompt file path from configuration
    prompt_file_relative = config.get('prompt_file')
    if not prompt_file_relative:
        logging.error("Prompt file path not specified in the configuration.")
        return
    
    # Load GPT prompt
    prompt_file_path = os.path.join(os.path.dirname(__file__), prompt_file_relative)
    prompt_template = load_prompt(prompt_file_path)
    if not prompt_template:
        logging.error("Prompt template is empty. Ends program.")
        return
    
    # Get the GPT API key file path from configuration
    gpt_file_relative = config.get('gpt_api_key_file')
    if not gpt_file_relative:
        logging.error("GPT API key file path not specified in the configuration.")
        return
    
    # Load GPT API key prompt
    gpt_file_path = os.path.join(os.path.dirname(__file__), gpt_file_relative)
    gpt_api_key = load_gpt_api(gpt_file_path)
    if not gpt_api_key:
        logging.error("GPT API key is empty. Ends program.")
        return

    # Path to user's home directory
    home_directory = os.path.expanduser('~')
    urls_filename = "urls.txt"

    # Path to the text file where the links are stored
    links_file_path = os.path.join(home_directory, 'Osint_Scraper', urls_filename)

    # Read links from the file
    links_list = read_links_from_file(links_file_path)

    if not links_list:
        logging.info("No links found to process.")
        return

    # GPT API, model and version set up 
    GPT_API_KEY = gpt_api_key
    ENDPOINT = "Please enter your endpoint here"
    GPT_MODEL = "Please enter desired GPT model"
    GPT_API_VERSION = "Please enter desired API version"

    client = AzureOpenAI(
        azure_endpoint = ENDPOINT, 
        api_key = GPT_API_KEY, 
        api_version = GPT_API_VERSION,
        http_client = httpx.Client(verify = False)
    )

    # Extracting article text from link (using relevant parser)
    # Taking each text to GPT with prompt and inserting result to json file
    for curr_link in links_list:
        logging.info(f"Processing URL: {curr_link}")
        parser = find_parser_for_url(curr_link)
        if parser:
            data = parser.fetch_data(curr_link)
            if data:
                # Prepare the prompt by inserting the article data
                prompt_w_article_text = prompt_template.format(data=data)

                # Initialize extracted_data
                extracted_data = None

                # Call the GPT API
                try:
                    GPT_RES = client.chat.completions.create(
                        model = GPT_MODEL, 
                        messages=[
                            {"role": "user", "content": prompt_w_article_text}
                        ]
                    )

                    # Extract and parse the content
                    final_content = GPT_RES.choices[0].message.content

                    # Setting 'createdDate' field
                    now = datetime.datetime.now()
                    item_formatted_datetime = now.strftime("%Y-%m-%dT%H:%M:%S")

                    # Osint item structure - Parsing format for json file
                    extracted_data = {
                            "title": "",
                            "summary": """""",
                            "createdDate": item_formatted_datetime,
                            "source": curr_link
                            # Add more fields as you wish
                    }

                    for line in final_content.strip().split('\n'):
                        if ': ' in line:  # Ensure there's a key-value format in the line
                            key, value = line.split(': ', 1)
                            key = key.strip()
                            value = value.strip()
                            value = value.strip('"')  # Remove extra quotes from value
                            if key in extracted_data:  # Make sure it's a valid key
                                if value:  # Check if the value is not empty
                                    if isinstance(extracted_data[key], list):
                                        # Handle list values
                                        extracted_data[key] = value.split(', ')
                                    else:
                                        # Handle non-list values
                                        extracted_data[key] = value

                    # Empty fields handling
                    must_fields = ["title", "summary", "createdDate", "source"]

                    for field in must_fields:
                        # Retrieve the field value (could be None if the field does not exist)
                        field_value = extracted_data.get(field, "")
                        # Check if the field value is empty
                        if not field_value:
                            print(f"Field '{field}' is empty. Can't proceed with item creation. article link: {curr_link}")
                            break

                except Exception as e:
                    logging.error(f"Error calling GPT API for {curr_link}: {e}")

                # Output folder definition (downloads folder)
                downloads_directory = os.path.join(home_directory, 'Downloads')
                current_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                file_name = f"data_output_{current_time}.json"
                file_path = os.path.join(downloads_directory, file_name)

                # Write the data to a JSON file
                with open(file_path, "w") as json_file:
                    json.dump(extracted_data, json_file, indent=4)

            else:
                logging.warning(f"No data returned from {curr_link}")
        else:
            logging.warning(f"No parser found for URL: {curr_link}")

if __name__ == '__main__':
    main()
