import requests
import pymongo
import bs4
from bs4 import BeautifulSoup
import time
from urllib import parse
import os
import random

# Save all data to MongoDB

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['feitsui']
singer_coll = db['singers']
song_coll = db['lyric']

headers = {    
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",        
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

agents = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "
]

def download_one_song(song_url):
    try:
        headers["User-Agent"] = random.choice(agents)
        doc = requests.get(song_url, headers=headers)
        if doc.status_code != 200:
            print ("[Faild] {}".format(song_url))
            return
        html = BeautifulSoup(doc.content, "lxml")
        main = html.select_one("body > div.container > div > main")
        title = main.find("h2").text.strip()
        
        article = main.select_one('body > div.container > div > main > article').find_all('p')
        ps = [ child for child in main.children if child.name == 'p']
        info = [p.split(" ") for p in ps[0].text.strip().split("\n")]
        info = {p[0]: p[1:] for p in info}
        if info.get('歌手'):
            info['歌手'] = [" ".join(info['歌手'])]

        if len(ps) == 5:
            desc = ps[1].text.strip()
            label = [p.strip() for p in ps[2].text.strip().split("\n")]
        elif len(ps) == 4:
            desc = ""
            label = [p.strip() for p in ps[1].text.strip().split("\n")]
        elif len(ps) == 3:
            desc = ""
            label = []

        lyric = []
        for i, p in enumerate(article):
            for item in p.children:
                if isinstance(item, bs4.element.NavigableString):
                    item = str(item)
                    if "翡翠粤语歌词" not in item:
                        lyric.append(item)
            if i != len(article) - 1:
                lyric.append("")
        
        lyric = "\n".join(lyric)

        doc = {
            'title': title,
            'url': song_url,
            'info': info,
            'label': label,
            'lyric': lyric,
            'desc': desc
        }

        song_coll.update_one({'url': song_url}, {"$set": doc}, upsert=True)    
    except Exception as e:
        print ("[Faild] URL {}".format(song_url))

def download_one_singer(singer_url, singer):
    print ("Downloading {} ...".format(singer_url))
    song_urls = []
    try:        
        singer_page = requests.get(singer_url, headers=headers)        
        if singer_page.status_code != 200:
            msg = "[{} Faild] URL: {}".format(singer_page.status_code, singer_url)
            with open("log.txt", "w") as f:
                f.write(msg)
            print (msg)        
        else:
            html = BeautifulSoup(singer_page.content, 'lxml')
            songs = html.select_one("body > div.container > div > main").select("li")
            songs_lst = []
            for song in songs:
                href = song.select_one('a')
                song_url = "https://www.feitsui.com{}".format(parse.urlparse(href.attrs['href']).path) if href else ""
                name = song.select_one('a')
                name = name.text if name else ""
                mandarin = song.select_one('small')
                mandarin = mandarin.text if mandarin else ""

                doc = {
                    'url': song_url,
                    'name': name,
                    'mandarin': mandarin
                }

                songs_lst.append(doc)
                song_urls.append(song_url)               

            singer_coll.update_one({"url": singer_url}, {"$set": {"songs": songs_lst}})
            print ("[SUCCESS] {} song(s) from {}".format(len(song_urls), singer_url))

    except Exception as e:
        msg = "[Faild] URL: {}".format(singer_url)
        with open("log.txt", "w") as f:
            f.write(msg)
        print (msg, e)

if __name__ == "__main__":
    
    # 1. 先采集每个歌手的信息
    """
    singer_url = "https://www.feitsui.com/singer_s/"
    req = requests.get(singer_url)
    html = BeautifulSoup(req.content, "lxml")
    singers = html.select_one("body > div.container > div > main").select('li')

    singer_urls = []
    for singer in singers:
        href = singer.select_one('a')
        singer_url = "https://www.feitsui.com{}".format(href.attrs['href']) if href else ""
        name = singer.select_one('a')
        name = name.text if name else ""
        english_name = singer.select_one('small')
        english_name = english_name.text if english_name else ""
        doc = {
            'url': singer_url,
            'name': name,
            'english_name': english_name
        }
        singer_coll.update_one({'url': singer_url}, {"$set": doc}, upsert=True)
        singer_urls.append(singer_url)
    """
    
    # 2. 采集每个歌手的曲目列表
    singer_urls = singer_coll.find()
    singer_urls = [(singer_url['url'], singer_url['name']) for singer_url in singer_urls]
    """
    for singer_url, singer in singer_urls:
        if singer_coll.count_documents({'url': singer_url, 'songs': {'$exists': True}}) == 0:
            #time.sleep(10)
            #print (singer_url, singer)
            download_one_singer(singer_url, singer)
        else:
            pass 
            #print ("{} has songs field!".format(singer_url))
    
    """

    # 3. 采集每首歌的歌词
    song_urls = []
    for singer_url, name in singer_urls:
        songs = singer_coll.find_one({"url": singer_url}).get('songs')
        if songs:
            for song in songs:
                song_urls.append((song['url'], name))
    
    song_urls = list(set(song_urls))

    count = 0
    for song_url, name in song_urls:
        if song_coll.count_documents({'url': song_url}) == 0:
            count += 1
            time.sleep(20) # 20的时候不会被封IP
            print ("Downloading [{}] {} {}".format(count, song_url, name))            
            download_one_song(song_url)
        else:
            pass
            #print (" {} already downloa.".format(song_url))
    #"""