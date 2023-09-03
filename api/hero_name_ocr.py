import logging

import cv2
import numpy as np
import pytesseract

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class HeroNameOCR:
    def __init__(self, data_heroes):
        self.hero_names = {h["localized_name"].upper(): h["name"] for h in data_heroes.values()}
        self.tessdata = "tessdata"
        self.characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ- "
        self.config = f'--psm 7 --oem 0 --tessdata-dir {self.tessdata} --user-words eng.user-words -c tessedit_char_whitelist="{self.characters}"'

    def __levenshtein(self, seq1, seq2):
        size_x = len(seq1) + 1
        size_y = len(seq2) + 1
        matrix = np.zeros((size_x, size_y))
        for x in range(size_x):
            matrix[x, 0] = x
        for y in range(size_y):
            matrix[0, y] = y

        for x in range(1, size_x):
            for y in range(1, size_y):
                if seq1[x - 1] == seq2[y - 1]:
                    matrix[x, y] = min(
                        matrix[x - 1, y] + 1,
                        matrix[x - 1, y - 1],
                        matrix[x, y - 1] + 1
                    )
                else:
                    matrix[x, y] = min(
                        matrix[x - 1, y] + 1,
                        matrix[x - 1, y - 1] + 1,
                        matrix[x, y - 1] + 1
                    )
        return matrix[size_x - 1, size_y - 1]

    def __apply_threshold(self, img, argument):
        switcher = {
            0: img,
            1: 255 - img,
            2: cv2.threshold(cv2.GaussianBlur(img, (9, 9), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            3: cv2.threshold(cv2.GaussianBlur(img, (7, 7), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            4: cv2.threshold(cv2.GaussianBlur(img, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            5: cv2.threshold(cv2.medianBlur(img, 5), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            6: cv2.threshold(cv2.medianBlur(img, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            7: cv2.adaptiveThreshold(cv2.GaussianBlur(img, (5, 5), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 2),
            8: cv2.adaptiveThreshold(cv2.medianBlur(img, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                     31, 2),
            9: cv2.threshold(cv2.GaussianBlur(img, (5, 5), 0), 75, 255, cv2.THRESH_BINARY)[1],
            10: cv2.threshold(cv2.GaussianBlur(img, (5, 5), 0), 120, 255, cv2.THRESH_BINARY)[1],
        }
        return switcher.get(argument, "Invalid method")

    def __sanitize_hero_name(self, h):
        h = h.upper()
        h = h.replace("'", "")

        return h

    def __filter_hsv(self, img, hMin, hMax, sMin, sMax, vMin, vMax):
        lower = np.array([hMin, sMin, vMin])
        upper = np.array([hMax, sMax, vMax])

        mask = cv2.inRange(img, lower, upper)
        return mask

    def __preprocess(self, img, team):
        if team == 0:
            return self.__filter_hsv(img, 30, 80, 60, 220, 140, 255)
        if team == 1:
            return self.__filter_hsv(img, 0, 10, 128, 255, 102, 255)
        if team == 2:
            return self.__filter_hsv(img, 0, 170, 0, 30, 190, 255)

        raise Exception(f"bad team number {team}")

    def __parse_internal(self, img_org, team):
        img_pre = self.__preprocess(img_org, team)

        #best = []

        for i in range(11):
            img = self.__apply_threshold(img_pre, i)

            res = pytesseract.image_to_string(img, lang='eng', config=self.config)
            res = res.strip().upper()

            #distances = {h: self.__levenshtein(self.__sanitize_hero_name(h), res) for h in self.hero_names.keys()}
            #results = {k: v for k, v in sorted(distances.items(), reverse=False, key=lambda item: item[1])}

            #heroname1, distance1 = list(results.items())[0]
            #heroname2, distance2 = list(results.items())[1]

            if res in self.hero_names:
                logger.info(f"found heroname in {i}")
                return self.hero_names[res]

            #best.append([res, heroname1, heroname2])

        #logger.info(best)

        return None

    def parse_hero_name(self, img_org, team):
        hero_name = self.__parse_internal(img_org, team)

        if hero_name:
            return hero_name

        return self.__parse_internal(img_org, 2)
