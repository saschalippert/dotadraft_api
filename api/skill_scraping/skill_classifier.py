import cv2
import numpy as np

from skill_scraping.image_matcher import ImageMatcher


class SkillClassifier:
    def __init__(self, images):
        self.image_locator = ImageMatcher()

        self.spells = {}
        self.point_history = []

        for filename, image in images.items():
            preprocessed = self.image_locator.preprocess(image)
            kp, desc = self.image_locator.kp_desc(preprocessed)

            self.spells[filename] = {
                "img_org": cv2.resize(image, (64, 64)),
                "img_pre": preprocessed,
                "kp": kp,
                "desc": desc,
                "hist": self.calc_hist(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
            }

    def calc_hist(self, img1_hsv):
        hist_img1 = cv2.calcHist([img1_hsv], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist_img1 = cv2.normalize(hist_img1, None, norm_type=cv2.NORM_MINMAX).flatten()

        return hist_img1

    def comp_hist(self, h1, h2):
        return cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)

    def template_match(self, i1, i2):
        res = cv2.matchTemplate(i1, i2, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        return max_val

    def get_spell_name(self, skill_img):
        i1 = cv2.resize(skill_img, (64, 64))

        img1_hsv = cv2.cvtColor(skill_img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(img1_hsv)

        mean_s = np.mean(s)
        mean_v = np.mean(v)

        mean_t = (mean_s / 80 + mean_v / 60) / 2

        if mean_v < 25 or mean_t < 0.95:
            return None

        hist = self.calc_hist(img1_hsv)

        result_hist = {k: self.comp_hist(v["hist"], hist) for k, v in self.spells.items()}
        result_hist = {k: v for k, v in sorted(result_hist.items(), reverse=True, key=lambda item: item[1])}
        result_hist = dict(list(result_hist.items())[:100])

        results_match = {k: self.template_match(v["img_org"], i1) for k, v in self.spells.items() if k in result_hist}

        results_comb = {k: (v + result_hist[k] * 0.75) / 2 for k, v in results_match.items()}

        results = {k: v for k, v in sorted(results_comb.items(), reverse=True, key=lambda item: item[1])}

        spellname, score = list(results.items())[0]

        if score < 0.4:
            return None

        return spellname

    def find_spells(self, top_img):
        found_spells = []

        preprocessed_top = self.image_locator.preprocess(top_img)
        kp_top, desc_top = self.image_locator.kp_desc(preprocessed_top)

        for spell, data in self.spells.items():
            matches = self.image_locator.match_descriptors(data["desc"], desc_top)
            good = self.image_locator.good_matches(matches, 0.5)

            if len(good) > 4:
                points = self.image_locator.get_points(data["img_pre"], data["kp"], kp_top, good)

                if points is not None:
                    found_spells.append(spell)
                    self.point_history.append(points)

        return found_spells

    def get_skill_image(self, top_img, avg):
        pts2 = np.float32([[0, 0], [0, 64 - 1], [64 - 1, 64 - 1], [64 - 1, 0]]).reshape(-1, 1, 2)
        M = cv2.getPerspectiveTransform(avg.astype(np.float32), pts2)
        return cv2.warpPerspective(top_img, M, (64, 64))

    def get_skill_images(self, top_img, averages):
        skill_images = []

        for avg in averages:
            skill_images.append(self.get_skill_image(top_img, avg))

        return skill_images
