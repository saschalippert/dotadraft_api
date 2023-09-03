from datetime import datetime

from sqlitedict import SqliteDict


def main():
    sqldict = SqliteDict('matches_db.sqlite', autocommit=True)

    max_ts = 0
    dates = {}
    max_match_seq_id = 0

    for key, value in sqldict.iteritems():
        date = datetime.fromtimestamp(value["start_time"]).date()

        if date == datetime(2020, 10, 28).date():
            max_match_seq_id = max(max_match_seq_id, value["match_seq_num"])

        date_sum = dates.get(date, 0)
        date_sum = date_sum + 1
        dates[date] = date_sum

        max_ts = max(max_ts, value["start_time"])

    dates = {k: v for k, v in sorted(dates.items(), key=lambda item: item[0])}

    print(datetime.fromtimestamp(max_ts))

    sqldict.close()


if __name__ == '__main__':
    main()
