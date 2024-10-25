# Change "your_parser" to the file name of the desired parser
# Change "yourParser" to the relevant class name of the desired parser

from parsers.your_parser import yourParser

if __name__ == '__main__':
    parser = yourParser()
    url = 'Please enter a link here'
    data = parser.fetch_data(url)
    print(data)

    