import requests


def main():
    for i in range(10):
        proxy = f"socks5://user{i}:password{i}@127.0.0.1:9050"
        url = f"https://api.myip.com/"
        res = requests.get(url, proxies={"http": proxy, "https": proxy})
        print(res.json())


if __name__ == '__main__':
    main()
