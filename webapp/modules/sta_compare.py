import time, re, urllib.parse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def get_data(keyword):
    service = Service(r"C:\MyApps\statio\webapp\driver\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 背景執行
    browser = webdriver.Chrome(service=service, options=options)

    try:
        items_9x9, search_table = crawl_9x9(browser, keyword)
        items_rakuten = crawl_rakuten(browser, search_table)
        all_items = []

        # 格式整理
        for item in items_9x9:
            prices = []
            # 樂天價格
            for r in items_rakuten:
                if r['name'] == item['name'] and r['price'] is not None:
                    prices.append({'site': '樂天市場購物網', 'price': r['price'], 'url': r['url']})
            # 9*9 價格
            prices.append({'site': '九乘九文具專家', 'price': item['price'], 'url': item['url']})

            # 至少有一個價格才加入
            if prices:
                prices.sort(key=lambda x: x['price'])
                item['prices'] = prices
                all_items.append(item)

        return all_items

    finally:
        browser.quit()

# 9*9
def crawl_9x9(browser, keyword):
    url = f"https://www.9x9.tw/mod/search/result.php?keyword={urllib.parse.quote(keyword)}&search_send=1"
    browser.get(url)
    time.sleep(0.2)
    bsoup = BeautifulSoup(browser.page_source, 'html.parser')

    datadict = []
    product = bsoup.find('div', {'class': 'product'})
    if not product:
        return datadict, []

    listarea = product.find('div', {'class': 'listarea'})
    pinfo = listarea.find_all('div', {'class': 'pinfo'})

    for i in range(min(5, len(pinfo))):
        name_tag = pinfo[i].find('div', {'class': 'name'})
        if not name_tag: 
            continue
        name = name_tag.get_text().strip()

        # 抓圖片
        img_tag = pinfo[i].find('div', {'class':'pic'}).find("img")
        img = img_tag["src"] if img_tag else "https://via.placeholder.com/150"

        # 抓價格
        price_tags = pinfo[i].find('div', {'class': 'price'})
        prices = []
        for tag in ['op', 'bp', 'lp', 'tp']:
            t = price_tags.find('div', {'class': tag})
            if t:
                price_text = t.get_text()
                price_digits = re.sub(r'[^\d]', '', price_text)
                if price_digits:
                    prices.append(int(price_digits))
        if not prices:
            continue
        price = min(prices)

        # 抓商品連結
        link_tag = pinfo[i].find('div', {'class': 'pic'})
        url = link_tag.find('a')['href'] if link_tag.find('a') else None

        datadict.append({"name": name, "price": price, "url": url, "img": img})

    search_table = [{'name': d['name']} for d in datadict]
    return datadict, search_table

# rakuten
def crawl_rakuten(browser, search_table):
    datadict = []
    for srow in search_table:
        keyword = srow['name']
        url = f"https://www.rakuten.com.tw/search/{urllib.parse.quote(keyword)}/15619/?s=2"
        browser.get(url)
        time.sleep(0.2)
        bsoup = BeautifulSoup(browser.page_source, 'html.parser')
        commodity = bsoup.find('div', {'class': '_6xzpdb0 _6xzpdbpc _6xzpdbfr _8k5k3g2 _6xzpdbtc _16u6wpd3 _6xzpdb4a _6xzpdb51 _6xzpdb5s _6xzpdb6j _6xzpdb0 _6xzpdbb _6xzpdbpc _6xzpdb8 _6xzpdb1r _6xzpdbj _16u6wpd4'})
        recommend = commodity.find('div', {'class', '_4z4ak1 _6xzpdb8 _6xzpdbc _6xzpdbyv _6xzpdbyx _6xzpdb9j qa-searchResults-storeRecommend-label'})
        if recommend != None:
            continue
        pinfo = bsoup.find('div', {'class': '_16u6wpdb'})
        if not pinfo:
            datadict.append({'site': 'rakuten', 'name': keyword, 'price': None, 'url': None})
        else:
            # 抓價格
            price_tag = pinfo.find('div', {'class': "_1md3074m"})
            price = int(re.sub(r'[^\d]', '', price_tag.get_text())) if price_tag else None
            # 樂抓連結
            a_tag = pinfo.find('a')
            link = a_tag['href'] if a_tag else None
            datadict.append({'site': 'rakuten', 'name': keyword, 'price': price, 'url': link})
    return datadict