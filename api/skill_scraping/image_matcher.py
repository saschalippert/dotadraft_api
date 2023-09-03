import cv2
import numpy as np


class ImageMatcher:
    def __init__(self):
        self.detector = cv2.SIFT_create()
        self.matcher = cv2.BFMatcher(normType=cv2.NORM_L1)

    def kp_desc(self, img):
        return self.detector.detectAndCompute(img, None)

    def preprocess(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def good_matches(self, matches, distance):
        good = []
        for m, n in matches:
            if m.distance < distance * n.distance:
                good.append([m])

        return good

    def match_descriptors(self, sub_desc, top_desc):
        return self.matcher.knnMatch(sub_desc, top_desc, k=2)

    def get_box(self, kps_top, matches):
        dst_pts = np.float32([kps_top[m[0].trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        pos_x = [int(p[0][0]) for p in dst_pts]
        pos_y = [int(p[0][1]) for p in dst_pts]

        return min(pos_x), min(pos_y), max(pos_x), max(pos_y)

    def get_points(self, img_sub, kps_sub, kps_top, matches):
        src_pts = np.float32([kps_sub[m[0].queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kps_top[m[0].trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5)

        if matrix is not None:
            h, w = img_sub.shape
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            return cv2.perspectiveTransform(pts, matrix)

        return None

    def get_image(self, img_sub, img_top, kps_sub, kps_top, matches):
        h, w = img_sub.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        points = self.get_points(img_sub, kps_sub, kps_top, matches)

        perspectiveM = cv2.getPerspectiveTransform(np.float32(points), pts)
        return cv2.warpPerspective(img_top, perspectiveM, (w, h))
