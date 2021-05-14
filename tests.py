import datetime
import nltk
import unittest
from bot_functions import analyse_flags, nltk_convers
from web_request import Parser


class CommandTest(unittest.TestCase):

    def setUp(self):  # Срабатывает каждый раз при запуске тестов
        self.parser1 = Parser('https://www.rbc.ru/story/6009a4899a79471a2909f35a')
        self.parser2 = Parser('https://www.rbc.ru/rbcfreenews/609a20029a7947068a8b7cf8')
        nltk.download('punkt')
        nltk.download('stopwords')

    def test_analyse_flags(self):  # Если вывод команды совпадает со списком имён настоящего пути.
        self.assertEqual(analyse_flags("Зеленский планирует встретиться с Путиным."
                                       " На встрече обсудят сотрудничество в сфере борьбы"
                                       " с коронавирусом и взаимной помощи."), ['🇺🇦', '🇷🇺', '🦠'])

    def test_nltk_convers(self):  # Если вывод команды совпадает с данным списком частот.
        self.assertEqual(nltk_convers("Маша пришла кушать кашу. Каша не была вкусной,"
                                      " так что она стала кушать борщ.").most_common(3),
                         [('кушать', 2), ('маша', 1), ('пришла', 1)])

    def test_find_stories(self):  # Если статья с данным названием имеет данные дату и ссылку.
        self.assertEqual(self.parser1.find_stories()['В Москве раньше срока откроют'
                                                     ' закрытый участок салатовой ветки метро'],
                         (datetime.datetime(2021, 5, 13, 12, 31),
                          'https://www.rbc.ru/rbcfreenews/609ceeeb9a79476c5fdb4a3f'))

    def test_parse_story(self):  # Если найденные теги совпадают с данными.
        self.assertEqual(self.parser2.parse_story()[0], 'ЖКХ\nМосква\nгорячая вода\nотключение\n')


if __name__ == "__main__":
    unittest.main()
