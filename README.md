## Web Scraper Project for Osint items generation

## Table of Contents
1. [Introduction](#Introduction)
2. [Features](#Features)
3. [Requirements](#Requirements)
4. [Usage](#Usage)

## Introduction
A modular web scraping project in Python designed to scrape data from multiple pre-defined websites using individual parsers for each site. 
The project includes integration with OpenAI's GPT API to process scraped data into Osint items.

## Features
- **Custom Instructions:** Uses prompt instructions to guide ChatGPT for targeted scraping needs.
- **Configurable:** Easily modify the scraper to adapt to different data sources or parsing requirements.
- **Optimized Data Handling:** Focusing only on relevant data fields.
- **Scalable:** Capable of handling large-scale scraping jobs while maintaining performance.
- **Logging & Debugging:** Built-in logs to help you monitor processes and troubleshoot effectively.

## Requirements
**Python 3**
Make sure you have Python 3 installed on your machine.

**Package Manager (pip)**
You can manage dependencies with pip.

**API Keys / Credentials (as needed)**
The integration with OpenAI's GPT requires API key. Make sure you have it beforehand.

## Usage
1. **Prompt** - Enter your prompt to the prompt.txt file in the config folder.
2. **GPT API key** - Enter your GPT API key to the gpt_api_key.txt file in the config folder.
3. **Urls** - Enter your Urls list to the urls.txt file.
4. **Run the scraper** - Run the following command:
```python
python main.py
```