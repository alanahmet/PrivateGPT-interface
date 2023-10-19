from github import Github
import os
from urllib.parse import urlparse

from paddleocr import PaddleOCR, draw_ocr
from PIL import Image

import imaplib
import email
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
import json
import numpy as np
import requests
from requests.models import MissingSchema
import trafilatura
from langchain.document_loaders import UnstructuredURLLoader
import os


def get_repo(repo_adress):
    g = Github('Github API token')
    parsed_url = urlparse(repo_adress)
    path_components = parsed_url.path.split("/")
    owner = path_components[1]
    repo = path_components[2]
    repo = g.get_repo(f"{owner}/{repo}")
    contents = repo.get_contents("")

    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            try:
                print(f"Downloading {file_content.path}")
                raw_file = file_content.decoded_content
                txt_file_content = raw_file.decode('utf-8')
                os.makedirs("source_documents", exist_ok=True)
                with open(f"source_documents/{file_content.name}.txt", "w", encoding="utf-8") as f:
                    f.write(txt_file_content)
            except:
                print(f"{file_content.name} incompatible")


def paddle_ocr(path, print_line=True, save_img=False):
    ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)
    font_path = './fonts/simfang.ttf'
    img_path = path
    result = ocr.ocr(img_path, cls=True)
    result_array = [res[1][0] for res in result[0]]

    text_file_name = path.split("/")[-1]
    list_as_text = '\n'.join(result_array)  # separate elements with a
    with open("source_documents/" + text_file_name + ".txt", 'w') as file:
        file.write(list_as_text)

    if print_line:
        for idx in range(len(result)):
            res = result[idx]
            for line in res:
                print(line)

    if save_img:
        result_path = "./ocr_result"
        if not os.path.exists(result_path):
            os.makedirs(result_path)
        result = result[0]
        image = Image.open(img_path).convert('RGB')
        boxes = [line[0] for line in result]
        txts = [line[1][0] for line in result]
        scores = [line[1][1] for line in result]
        im_show = draw_ocr(image, boxes, txts, scores, font_path=font_path)
        im_show = Image.fromarray(im_show)
        name_number = 1
        while os.path.exists(result_path + "/result" + str(name_number) + ".jpg"):
            name_number += 1
        im_show.save(result_path + "/result" + str(name_number) + ".jpg")


def get_mails(username, password):
    username = username
    password = password

    server = imaplib.IMAP4_SSL("imap.gmail.com")
    server.login(username, password)
    server.select("INBOX")

    date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    search_criteria = f'(SINCE "{date_since}")'

    status, data = server.search(None, search_criteria)
    message_ids = data[0].split()

    for id in message_ids:
        status, data = server.fetch(
            id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])")
        msg = email.message_from_bytes(data[0][1])
        subject = msg.get("Subject", "")
        sender = msg.get("From", "")
        print(f"{subject} from {sender}")

    # write the messages to a text file
    with open("./source_documents/mails.txt", "w") as file:
        for id in message_ids:
            status, data = server.fetch(id, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            file.write(f"From: {msg['From']}")
            file.write(f"Subject: {msg['Subject']}")
            file.write(f"Date: {msg['Date']}")
            file.write(msg.get_payload())
            file.write("=====================")


def get_web_data(url, file_name):
    response = requests.get(url)
    content = response.text

    file_path = './source_documents/' + file_name + ".txt"
    with open(file_path, 'w', encoding="utf-8") as f:
        f.write(content)

    f.close()


def beautifulsoup_extract_text_fallback(response_content):
    '''
    This is a fallback function, so that we can always return a value for text content.
    Even for when both Trafilatura and BeautifulSoup are unable to extract the text from a 
    single URL.
    '''

    soup = BeautifulSoup(response_content, 'html.parser')

    text = soup.find_all(text=True)

    cleaned_text = ''
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head',
        'input',
        'script',
        'style',]

    for item in text:
        if item.parent.name not in blacklist:
            cleaned_text += '{} '.format(item)

    cleaned_text = cleaned_text.replace('\t', '')
    return cleaned_text.strip()


def extract_text_from_single_web_page(url):

    downloaded_url = trafilatura.fetch_url(url)
    try:
        a = trafilatura.extract(downloaded_url, output_format="json", with_metadata=True, include_comments=False,
                                date_extraction_params={'extensive_search': True, 'original_date': True})
    except AttributeError:
        a = trafilatura.extract(downloaded_url, json_output=True, with_metadata=True,
                                date_extraction_params={'extensive_search': True, 'original_date': True})
    if a:
        json_output = json.loads(a)
        return json_output['text']
    else:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return beautifulsoup_extract_text_fallback(resp.content)
            else:
                return np.nan
        except MissingSchema:
            return np.nan


def get_web_text(url, filename):
    single_url = url
    text = extract_text_from_single_web_page(url=single_url)
    file_path = './source_documents/' + filename + ".txt"
    with open(file_path, 'w', encoding="utf-8") as f:
        f.write(text)

    f.close()


def langchain_web_scraping(website_list):
    loader = [UnstructuredURLLoader(urls=website_list)]
    while loader:
        web_contents_objects = loader.pop()
        web_contents = web_contents_objects.load()

        for content in web_contents:
            file_name = str(content.metadata["source"]).split("/")[-2]
            save_path = "web_scaps"

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            print(save_path, file_name, content.metadata["source"])
            with open(save_path + "/" + file_name + ".txt", "w") as file:
                content = content.page_content
                file.write(content)
