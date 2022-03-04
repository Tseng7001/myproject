import requests
from bs4 import BeautifulSoup
import pymysql

import time
url = 'https://www.txt123.cc'

conn = pymysql.connect(host='127.0.0.1', user='root', password='123456789', db='myproject', port=3306)
cursor = conn.cursor()

def get_html(nowUrl): # 處理網頁原始碼
    header = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15"}
    resp = requests.get(nowUrl, headers=header)

    resp = resp.content.decode('gb18030')  # 將亂碼轉成文字

    soup = BeautifulSoup(resp, 'html.parser')

    return soup

def get_menuList(): # 獲取導覽列網址清單
    global url

    header = {'User-Agent':"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15"}
    resp = requests.get(url, headers=header)

    resp = resp.content.decode('gb18030') # 將亂碼轉成文字

    soup = BeautifulSoup(resp, 'html.parser')

    catelogue = soup.find('ul', {'class':'nav navbar-nav'})

    catelogue_list = []

    for item in catelogue:
        item_url = item.find('a')
        if item_url != -1:
            catelogueUrl = url + item_url.get('href')
            catelogue_list.append(catelogueUrl)

    catelogue_list = catelogue_list[:-1] # 導覽列網址, 排行榜另外抓

    return catelogue_list


def get_comicUrl(): #獲取各分類所有的小說標題及鏈結
    menu_list = get_menuList()
    count = 1 # 用來做換頁url 標記, 網址格式 https://www.txt123.cc/fenlei/{}_{}/.format(導覽列第幾個, 第幾頁)
    for menu in menu_list:  # 依序從導覽列進入

        header = {'User-Agent':"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15"}
        resp = requests.get(menu, headers=header)

        resp = resp.content.decode('gb18030') # 將亂碼轉成文字

        soup = BeautifulSoup(resp, 'html.parser')

        pageName = soup.find('li', {'class':'active'}).text

        total_page = int(soup.find('li', {'class':'disabled'}).text.split('/')[1]) #抓出每個類別的總頁數

        current_page = 1
        for current_page in range(1,total_page+1): # 進入每個分頁
            html = get_html('https://www.txt123.cc/fenlei/{}_{}/'.format(count, current_page))

            table = html.find('table',{'class':'table'})

            alltr = table.find_all('tr')
            for tr in alltr:
                if tr.find('a') != None:
                    comic_page = tr.find('a').get('href') # 漫畫鏈結
                    get_comicAllchap(comic_page)


        count += 1 # 換到下一個分類
    cursor.close()

def get_comicAllchap(comic_page): # 獲取單篇小說所有的章節名稱及鏈結
    html = get_html(comic_page)
    bookTitle = html.find('h1', {'class':'bookTitle'}).text  # 小說名稱, 用來索引資料庫
    allchap = html.find_all('dd', {'class':'col-md-3'}) # 所有章節
    chapter_id = 1 # 每次第一章節都從chapter_id = 1 開始, 等於第幾章節的意思
    for chap in allchap:
        chapter_url = url + chap.find('a').get('href') # 章節鏈結

        html = get_html(chapter_url)
        name = html.find('h1', {'class': 'readTitle'}).text # 章節名稱
        content = html.find('div', id='htmlContent').text
        create_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 此檔案上傳時間
        updated_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 此檔案上傳時間

        sql = "select * from `book` where `title` = '{}'".format(bookTitle) # 找出與book Table 相符的小說名稱
        cursor.execute(sql)
        result = cursor.fetchone()
        result = list(result) # 將tuple 轉成 list
        book_id = result[0] # book_id = 書本id

        sql = "select * from `chapter` where `name` = '{}'".format(name) # 確認資料庫內是否有已經存在的章節
        cursor.execute(sql)
        conn.commit()
        if cursor.rowcount == 0:
            sql = "insert into `chapter` (`id`, `book_id`, `name`, `chapter_url`, `content`, `create_at`, `updated_at`) values ('{}','{}','{}','{}','{}','{}','{}')".format(chapter_id, book_id, name, chapter_url,content, create_at, updated_at)
            cursor.execute(sql)
            conn.commit()
        chapter_id += 1
        print(name)
        print('-'*50)
        print(content)


def get_htmlContent(chap_url): # 抓取個章節的內容（這邊1個章節＝1頁）
    html = get_html(chap_url)
    name = html.find('h1', {'class':'readTitle'}).text
    content = html.find('div', id='htmlContent').text
    create_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 此檔案上傳時間
    updated_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 此檔案上傳時間
    content = content.replace('收藏【小说123网www.txt123.cc】，元尊小说无弹窗免费阅读', '')
    print(name)
    print(chap_url)
    print(content)
    print('-'*50)

get_comicUrl()