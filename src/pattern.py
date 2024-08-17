# -*- coding: utf-8 -*-

BASE_URL = 'https://www.chrono24.com'

# Popular brands path
URL_PATH_BRANDS = '/search/browse.htm'

# Check active page
XPATH_ACTIVE_PAGE = '//nav[@aria-label="Pagination"]//span[@class="active"]'
XPATH_PRODUCT_IN_LIST_BY_BRAND = '//div[@class ="js-article-item-container article-item-container wt-search-result article-image-carousel"]'

XPATH_PRODUCT_DETAIL_NAME = '//h1//span[@class="d-block"]//.'
XPATH_PRODUCT_DETAIL_MORE = '//h1//span[@class="d-block text-md text-sm-lg text-weight-normal"]'
XPATH_PRODUCT_DETAIL_MORE_2 = '//h1//span[@class="d-block"]/span/span'
XPATH_PRODUCT_DETAIL_PRICE = '//div[@class="row"]//span[@class="js-price-shipping-country"]'
XPATH_PRODUCT_DETAIL_CURRENCY = '//div[@class="row"]//span[@class="currency"]'

XPATH_PRODUCT_DETAIL_META_DATA = '//div[@class="js-tab-panel tab-panel"]//table'
XPATH_PRODUCT_DETAIL_BASIC_DATA_PATTERN = '//strong[text()="%s"]/../../td'
XPATH_PRODUCT_DETAIL_BASIC_DATA_LISTING_CODE = '//strong[text()="Listing code"]/../../td'

# 34 items
LIST_BASIC_DATA = {
    'listing_code': 'Listing code',
    # 'brand': 'Brand', # manufacturer
    'model': 'Model',
    'reference_number': 'Reference number',
    'movement': 'Movement',
    'case_material': 'Case material',
    'bracelet_material': 'Bracelet material',
    'year_of_production': 'Year of production',
    'condition': 'Condition',
    'scope_of_delivery': 'Scope of delivery',
    'gender': 'Gender',
    'location': 'Location',
    # 'price': 'Price', # Lấy price đầu trang
    'availability': 'Availability',
    'caliber_movement': 'Caliber/movement',
    'power_reserve': 'Power reserve',
    'number_of_jewels': 'Number of jewels',
    'case_diameter': 'Case diameter',
    'water_resistance': 'Water resistance',
    'bezel_material': 'Bezel material',
    'crystal': 'Crystal',
    'dial': 'Dial',
    'bracelet_color': 'Bracelet color',
    'clasp': 'Clasp',
    'clasp_material': 'Clasp material',
    'base_caliber': 'Base caliber',
    'dial_numerals': 'Dial numerals',
    'most_recent_servicing': 'Most Recent Servicing',
    'dealer_product_code': 'Dealer product code',
    'thickness': 'Thickness',
    'lug_width': 'Lug width',
    'frequency': 'Frequency',
    'bracelet_length': 'Bracelet length',
    'bracelet_thickness': 'Bracelet thickness',
    'buckle_width': 'Buckle width'
}
