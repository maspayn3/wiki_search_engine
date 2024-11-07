#!/usr/bin/env python3
import sys
import csv
import re
import os


sys.path.append(os.path.dirname(__file__))


csv.field_size_limit(sys.maxsize)

def clean_text(text):
    """Prepares text for usage in an inverted index."""
    # removes non alphanumerics and case sensitivity
    text = re.sub (r"[^a-zA-Z0-9 ]+", "", text)
    text = text.casefold()

    # split text into list of whitespace-deliminated words
    text = text.split()

    with open("stopwords.txt", mode='r', encoding='utf-8') as file:
        stop_words = [word.strip() for word in file]

    # remove stop words from body of text
    # for word in text:
    #     if word in stop_words:
    #         text.remove(word)
    word_list = [word for word in text if word not in stop_words]
    return word_list

def map1():
    # input format: DOC_ID, TITLE, BODY
    for row in csv.reader(sys.stdin):
        # print(row, "\n")
        doc_id, title, body = row
        
        # combine title and body
        body = body + " " + title

        word_list = clean_text(body)
        
        for word in word_list:
            print(f"{word} {doc_id}\t{1}")
            

if __name__ == "__main__":
    map1()