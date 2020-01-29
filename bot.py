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
        " \n\n <i>example:</i> \n  веном\n  /random",
        parse_mode='HTML')



# @dp.message_handler()
# async def echo(message: types.Message):
#     await message.reply(message.text)


if __name__ == '__main__':
    executor.start_polling(dp)
