import json
import logging

from skill_scraping.screen_utils import idx_radiant, idx_dire, idx_main, idx_player
from skill_scraping.skill_classifier import SkillClassifier

logger = logging.getLogger()
logger.setLevel(logging.INFO)

screen_idx_radiant = idx_radiant()
screen_idx_dire = idx_dire()
screen_idx_main = idx_main()


class SkillScraping():
    def __init__(self, data_skills, skill_images, screen_matrix_map):
        self.data_skills = data_skills
        self.skill_matrix_map = screen_matrix_map
        self.skill_classifier = SkillClassifier(skill_images)

    def get_skills(self, screen, averages):
        skill_images = self.skill_classifier.get_skill_images(screen, averages)
        found_spells = [self.skill_classifier.get_spell_name(s) for s in skill_images]
        return [i for i in found_spells if i]

    def analyse_screen(self, screen, aspect_ratio):
        main_skills = self.analyse_main(screen, aspect_ratio)
        player_skills, skill_count = self.analyse_players(screen, aspect_ratio)

        return main_skills, player_skills, len(main_skills) + player_skills

    def analyse_main(self, screen, aspect_ratio):
        skill_matrix = self.skill_matrix_map[aspect_ratio]
        main_skills = self.get_skills(screen, skill_matrix[screen_idx_main])

        return main_skills

    def analyse_players(self, screen, aspect_ratio):
        skill_matrix = self.skill_matrix_map[aspect_ratio]

        skill_count = 0
        player_skills = []

        for i in range(10):
            found_skills = self.get_skills(screen, skill_matrix[idx_player(i)])
            player_skills.append(found_skills)

            skill_count += len(found_skills)

        return player_skills, skill_count
