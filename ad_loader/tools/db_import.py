import json
import os

from sqlitedict import SqliteDict


def main():
    sqldict = SqliteDict('matches_db.sqlite', autocommit=True)

    folder = "/home/sascha/PycharmProjects/adguide/matches"

    filelist = os.listdir(folder)
    for file in filelist[:]:
        if not (file.endswith(".json")):
            filelist.remove(file)

    for file in filelist:
        file_path = f"{folder}/{file}"

        with open(file_path) as json_file:
            match = json.load(json_file)
            seq_num = match["match_seq_num"]
            sqldict[seq_num] = match
            print(f"saved {seq_num}")

    sqldict.close()


if __name__ == '__main__':
    main()
