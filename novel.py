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
                    book_url = tr.find('a').get('href') # 漫畫鏈結
                    content_list = tr.text.split() # type = list, 把文字部分變成list處理
                    # list長度不一定一樣, 依據長度分別處理，主要差別在最新章節及章節名稱的部分
                    # 有的第幾章及名稱會合再一起，所以在這邊做判斷
                    html = get_html(book_url)
                    # 有的小說沒有封面圖面, 另外做判斷
                    cover_url = html.find('img', {'class': 'img-thumbnail'}).get('src') if html.find('img', {'class': 'img-thumbnail'}) != None else '尚無封面'

                    if len(content_list) == 6:
                        title = content_list[0] # 小說標題 type=str
                        new_novel = content_list[1] + content_list[2] # 最新篇章
                        update_at = content_list[4] # 更新時間 (網站上作者漫畫的更新時間)
                        create_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) # 此檔案上傳時間
                        author = content_list[3] # 作者
                        publish_status = content_list[5] # 連載狀態

                        sql = "select * from `book` where `title` = '{}'".format(title)
                        cursor.execute(sql)
                        conn.commit()
                        if cursor.rowcount == 0:
                            sql = "insert into `book` (`site_id`, `title`, `author`, `book_url`, `publish_status`, `cover_url`, `created_at`, `updated_at`) " \
                                  "values (1, '{}','{}','{}','{}','{}','{}','{}')".format(title, author, book_url, publish_status, cover_url, create_at, update_at)
                            cursor.execute(sql)
                            conn.commit()
                        print(title, author, book_url, publish_status, cover_url, create_at, update_at)
                    else:
                        title = content_list[0] # 小說標題 type=str
                        new_novel = content_list[1] # 最新篇章
                        update_at = content_list[3] # 更新時間 (網站上作者漫畫的更新時間)
                        create_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) # 此檔案上傳時間
                        author = content_list[2] # 作者
                        publish_status = content_list[4] # 連載狀態

                        sql = "select * from `book` where `title` = '{}'".format(title)
                        cursor.execute(sql)
                        conn.commit()
                        if cursor.rowcount == 0:
                            sql = "insert into `book` (`site_id`, `title`, `author`, `book_url`, `publish_status`, `cover_url`, `created_at`, `updated_at`) " \
                                  "values (1, '{}','{}','{}','{}','{}','{}','{}')".format(title, author, book_url, publish_status, cover_url, create_at, update_at)
                            cursor.execute(sql)
                            conn.commit()
                        print(title, author, book_url, publish_status, cover_url, create_at, update_at)
                else:
                    pass
            print('{}第{}頁結束'.format(pageName, current_page))

        count += 1 # 換到下一個分類
    cursor.close()

def get_comicAllchap(comic_page): # 獲取單篇小說所有的章節名稱及鏈結
    html = get_html(comic_page)
    allchap = html.find_all('dd', {'class':'col-md-3'}) # 所有章節
    img_url = html.find('img', {'class':'img-thumbnail'}).get('src') # 封面圖面
    
    for chap in allchap:
        title = chap.text
        chap_url = url + chap.find('a').get('href')
        content = get_htmlContent(chap_url) # 小說內文
        # sql = 'select * from `novel` where `new_novel` = %s'.format(new_novel)
        # cursor.execute(sql)
        # conn.commit()
        # if cursor.rowcount == 0:
        sql = "insert into `chapter` (`title`, `chap_url`, `img_url`, `content`) values ('{}','{}', '{}', '{}')".format(title, chap_url, img_url, content)
        cursor.execute(sql)
        conn.commit()

        print(title)
        print('-'*50)
        print(content)
    cursor.close()

def get_htmlContent(chap_url): # 抓取個章節的內容（這邊1個章節＝1頁）
    html = get_html(chap_url)
    content = html.find('div', id='htmlContent').text
    
    content = content.replace(' 收藏【小说123网www.txt123.cc】，元尊小说无弹窗免费阅读！', '')
    return content



def conn_mysql(): #建立mysql連線並執行sql指令
    try:
        conn = pymysql.connect(host='127.0.0.1', user='root', password='123456789', db='myproject', port=3306)
        cursor = conn.cursor()
        # cursor.execute()
        # conn.commit()
        # cursor.close()
        print("執行成功")
    except:
        print('執行失敗')


get_comicUrl()