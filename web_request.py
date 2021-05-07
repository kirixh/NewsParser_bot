import requests
import dateparser
from bs4 import BeautifulSoup


class Parser:
    def __init__(self, url):
        """
        Отправляем запрос на сайт url, полученный html код превращает в soup.
        :param url: ссылка на сайт
        """
        self.url = url
        response = requests.get(self.url)
        response.encoding = 'utf-8'
        self.html = response.text
        self.soup = BeautifulSoup(self.html, "lxml")

    def find_stories(self):
        """
        Находит все темы или статьи.
        :return: {"name":(date, url) }
        """
        news = dict()
        items = self.soup.find_all("div", class_="item__wrap l-col-center")
        for item in items:
            if item.find('span', class_='item__title rm-cm-item-text'):
                date = item.span.text
                date = " ".join(date.split())
                date = dateparser.parse(date)
                name = item.a.text
                name = " ".join(name.split())
                news[name] = (date, item.a['href'])
        return news

    def parse_story(self):
        """
        Парсит статью, находит ее текст и теги.
        :return: (tags, text)
        """
        text = ''
        tags_list = []
        tags = ''
        items = self.soup.find_all("p")
        for item in items:
            text = text + item.text
            if item.text and item.text[0] != '\n':  # если текст не пуст и не начинается с \n
                text += '\n' * 2                    # добавляем отступы
        found_tags = self.soup.find_all("a", class_="article__tags__item")
        for tag in found_tags:
            tags_list.append(tag.text)  # список тегов
        for tag in sorted(tags_list):
            tags += tag + '\n'          # переводим список в одну строку
        return tags, text



