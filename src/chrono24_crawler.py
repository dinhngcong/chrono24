# -*- coding: utf-8 -*-

import json
from random import randrange
import requests
from lxml import html
from loguru import logger
from prettytable import PrettyTable

from libs.user_agent import USER_AGENT
from libs.proxy import PROXY

from database import Database
import pattern


class Chrono24Crawler(Database):

    def __init__(self):
        self.get_db_connection()

    def get_user_agent(self):
        return USER_AGENT[randrange(len(USER_AGENT)-1)]

    def get_proxy(self, proxy=False):
        if not proxy:
            proxy = PROXY[randrange(len(PROXY) - 1)]
        proxy_data = proxy.split(":")
        return f"http://{proxy_data[2]}:{proxy_data[3]}@{proxy_data[0]}:{proxy_data[1]}"

    def get_ip(self, header, proxy=False):
        if not proxy:
            return '127.0.0.1'
        try:
            response = requests.get("https://api.myip.com/", headers=header, proxies=proxy)
            return response.content
        except requests.exceptions.RequestException as err:
            logger.error(f'Can not get IP infomation from proxy: {err}')
            return False

    def send_request(self, path_url, headers={}, proxy=False):
        url = f'{pattern.BASE_URL}{path_url}'
        header = {
            # 'User-Agent': USER_AGENT[randrange(len(USER_AGENT) - 1)]
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }
        header.update(headers)
        proxy = self.get_proxy(proxy)
        proxy = {
            'http': proxy,
            'https': proxy,
        }
        ip = self.get_ip(headers, proxy)
        if not ip:
            ip = 'No info'
        logger.info(f'Send Request:\n- URL: {url}\n- Header: {header}\n- Proxy: {proxy}\n- IP info: {ip}')
        try:
            response = requests.get(url, headers=header, proxies=proxy)
            if response.status_code == 200:
                print(response.content)
                tree = html.fromstring(response.content)
                logger.info('Send request successfully')
                return tree
            else:
                logger.error(f'Failed to retrieve content. Status code: {response.status_code}')
                return False
        except Exception as e:
            logger.error(f'Failed to send request: {e}')

    def is_more_data(self, handler_page, active_page, els):
        return handler_page == active_page and els

    def crawl_brands(self, headers={}, proxies=False):
        logger.info('\nStarting crawl brand data on Chrono24')
        tree = self.send_request(pattern.URL_PATH_BRANDS, headers, proxies)
        if not tree:
            logger.error('Failed to get data brands')
            return
        brand_els = tree.xpath('//div[@class="flickity-slider"]//a')
        if len(brand_els):
            t = PrettyTable(['Brand', 'Slug', 'Img'])
            for brand_el in brand_els:
                brand_info = brand_el.xpath(".")[0]
                brand_slug = brand_info.get('href')
                brand_img = brand_el.xpath('.//div[@class="rcard-img-background"]')[0].get('data-original')
                brand_name = brand_el.xpath('.//h3[@class="h5 rcard-title"]')[0].text_content().strip()
                t.add_row([brand_name, brand_slug, brand_img])
                sql = """
                    INSERT INTO w_brand (name, slug, source, img)
                    VALUES (%s, %s, %s, %s)
                """
                self.cur.execute(sql, (brand_name, brand_slug, 'chrono24', brand_img))
                logger.info(f'Get brand on Chrono24: {brand_name} | {brand_slug} | {brand_img}')
        else:
            brand_els = tree.xpath('//ul[@class="row m-b-2 list-unstyled"]//a[@data-interaction-event-name="interact_navigation"]')
            t = PrettyTable(['Brand', 'Slug'])
            for brand_el in brand_els:
                brand_info = brand_el.xpath(".")[0]
                brand_slug = brand_info.get('href')
                brand_name = brand_el.xpath('.')[0].text_content().strip()
                t.add_row([brand_name, brand_slug])
                sql = """
                    INSERT INTO w_brand (name, slug, source)
                    VALUES (%s, %s, %s)
                """
                self.cur.execute(sql, (brand_name, brand_slug, 'chrono24'))
                logger.info(f'Get brand on Chrono24: {brand_name} | {brand_slug}')
        t.align = "l"
        print(t)
        self.end_db_connection()
        logger.info(f'Get brand on Chrono24 successfuly. Total {len(brand_els)} brands.')

    def get_all_products_link(self, run_mode='by_brand', headers={}, proxies=False):
        logger.info('\nStarting get all products link on Chrono24')
        sql = """SELECT * FROM w_brand;"""
        self.cur.execute(sql)
        brands = self.cur.fetchall()
        total_products = 0
        for brand in brands:
            total_product = self.handle_product_list_by_brand(brand)
            total_products += total_product
        logger.info(f'Get all products link on Chrono24 successfuly. Total {total_products} brands.')

    def handle_product_list_by_brand(self, brand, headers={}, proxies=False):
        param_url = brand[2].split('.')

        is_more = True
        handle_page = 1
        try_count = 0
        total_crawl = 0
        while is_more:
            handle_url = f'{param_url[0]}-{handle_page}.{param_url[1]}'
            try:
                tree = self.send_request(handle_url, headers, proxies)
                if not tree:
                    logger.error('Failed to get data products link by brand')
                    return 0
            except requests.exceptions.RequestException as err:
                logger.error(err.response.json())
                if try_count > 3:
                    logger.info('Not have more data need crawl.')
                    logger.info(err.response.json())
                    is_more = False
                    return 0
                else:
                    try_count += 1
                    logger.warning('Try crawl more data!')

            product_els = tree.xpath(pattern.XPATH_PRODUCT_IN_LIST_BY_BRAND)
            for product_el in product_els:
                a_el = product_el.xpath(".//a")[0]
                slug = a_el.get('href')
                check_exists = """SELECT id FROM w_product WHERE slug = '%s' LIMIT 1;""" % slug
                self.cur.execute(check_exists)
                product_exists = self.cur.fetchone()
                if product_exists:
                    continue
                sql = """
                    INSERT INTO w_product (slug, manufacturer_id, manufacturer)
                    VALUES (%s, %s, %s)
                """
                self.cur.execute(sql, (a_el.get('href'), brand[0], brand[1]))
                total_crawl += 1

            active_pages = tree.xpath(pattern.XPATH_ACTIVE_PAGE)
            active_page = int(active_pages[0].text_content().strip())
            if self.is_more_data(handle_page, active_page, tree):
                handle_page += 1
                try_count = 0
                logger.info('Have more data need crawl')
            else:
                if try_count > 3:
                    logger.info('Not have more data need crawl.')
                    is_more = False
                else:
                    try_count += 1
                    logger.warning('Try crawl more data!')

            self.conn.commit()
            logger.info(f'Get product link by brand {brand[1]} data successfully. Total: {total_crawl}')
        return total_crawl


    def get_details_products_list(self, headers={}, proxies=False):
        logger.info('\nStarting get detail products list on Chrono24')
        sql = """SELECT id, slug FROM w_product WHERE name IS NULL LIMIT 1;"""
        self.cur.execute(sql)
        links = self.cur.fetchall()
        total_products = 0
        for link in links:
            self.get_details_product_by_link(link)
            total_products += 1
        logger.info(f'Get get detail products list on Chrono24 successfuly. Total {total_products} brands.')

    def get_details_product_by_link(self, link_data, headers={}, proxies=False):
        try:
            tree = self.send_request(link_data[1], headers, proxies)
            if not tree:
                logger.error('Failed to get detail product by link')
                return
        except requests.exceptions.RequestException as err:
            logger.error(err.response.json())
            return err.response.json()


"""Khởi tạo"""
chrono_worker = Chrono24Crawler()
"""Lấy thông tin Brand về hệ thống"""
# chrono_worker.crawl_brands()
"""Lấy thông tin sản phẩm cần crawl về hệ thống"""
chrono_worker.get_all_products_link()
"""Crawl chi tiết thông tin sản phẩm"""
# chrono_worker.get_details_products_list()
