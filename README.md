# Vimeo-OTT-Downloader-
📼 Download videos and series from Vimeo OTTs such as Dropout.tv

## Config
Create a `config.py` from requests.
```python
platform_cookies = {
    'tracker': 'xxx',
    'locale_det': 'en',
    '__stripe_mid': 'xxx',
    '_session': 'xxx',
    '__cf_bm': 'xxx',
    '__stripe_sid': 'xxx',
    'referrer_url': 'xxx',
}

platform_headers = {
    'authority': 'xxx',
    'referer': 'xxx',
}

out = "X:\\Downloads\\"
urls = ["https://xyz.xyz/xyz", "https://xyz.xyz/abc"]
```
