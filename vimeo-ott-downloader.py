import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlretrieve

import time
import os
import json

import config

ps = requests.Session()
ps.headers.update({
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-DE,en;q=0.9,de-DE;q=0.8,de;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
})

ps.cookies.update(config.platform_cookies)
ps.headers.update(config.platform_headers)

out_dir = config.out
series_urls = config.urls

def download_from_url(url, filename):
    print(f" > Downloading {url}: Starting to {filename}...")
    urlretrieve(url, filename)
    print(f" > Downloading {url}: Done")

def to_filename(s):
    return "".join(x for x in s if (x.isalnum() or x in "._- "))

def get_videos_of_series(url):
    r = ps.get(url)
    s = BeautifulSoup(r.content, features="lxml")

    season_select = s.select_one("body > section > section.episode-container.video-container.padding-bottom-large.padding-horizontal-medium > div.row.relative.season-controls.padding-bottom-medium.padding-top-large > div.small-16.medium-11.large-13.columns.text-left.small-only-text-center > div > form:nth-child(1) > select")
    season_urls = [(x["value"], x.text.strip()) for x in season_select.select("option")]

    season_results = {}
    for u, n in season_urls:
        r = ps.get(u)
        s = BeautifulSoup(r.content, features="lxml")

        season_results[n] = [x["href"] for x in s.select("body > section > section.episode-container.video-container.padding-bottom-large.padding-horizontal-medium > div:nth-child(2) > div > div > ul > li > div > div > a")]

    return season_results

def get_file_from_video(v_url, quality='1080p'):
    r = ps.get(v_url)
    s = BeautifulSoup(r.content, features="lxml")
    v_embed_url = urlparse(s.select_one("#watch-embed")["src"])
    jwt_token = [x.split("=")[1] for x in v_embed_url.query.split("&") if "user-token" in x]

    params = {
        'api': '1',
        'auth-user-token': jwt_token,
        'autoplay': '1',
        'locale': 'en',
        'playsinline': '1',
        'sharing': '1',
        'title': '0',
        'vimeo': '1',
    }

    r = ps.get(f'https://embed.vhx.tv{v_embed_url.path}', params=params)
    ott_data = r.text[r.text.index("window.OTTData")+len("window.OTTData = "):]
    ott_data = json.loads(ott_data[:ott_data.index("</script>")])

    video_title = ott_data["video"]["title"]

    r = ps.get(ott_data["config_url"])
    config_data = r.json()
    thumbnail_url = config_data["video"]["thumbs"]["base"]
    cdn_url = [x["url"] for x in config_data["request"]["files"]["progressive"] if x["quality"] == quality][0]

    return cdn_url, video_title, thumbnail_url

pool = ThreadPoolExecutor(max_workers=5)
futures = []

for s in series_urls:
    sfn = out_dir + to_filename(s.split("/")[-1]) + "\\"
    os.makedirs(sfn, exist_ok=True)

    videos_by_season = get_videos_of_series(s)
    print(s, "Seasons:", videos_by_season)
    print(s, "Seasons:", len(videos_by_season))

    for season in videos_by_season:
        ssfn = sfn + to_filename(season) + "\\"
        os.makedirs(ssfn, exist_ok=True)

        videos = videos_by_season[season]
        itr = 0
        for v in videos:
            itr += 1

            try:
                cdn_url, video_title, thumbnail_url = get_file_from_video(v)
            except Exception as ex:
                print("ERROR on", v, "SKIPPING")
                continue

            print(video_title, cdn_url)
            filename = ssfn + str(itr) + "__" + to_filename(video_title) + "_" + cdn_url.split("/")[-1]
            
            if os.path.exists(filename):
                continue
            
            futures.append(pool.submit(lambda x: download_from_url(*x), (cdn_url, filename)))
            
            # thumbname = ssfn + to_filename(video_title) + thumbnail_url.split("/")[-1] + ".jpg"
            # futures.append(pool.submit(lambda x: download_from_url(*x), (thumbnail_url, thumbname)))
            print(futures)

while True:
    all_done = True
    for f in futures:
        if not f.done():
            all_done = False

    if all_done:
        break
    else:
        print("Still downloading...")
        print([x for x in futures])
        time.sleep(10)
