import requests
from bs4 import BeautifulSoup
import dateparser

with open('rbc.html', 'w') as file:
    response = requests.get('https://www.rbc.ru/story/')
    response.encoding = 'utf-8'
    file.write(response.text)
with open('rbc.html', 'r') as file:
    html = file.read()
# print(html)
soup = BeautifulSoup(html, "lxml")


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

