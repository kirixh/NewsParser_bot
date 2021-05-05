import requests
import dateparser
from bs4 import BeautifulSoup
import time


class Parser:
    def __init__(self, url):
        self.url = url
        response = requests.get(self.url)
        response.encoding = 'utf-8'
        self.html = response.text
        self.soup = BeautifulSoup(self.html, "lxml")

    def find_stories(self):
        news = dict()
        items = self.soup.find_all("div", class_="item__wrap l-col-center")
        for item in items:
            if item.find('span', class_='item__title rm-cm-item-text') is not None:
                date = item.span.text
                date = " ".join(date.split())
                date = dateparser.parse(date)
                name = item.a.text
                name = " ".join(name.split())
                # print(item.span.text)
                news[name] = (date, item.a['href'])
            # print(item)
        return news

    def parse_story(self):
        text = ''
        tags_list = []
        tags = ''
        items = self.soup.find_all("p")
        for item in items:
            text = text + item.text
            if item.text and item.text[0] != '\n':
                text += '\n' * 2
        found_tags = self.soup.find_all("a", class_="article__tags__item")
        for tag in found_tags:
            tags_list.append(tag.text)
        for tag in sorted(tags_list):
            tags += tag + '\n'
        return tags, text


t1 = time.time()
print(Parser('https://www.rbc.ru/story/').find_stories())
t2 = time.time()
print("Time of execution: ", t2 - t1)

"""with open('rbc.html', 'w') as file:
    response = requests.get('https://www.rbc.ru/story/')
    response.encoding = 'utf-8'
    file.write(response.text)
with open('rbc.html', 'r') as file:
    html = file.read()"""

# print(html)
# soup = BeautifulSoup(html, "lxml")

"""
def find_stories(b_soup):
    news = dict()
    items = b_soup.find_all("div", class_="item__wrap l-col-center")
    for item in items:
        if item.find('span', class_='item__title rm-cm-item-text') is not None:
            date = item.span.text
            date = " ".join(date.split())
            name = item.a.text
            name = " ".join(name.split())
            # print(item.span.text)
            news[name] = (date, item.a['href'])  # добавить скачивание изображений в бд
        # print(item)
    return news


def parse_story(b_soup):
    text = ''
    tags = []
    items = b_soup.find_all("p")
    for item in items:
        text = text + item.text
        if item.text[0] != '\n':
            text += '\n' * 2
    found_tags = b_soup.find_all("a", class_="article__tags__item")
    for tag in found_tags:
        tags.append(tag.text)
    return tags, text


themes = find_stories(soup)
print(themes)
with open('rbc_theme.html', 'w') as file:
    response = requests.get(themes["Дело Навального"][1])
    response.encoding = 'utf-8'
    file.write(response.text)
with open('rbc_theme.html', 'r') as file:
    html = file.read()
soup = BeautifulSoup(html, "lxml")
stories = find_stories(soup)
print(stories)
with open('rbc_story.html', 'w') as file:
    response = requests.get(stories["Суд принял к производству иск Навального к Пескову"][1])
    response.encoding = 'utf-8'
    file.write(response.text)
with open('rbc_story.html', 'r') as file:
    html = file.read()
soup = BeautifulSoup(html, 'lxml')
print(parse_story(soup)[1])"""
