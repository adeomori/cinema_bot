import logging
import urllib.parse
import aiohttp
import re
import asyncio
import json
import difflib
import os
from aiogram import Bot, Dispatcher, executor, types
from langdetect import detect
from bs4 import BeautifulSoup
from random import choice

GOOGLE_KEY = 'AIzaSyA9CvGYZwqZvnwuNPlyj4bB5Xf4H0dyqjM'
KEY_TRANSLATE = os.environ.get('KEY_TRANSLATE',
                               'trnsl.1.1.20200127T183129Z.78b55e8b4e771851.2b3c7bc51353baeaba46fd294621a1d787cded42')
proxy_host = os.environ.get('socks5://py.manytask.org:1080')
proxy_credentials = os.environ.get('student:JGNICRoFHftRqllRh3O0xi0sfbhmLyt7')
if proxy_credentials:
    login, password = proxy_credentials.split(':')
    proxy_auth = aiohttp.BasicAuth(login=login, password=password)
else:
    proxy_auth = None

bot = Bot(token=os.environ.get('BOT_TOKEN', '600735080:AAHCtSng410JMbkQ3_qpD-Bh77bE0sl7Kgs'),
          proxy=proxy_host, proxy_auth=proxy_auth)
dp = Dispatcher(bot)

#
# @dp.message_handler(commands=['ref'])
# async def create_random_id(message):
#     global list_id_film
#     new_list_id_film = []
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
#     }
#     url = 'https://www.ivi.ru/movies'
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, headers=headers) as resp:
#             text = await resp.text()
#     janr = re.findall(r'(?<=href=")[\w/]+(?=")', text)
#     janrlist = []
#     for elem in janr:
#         if elem[:4] == '/mov' and elem != '/movies' and elem != '/series' and elem != '/movies/erotika':
#             janrlist.append(elem)
#     urls = []
#     for elem in janrlist:
#         urls.append('https://www.ivi.ru' + elem)
#     for url in urls:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, headers=headers) as resp:
#                 text = await resp.text()
#                 film = re.findall(r'(?<=href="/watch/)[\d]+', text)
#                 for id_ in film:
#                     new_list_id_film.append(id_)
#     new_list_id_film = sorted(new_list_id_film)
#     prev = new_list_id_film[0]
#     list_id_film = []
#     for elem in new_list_id_film:
#         if elem != prev:
#             list_id_film.append(elem)
#             prev = elem
#     await asyncio.sleep(3600 * 24)


@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when client send `/start` or `/help` commands.
    """
    await message.reply(
        "Hello!\n   I would like to help you find information about the film.\n\n<i>Possible commands:</i> "
        "\n<b>Movie title</b>:"
        " to search film, its description and ratings \n<b>/random</b>: to get random film "
        " \n\n <i>example:</i> \n  веном\n Команды, доступные боту:\n /random - предлагает случайный фильм\n /help",
        parse_mode='HTML')


@dp.message_handler()
async def false(message):
    if message.text.startswith('/'):
        await bot.send_message(message.chat.id, 'У меня нет такой команды, попробуйте '
                                                '\n/help для просмотра возможностей', parse_mode='HTML')
    else:
        await cinema(message)


# async def find_on_ivi(film):


@dp.message_handler()
async def cinema(message: types.Message, *args):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    question = message.text
    s = ''
    try:

        try:
            lang = detect(message.text)
            if  lang != 'uk':
                ADRESS = "https://translate.yandex.net/api/v1.5/tr.json/translate"
                KEY = KEY_TRANSLATE
                params = {
                    "key": KEY,
                    "text": message.text,
                    "lang": "ru-en",
                    "format": "plain"
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(ADRESS, data=params) as resp:
                        tran = await resp.text()
                        quest = json.loads(tran)['text'][0]
                        print(quest)
        except Exception:
            pass
        message['text'] = quest
        await imdb(message, headers)
        await get_ivi_films(message, headers)
    except Exception:
        question = message.text
        try:
            await imdb(message, headers)

        except Exception:
            try:
                await get_ivi_films(message, headers)
            except Exception:
                url = 'https://vk.com/video?len=2&q={}'.format(urllib.parse.quote(question))
                s = 'Описание не нашлось.\nСмотреть: ' + url
                await bot.send_message(message.chat.id, s, parse_mode='HTML')


@dp.message_handler()
async def get_ivi_films(message, headers):
    # print(message["text"])
    url = 'http://ivi.ru/search/?q={}'.format(message["text"])
    print(url)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            tran = await resp.text()
    soap = BeautifulSoup(tran)
    found_films = soap.findAll('li', {'class': 'gallery__item'})
    i = 0
    s = 'Этот фильм есть на ivi.\n'
    if len(found_films) > 0:
        if len(found_films) == 1:
            s += 'Его можно посмотреть по этой ссылке:\n'
        else:
            s += 'Его можно посмотреть по одной из этих ссылок:'
        while i < min(4, len(found_films)):
            found_film = str(found_films[i])
            ivi_url = 'http://ivi.ru' + re.findall(r'(?<=href=")[\w/]+(?=")', found_film)[0]
            s += ivi_url + '\n'
            i += 1
    else:
        s = 'К сожалению, этого фильма нету на ivi\n'
        raise NameError
    await bot.send_message(message.chat.id, s, parse_mode='HTML')

#к сожалению на сайт не пускает
@dp.message_handler()
async def parse_anime(message, headers):
    film = message['text']
    print(film)
    url = 'https://yummyanime.club/search?word={}'.format(film)
    print(url)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            tran = await resp.text()

    soap = BeautifulSoup(tran)
    print(soap)
    first_search_result = soap.findAll('div', {'class': 'content-page search-page'})
    print(first_search_result)
    adress = re.findall(r'href=[\'"]?([^\'" >]+)', str(first_search_result))
    anime_adress = 'https://yummyanime.club' + adress[0]
    print(anime_adress)
    async with aiohttp.ClientSession() as session:
        async with session.post(anime_adress, headers=headers) as next_resp:
            tran_next = await next_resp.text()
    # resp_new = requests.get(film_adress)
    soap = BeautifulSoup(tran_next)
    info = soap.find('ul', {'class': 'content-main-info'})
    year = re.findall(r"Год: </span>(.*?)</li>", str(info))
    genre_studio = re.findall(r"\">(.*?)</a></li>", str(info))
    genre = genre_studio[: -1]
    studio = genre_studio[-1]
    series = re.findall(r"Серии:</span>(.*?)</li> ", str(info))
    if len(year) == 1:
        msg = ''
        msg += 'Год выпуска: <b>' + year[0] + '<b>\n'
        msg += 'Серий: <b>' + series[0] + '<b>\n'
        msg += 'Студия: <b>' + studio[0] + '<b>\n'
        msg += 'Жанры: '
        for gan in genre:
            msg += '<b>' + gan + '<b> '
        msg += '\n'
        msg += 'Посмотреть это аниме можно тут: \n' + anime_adress
    else:
        msg = "no anime"

    print(msg)
    await bot.send_message(message.chat.id, msg, parse_mode='HTML')

@dp.message_handler()
async def imdb(message, headers):
    film = message.text

    url = 'http://www.omdbapi.com/?s={}&apikey=7a6406be'.format(urllib.parse.quote(film))
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            response = await resp.text()
    data = json.loads(response)
    if data['Response'] == 'True':
        imdbid = data['Search'][0]['imdbID']
        url = 'http://www.omdbapi.com/?i={}&apikey=7a6406be'.format(imdbid)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                response = await resp.text()
        values = json.loads(response)
        s = 'Название: ' + values.get('Title')\
            + '\nГод выпуска: ' + values.get('Year')\
            + '\nДлительность:' + values.get('Runtime')\
            + '\nДиректор: ' + values.get('Director')\
            + '\nРежиссер: ' + values.get('Actors')\
            + '\nСтрана: ' + values.get('Country') \
            + '\nРейтинг IMDb:' + values.get('imdbRating')\
            + '\nОписание: ' + values.get('Plot')\
            + '\n\n' + values.get('Poster')
        url = 'https://vk.com/video?len=2&q={}'.format(urllib.parse.quote(film))
        s += '\nСмотреть:' + url
        await bot.send_message(message.chat.id, s, parse_mode='HTML')
    else:
        raise NameError


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
