import json
import os

from sqlitedict import SqliteDict


def main():
    folder_in = "/home/sascha/Downloads/matches_db_20201221.sqlite"
    sqldict_in = SqliteDict(folder_in, autocommit=True)

    folder_out = "/home/sascha/Downloads/matches_db_xxx.sqlite"
    sqldict_out = SqliteDict(folder_out, autocommit=True)

    timestamp_last_patch = 1608246488

    for m in sqldict_in.values():
        if m["start_time"] >= timestamp_last_patch:
            sqldict_out[m["match_seq_num"]] = m

    sqldict_in.close()
    sqldict_out.close()


if __name__ == '__main__':
    main()
