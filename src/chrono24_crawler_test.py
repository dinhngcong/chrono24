# -*- coding: utf-8 -*-

import json
from random import randrange
import requests
from lxml import html
from loguru import logger

from libs.user_agent import USER_AGENT
from libs.proxy import PROXY

from src.database import Database
import pattern


def get_user_agent():
    return USER_AGENT[randrange(len(USER_AGENT)-1)]

def get_proxy(proxy=False):
    if not proxy:
        proxy = PROXY[randrange(len(PROXY) - 1)]
    proxy_data = proxy.split(":")
    return f"http://{proxy_data[2]}:{proxy_data[3]}@{proxy_data[0]}:{proxy_data[1]}"

def get_ip(header, proxy=False):
    if not proxy:
        return '127.0.0.1'
    try:
        response = requests.get("https://api.myip.com/", headers=header, proxies=proxy)
        return response.content
    except requests.exceptions.RequestException as err:
        return err.response.json()

def send_request(path_url, headers={}, proxy=False):
    url = f'{pattern.BASE_URL}{path_url}'
    header = {
        'User-Agent': USER_AGENT[randrange(len(USER_AGENT) - 1)]
    }
    header.update(headers)
    proxy = get_proxy(proxy)
    proxy = {
        'http': proxy,
        'https': proxy,
    }
    ip = get_ip(headers, proxy)
    logger.info(f'Send Request:\n- URL: {url}\n- Header: {header}\n- Proxy: {proxy}\n- IP info: {ip}')
    try:
        response = requests.get(url, headers=header, proxies=proxy)
        if response.status_code == 200:
            tree = html.fromstring(response.content)
            logger.info('Send request successfully')
            return tree
        else:
            logger.error(f'Failed to retrieve content. Status code: {response.status_code}')
            return False
    except Exception as e:
        logger.error(f'Failed to send request: {e}')

def crawl_brands(headers={}, proxies=False):
    tree = send_request(pattern.URL_PATH_BRANDS, headers, proxies)
    if not tree:
        logger.error('Failed to get data brands')
        return

    brand_els = tree.xpath('//div[@class="flickity-slider"]//a')
    print(len(brand_els))
    for brand_el in brand_els:
        print(brand_el)
        brand_info = brand_el.xpath(".")[0]
        brand_slug = brand_info.get('href')
        brand_img = brand_el.xpath('.//div[@class="rcard-img-background"]')[0].get('data-original')
        brand_name = brand_el.xpath('.//h3[@class="h5 rcard-title"]')[0].text_content().strip()
        print(f'New Brand data ===================================================================================='
              f'\n- {brand_name}\n- {brand_slug}\n- {brand_img}\n')


crawl_brands()
