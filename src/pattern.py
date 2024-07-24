# -*- coding: utf-8 -*-

BASE_URL = 'https://www.chrono24.com'

# Popular brands path
URL_PATH_BRANDS = '/search/browse.htm'

# Check active page
XPATH_ACTIVE_PAGE = '//nav[@aria-label="Pagination"]//span[@class="active"]'
XPATH_PRODUCT_IN_LIST_BY_BRAND = '//div[@class ="js-article-item-container article-item-container wt-search-result article-image-carousel"]'
XPATH_PRODUCT_DETAIL_META_DATA = '//div[@class="js-tab-panel tab-panel"]//table]'
XPATH_PRODUCT_DETAIL_NAME = '//h1//span[@class="d-block"]'
XPATH_PRODUCT_DETAIL_MORE = '//h1//span[@class="d-block text-md text-sm-lg text-weight-normal"]'
