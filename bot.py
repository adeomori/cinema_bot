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
from random import choice

KEY_TRANSLATE = os.environ['KEY_TRANSLATE']
proxy_host = os.environ.get('PROXY', None)
proxy_credentials = os.environ.get('PROXY_CREDS', None)
if proxy_credentials:
    login, password = proxy_credentials.split(':')
    proxy_auth = aiohttp.BasicAuth(login=login, password=password)
else:
    proxy_auth = None

bot = Bot(token=os.environ['BOT_TOKEN'],
          proxy=proxy_host, proxy_auth=proxy_auth)
dp = Dispatcher(bot)


# @dp.message_handler(commands=['start', 'help'])
# async def send_welcome(message: types.Message):
#     await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler(commands=['ref'])
async def create_random_id(message):
    global list_id_film
    new_list_id_film = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
    }
    url = 'https://www.ivi.ru/movies'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()
    janr = re.findall(r'(?<=href=")[\w/]+(?=")', text)
    janrlist = []
    for elem in janr:
        if elem[:4] == '/mov' and elem != '/movies' and elem != '/series' and elem != '/movies/erotika':
            janrlist.append(elem)
    urls = []
    for elem in janrlist:
        urls.append('https://www.ivi.ru' + elem)
    for url in urls:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                film = re.findall(r'(?<=href="/watch/)[\d]+', text)
                for id_ in film:
                    new_list_id_film.append(id_)
    new_list_id_film = sorted(new_list_id_film)
    prev = new_list_id_film[0]
    list_id_film = []
    for elem in new_list_id_film:
        if elem != prev:
            list_id_film.append(elem)
            prev = elem
    await asyncio.sleep(3600 * 24)

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


@dp.message_handler()
async def cinema(message: types.Message, *args):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
    }
    question = message.text
    s = ''
    try:
        if not args:
            try:
                lang = detect(message.text)
                if lang != 'bg' and lang != 'ru' and lang != 'bg' and lang != 'uk':
                    ADRESS = "https://translate.yandex.net/api/v1.5/tr.json/translate"
                    KEY = KEY_TRANSLATE
                    params = {
                        "key": KEY,
                        "text": message.text + ' w',
                        "lang": "en-ru",
                        "format": "plain"
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(ADRESS, data=params) as resp:
                            tran = await resp.text()
                            question = json.loads(tran)['text'][0][:-2]
            except Exception:
                pass
            url = 'https://duckduckgo.com/html?q={}'.format(urllib.parse.quote(question + ' иви'))
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    text = await resp.text()
            q = re.findall(r'(?<=https://www.ivi.ru/watch/)[\w]+', text)
            if not q:
                url = 'https://www.ivi.ru/search/?q={}'.format(urllib.parse.quote(question))
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as resp:
                        text = await resp.text()
                        q = re.findall(r'(?<=data-content-id=")[\w\d]+(?=")', text)
            url_next = 'https://www.ivi.tv/watch/' + q[0] + '/description' if q[
                0].isdigit() else 'https://www.ivi.tv/watch/' + q[0]
            async with aiohttp.ClientSession() as session:
                async with session.get(url_next, headers=headers) as resp:
                    text_next = await resp.text()
            name = re.findall(r'(?<=<meta name="title" content=").+(?=\))', text_next)
            if not name:
                name = re.findall(r'(?<=<meta name="title" content=")[\s\w\d]+', text_next)
            check = name[0].lower()
            check = check.replace('смотреть онлайн бесплатно все серии подряд в хорошем 720 hd качестве', '')
            check = check.replace('смотреть онлайн бесплатно все серии подряд в хорошем', '')
            check = check.replace('смотреть онлайн все серии подряд в хорошем 720 hd качестве', '')
            check = check.replace('и дополнительные материалы', '')
            check = check.replace('смотреть онлайн', '')
            check = check.replace('фильм ', '')
            check = check.replace('сериал ', '')
            if check[-2].isdigit():
                check = check[:-6]
            similary = difflib.SequenceMatcher(a=check, b=question.lower()).ratio()
            if similary < 0.53:
                raise IndexError
            if similary > 0.8 and similary < 0.9 and not question[-1].isdigit():
                s = 'Возможно вы имели ввиду\n'
            if similary < 0.8:
                s = 'Возможно вы ищите\n'
        else:
            q = [args[0]]
            url_next = 'https://www.ivi.tv/watch/' + q[0] + '/description' if q[
                0].isdigit() else 'https://www.ivi.tv/watch/' + q[0]
            async with aiohttp.ClientSession() as session:
                async with session.get(url_next, headers=headers) as resp:
                    text_next = await resp.text()
            name = re.findall(r'(?<=<meta name="title" content=").+(?=\))', text_next)
            if not name:
                name = re.findall(r'(?<=<meta name="title" content=")[\s\w\d]+', text_next)
        # await parsfilmfromivi(message, text_next, name, headers, s)
    except Exception:
        question = message.text
        # try:
        #     await parsfilmfromkinogo(message, question, headers)
        # except Exception:
        try:
            await imdb(message, headers)
        except Exception:
            url = 'https://vk.com/video?len=2&q={}'.format(urllib.parse.quote(question))
            s = 'Описание не нашлось.\nСмотреть: ' + url
            # try:
            #     url1 = 'https://duckduckgo.com/html?q={}'.format(urllib.parse.quote(question + ' kinogo.by'))
            #     async with aiohttp.ClientSession() as session:
            #         async with session.get(url1, headers=headers) as resp:
            #             text = await resp.text()
            #     g = re.findall(r'(?<=class="result__a" href=").+(?="><b>)', text)
            #     url = g[0]
            #     if url == 'https://kinogo.by/':
            #         url = g[1]
            #     if url.startswith('https://kin'):
            #         s += '\n' + url
            # except Exception:
            #     pass
            await bot.send_message(message.chat.id, s, parse_mode='HTML')


@dp.message_handler()
async def imdb(message, headers):
    question = message.text
    url = 'http://www.omdbapi.com/?s={}&apikey=fdc77053'.format(urllib.parse.quote(question))
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            response = await resp.text()
    values = json.loads(response)
    if values['Response'] == 'True':
        imdbid = values['Search'][0]['imdbID']
        k_equal = difflib.SequenceMatcher(a=question.lower(), b=values['Search'][0]['Title']).ratio()
        for value in values['Search']:
            new_k_equal = difflib.SequenceMatcher(a=value['Title'].lower(), b=question.lower()).ratio()
            if new_k_equal > k_equal:
                imdbid = value['imdbID']
                k_equal = new_k_equal
        url = 'http://www.omdbapi.com/?i={}&apikey=fdc77053'.format(imdbid)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                response = await resp.text()
        values = json.loads(response)
        s = 'Title: ' + values.get('Title') + '\nYear: ' + values.get('Year') + '\nRuntime:' + values.get(
            'Runtime') + '\nDirector: ' + values.get('Director') + '\nActors: ' + values.get(
            'Actors') + '\nCountry: ' + values.get('Country') + '\nRating: IMDb:' + values.get(
            'imdbRating') + '\nPlot: ' + values.get('Plot') + '\n\n' + values.get('Poster')
        url = 'https://vk.com/video?len=2&q={}'.format(urllib.parse.quote(question))
        s += '\nСмотреть:' + url
        # try:
        #     url1 = 'https://duckduckgo.com/html?q={}'.format(urllib.parse.quote(question + ' kinogo.by'))
        #     async with aiohttp.ClientSession() as session:
        #         async with session.get(url1, headers=headers) as resp:
        #             text = await resp.text()
        #     g = re.findall(r'(?<=class="result__a" href=").+(?="><b>)', text)
        #     url = g[0]
        #     if url == 'https://kinogo.by/':
        #         url = g[1]
        #     if url.startswith('https://kin'):
        #         s += '\n' + url
        # except Exception:
        #     pass
        await bot.send_message(message.chat.id, s, parse_mode='HTML')
    else:
        raise NameError


# @dp.message_handler()
# async def echo(message: types.Message):
#     await message.reply(message.text)


if __name__ == '__main__':
    executor.start_polling(dp)
