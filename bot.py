import time
import urllib.parse
import aiohttp
import re
import json
import os
from aiogram import Bot, Dispatcher, executor, types
from langdetect import detect
from bs4 import BeautifulSoup

KEY_TRANSLATE = os.environ.get('KEY_TRANSLATE')
proxy_host = os.environ.get('socks5://py.manytask.org:1080')
proxy_credentials = os.environ.get('student:JGNICRoFHftRqllRh3O0xi0sfbhmLyt7')
if proxy_credentials:
    login, password = proxy_credentials.split(':')
    proxy_auth = aiohttp.BasicAuth(login=login, password=password)
else:
    proxy_auth = None

bot = Bot(token=os.environ.get('BOT_TOKEN'),
          proxy=proxy_host, proxy_auth=proxy_auth)
dp = Dispatcher(bot)


@dp.message_handler(commands=['help', 'start'])
async def send_welcome(message: types.Message):
    await message.reply(
        "<b>Привет!</b>\nЭтот бот поможет вам найти информацию о\nвашем любимом фильме на imdb и посмотреть его на\n"
        "ivi.ru, если он там есть. Для этого вам необхожимо написать название  фильма этому боту.\nДля повторного просмотра этого сообщения "
        "нажмите /help.\nПриятного просмотра!",
        parse_mode='HTML')


@dp.message_handler()
async def false(message):
    if message.text.startswith('/'):
        await bot.send_message(message.chat.id,
                               'У меня нет такой команды, попробуйте \n/help для просмотра возможностей',
                               parse_mode='HTML')
    else:
        await cinema(message)


# async def find_on_ivi(film):


@dp.message_handler()
async def cinema(message: types.Message):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    s = ' '
    try:
        ADRESS = "https://translate.yandex.net/api/v1.5/tr.json/detect"
        KEY = KEY_TRANSLATE
        params = {
            "key": KEY,
            "text": message.text,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(ADRESS, data=params) as resp:
                tran = await resp.json()
        lang = tran["lang"]
        print(lang)
        if lang != 'en':
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
            try:
                inf = await kinopoisk(message, headers)
                s += 'Информацию об интересующем вас фильме на русском вы найдете по адресу\n'
                s += 'https://www.kinopoisk.ru/{}'.format(inf) + '\n'
                await bot.send_message(message.chat.id, s, parse_mode='HTML')
            except Exception:
                pass

        else:
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
                s = 'Ссылок не нашлось.\nВозможно, вы сможете увдиеть его тут: ' + url
                await bot.send_message(message.chat.id, s, parse_mode='HTML')


@dp.message_handler()
async def get_ivi_films(message, headers):
    url = 'http://ivi.ru/search/?q={}'.format(message["text"])
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


# к сожалению на сайт не пускает(хотя отдельно от бота работает -_-)
@dp.message_handler()
async def parse_anime(message, headers):
    film = message['text']
    url = 'https://yummyanime.club/search?word={}'.format(film)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            tran = await resp.text()

    soap = BeautifulSoup(tran)
    first_search_result = soap.findAll('div', {'class': 'content-page search-page'})
    print(first_search_result)
    adress = re.findall(r'href=[\'"]?([^\'" >]+)', str(first_search_result))
    anime_adress = 'https://yummyanime.club' + adress[0]
    print(anime_adress)
    async with aiohttp.ClientSession() as session:
        async with session.post(anime_adress, headers=headers) as next_resp:
            tran_next = await next_resp.text()
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
        msg += 'Серий: <b>' + series[0] + '<b>q\n'
        msg += 'Студия: <b>' + studio[0] + '<b>\n'
        msg += 'Жанры: '
        for gan in genre:
            msg += '<b>' + gan + '<b> '
        msg += '\n'
        msg += 'Посмотреть это аниме можно тут: \n' + anime_adress
    else:
        msg = "no anime"

    await bot.send_message(message.chat.id, msg, parse_mode='HTML')


@dp.message_handler()
async def kinopoisk(message, headers):
    url = 'https://www.kinopoisk.ru/index.php?kp_query={}'.format(message.text)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            tran = await resp.text()
    soap = BeautifulSoup(tran)

    main_search_result = soap.findAll('div', {'class': 'element most_wanted'})[0]
    adress = main_search_result.findAll('li')
    kinopoiskid = int(re.findall(r'data-id=(.*?) ', str(adress))[0][1:-1])
    return 'film/' + str(kinopoiskid)

@dp.message_handler()
async def imdb(message, headers):
    film = message.text

    url = 'http://www.omdbapi.com/?s={}&apikey=7a6406be'.format(film)
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
        s = 'Название: ' + values.get('Title') \
            + '\nГод выпуска: ' + values.get('Year') \
            + '\nДлительность:' + values.get('Runtime') \
            + '\nДиректор: ' + values.get('Director') \
            + '\nРежиссер: ' + values.get('Actors') \
            + '\nСтрана: ' + values.get('Country') \
            + '\nРейтинг IMDb:' + values.get('imdbRating') \
            + '\nОписание: ' + values.get('Plot') \
            + '\n\n' + values.get('Poster')
        await bot.send_message(message.chat.id, s, parse_mode='HTML')
    else:
        raise NameError


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
