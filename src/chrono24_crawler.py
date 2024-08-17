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

    def send_request(self, path_url, headers={}, proxy=False, get_mode='content'):
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
                # print(response.content)
                if get_mode == 'content':
                    tree = html.fromstring(response.content)
                else:
                    tree = response.text
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
        self.end_db_connection()
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
                partner_product_id = slug.split('--id')[1][:-4]

                check_exists = """SELECT id FROM w_product WHERE slug = '%s' LIMIT 1;""" % slug
                self.cur.execute(check_exists)
                product_exists = self.cur.fetchone()
                if product_exists:
                    continue

                sql = """
                    INSERT INTO w_product (partner_product_id, slug, manufacturer_id, manufacturer)
                    VALUES (%s, %s, %s, %s)
                """
                self.cur.execute(sql, (partner_product_id, slug, brand[0], brand[1]))
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
        sql = """SELECT id, partner_product_id, slug FROM w_product WHERE name IS NULL;"""
        self.cur.execute(sql)
        links = self.cur.fetchall()
        total_products = 0
        for link in links:
            self.get_details_product_by_link(link)
            total_products += 1
        self.end_db_connection()
        logger.info(f'Get get detail products list on Chrono24 successfuly. Total {total_products} brands.')

    def get_details_product_by_link(self, link_data, headers={}, proxies=False):
        try:
            tree = self.send_request(link_data[2], headers, proxies)
            if not tree:
                logger.error('Failed to get detail product by link')
                return

            # ================================================================================================ Meta data
            seq_fields = ['name', 'description', 'price']
            if not tree.xpath(pattern.XPATH_PRODUCT_DETAIL_NAME):
                sql = f"UPDATE w_product SET name = 'skip', error_log = 'Product link not available' WHERE id = {int(link_data[0])};"
                self.cur.execute(sql)
                self.conn.commit()
                return
            product_data = {
                'name': tree.xpath(pattern.XPATH_PRODUCT_DETAIL_NAME)[0].text_content().strip().split("\n")[0] or None,
                'description': tree.xpath(pattern.XPATH_PRODUCT_DETAIL_MORE)[0].text_content().strip() or None,
                'price': tree.xpath(pattern.XPATH_PRODUCT_DETAIL_PRICE)[0].text_content().strip() or None,
            }
            contents = tree.xpath(pattern.XPATH_PRODUCT_DETAIL_META_DATA)
            meta_datas = contents[0]
            basic_data_pattern = pattern.XPATH_PRODUCT_DETAIL_BASIC_DATA_PATTERN

            for k, v in pattern.LIST_BASIC_DATA.items():
                seq_fields.append(k)
                basic_data = meta_datas.xpath(basic_data_pattern % v)
                if len(basic_data) > 1:
                    product_data[k] = basic_data[1].text_content().strip() or None
                else:
                    product_data[k] = None
            # ========================================================================================= End of Meta data

            # ============================================================================================== Detail Data
            if not link_data[1]:
                partner_product_id = link_data[2].split('--id')[1][:-4]
            else:
                partner_product_id = link_data[1]
            detail_data = False
            detail_tree = self.send_request('/search/detail.htm?id=%s&originalNotes' % partner_product_id, headers, proxies)
            if detail_tree:
                detail_data = detail_tree.xpath('//notes')[0].text_content().strip()
            if not detail_data or detail_data == '':
                detail_data = self.send_request('/search/detail.htm?id=%s&originalNotes' % partner_product_id, headers, proxies, get_mode='text')
            # ======================================================================================= End of Detail Data

            # =================================================================================================== Update
            fields_name = ''
            fields_value = [partner_product_id, detail_data]
            for field in seq_fields:
                fields_name += f', {field} = %s'
                fields_value.append(product_data[field])
            fields_value.append(link_data[0]) # ID của product để update
            sql = f'UPDATE w_product SET partner_product_id = %s, detail = %s, {fields_name[2:]} WHERE id = %s;'
            self.cur.execute(sql, fields_value)
            self.conn.commit()
            # ============================================================================================ End of Update
        except requests.exceptions.RequestException as err:
            logger.error(err.response.json())
            sql = """UPDATE w_product SET error_log = %s WHERE id = %s;"""
            self.cur.execute(sql, (err.response.json(), int(link_data[0])))
            self.conn.commit()
            return err.response.json()

    def _get_detail_product(self, product_id):
        try:
            detail_data = self.send_request('/search/detail.htm?id=%s&originalNotes' % product_id, get_mode='text')
            print(detail_data)
        except requests.exceptions.RequestException as err:
            logger.error(err.response.json())
            return err.response.json()

    # Hàm lấy các meta fields
    def _get_metadata(self, headers={}, proxies=False):
        metadata = {}
        sql = """SELECT id, slug FROM w_product;"""
        self.cur.execute(sql)
        links = self.cur.fetchall()
        total_products = 0
        for link in links:
            tree = self.send_request(link[1], headers, proxies)
            if not tree:
                logger.error('Failed to get detail product by link')
                return

            contents = tree.xpath(pattern.XPATH_PRODUCT_DETAIL_META_DATA)
            meta_datas = contents[0]
            for label_origin in meta_datas.xpath(".//tr//strong"):
                label_value = label_origin.text_content().strip()
                label_key = label_value.lower().replace(' ', '_').replace('_', '_').replace('/', '_').replace(
                    '|', '_').replace('~', '_').replace('\\', '_')
                metadata[label_key] = label_value
        print(metadata)
        logger.info(f'Get get detail products list on Chrono24 successfuly. Total {total_products} brands.')

"""Khởi tạo"""
chrono_worker = Chrono24Crawler()
"""Lấy thông tin Brand về hệ thống"""
# chrono_worker.crawl_brands()
"""Lấy thông tin sản phẩm cần crawl về hệ thống"""
# chrono_worker.get_all_products_link()
"""Crawl chi tiết thông tin sản phẩm"""
# chrono_worker._get_metadata()
# chrono_worker._get_detail_product(34006556)
chrono_worker.get_details_products_list()

# /rolex/rolex-in-stock-2022-daytona-white-panda-dial-116500ln-oyster-bracelet--id35370091.htm
# /rolex/datejust-36-126234-mint-green-dial--id34017343.htm
# /rolex/rolex-in-stock-2022-daytona-black-dial-116500ln-oyster-bracelet--id35339960.htm
# /rolex/rolex-rolex-yacht-master-16622-platinum-bezel-and-dial-oyster-bracelet-40mm-2000--id34846355.htm
# chrono_worker.get_details_product_by_link([
#     0,
#     None,
#     '/rolex/rolex-in-stock-2022-daytona-white-panda-dial-116500ln-oyster-bracelet--id35370091.htm'
# ])
