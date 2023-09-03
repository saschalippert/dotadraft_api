import json
import os
from os import listdir
from os.path import isfile, join

import requests


class MatchRequestError(Exception):
    def __init__(self, status):
        self.status = status


def get_matches(key, match_seq_num, user):
    proxy = f"socks5://{user}:{user}@127.0.0.1:9050"
    url = f"https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v0001/?key={key}&start_at_match_seq_num={match_seq_num}"
    timeout = 15

    res = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=timeout)

    if res.ok:
        json_data = res.json()
        return {m["match_seq_num"]: m for m in json_data["result"]["matches"]}
    else:
        raise MatchRequestError(res.status_code)


def get_max_seq_id(min_seq):
    matches = [int(f.split(".")[0]) for f in listdir("matches") if isfile(join("matches", f))]
    matches.append(min_seq)
    return max(matches)


def filter_match(match, filters):
    for filter in filters:
        if not filter(match):
            return False

    return True


def filter_matches(matches):
    filters = []
    filters.append(lambda match: match["game_mode"] == 18)
    filters.append(lambda match: match["lobby_type"] == 0)
    filters.append(lambda match: match["human_players"] == 10)

    filtered_matches = {}

    for key, match in matches.items():
        if filter_match(match, filters):
            filtered_matches[key] = match

    return filtered_matches


def save_match(match):
    match_seq_num = match["match_seq_num"]

    filename = f"matches/{match_seq_num}.json"

    if os.path.isfile(filename):
        print(f"file {filename} exists")

    with open(filename, 'w') as outfile:
        json.dump(match, outfile, indent=4, sort_keys=True)
