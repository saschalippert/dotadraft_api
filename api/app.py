import copy
import json
import logging
import os
import random

import boto3
import cv2
import filetype
import numpy as np
from cerberus import Validator

from skill_scraping.screen_utils import resize_screen, crop
from hero_name_ocr import HeroNameOCR
from prediction.prediction import Prediction
from preload import load_data, load_skill_matrix, load_skill_images, load_hero_matrix
from skill_scraping.skill_scraping import SkillScraping

from multiprocessing import Process, Pipe

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("loading")

body_schema = {
    'filename': {
        'type': 'string',
        'required': True,
        'regex': '^[0-9a-f]{32}\.png$'
    },
    "team_radiant": {
        'type': 'boolean',
        'required': True,
    },
    'hero_name': {
        'type': 'string',
        'required': True
    },
    "version": {
        'type': 'string',
        'required': True,
        'regex': '^[0-9]\.[0-9]\.[0-9]$'
    }
}

body_validator = Validator(body_schema)

upload_bucket = os.environ['UPLOAD_BUCKET_NAME']

s3_resource = boto3.resource('s3')

data_heroes, data_skills, stats_skills = load_data()
all_hero_names = {k for k, v in data_heroes.items()}
skill_matrix = load_skill_matrix()
hero_matrix = load_hero_matrix()
skill_images = load_skill_images()

count_skills = len(skill_images)

logger.info(f"loaded {count_skills} skill images")

skill_scraping = SkillScraping(data_skills, skill_images, skill_matrix)
prediction = Prediction(data_heroes, data_skills)
hero_ocr = HeroNameOCR(data_heroes)


def ocr_heroes(result_pipe, screen, aspect_ratio, team_radiant):
    hero_names = []

    for i in range(10):
        hero_box = hero_matrix[aspect_ratio][i]
        hero_screen = crop(screen, hero_box)

        width = int(hero_screen.shape[1] * 4)
        height = int(hero_screen.shape[0] * 4)
        dim = (width, height)
        hero_screen = cv2.resize(hero_screen, dim, interpolation=cv2.INTER_AREA)

        hero_screen = cv2.cvtColor(hero_screen, cv2.COLOR_BGR2HSV)
        team_id = i // 5 if team_radiant else (9 - i) // 5
        hero_name = hero_ocr.parse_hero_name(hero_screen, team_id)

        hero_names.append(hero_name)

    result_pipe.send(hero_names)
    result_pipe.close()


def analyse_players(result_pipe, screen, aspect_ratio):
    player_skills, skill_count = skill_scraping.analyse_players(screen, aspect_ratio)

    result_pipe.send((player_skills, skill_count))
    result_pipe.close()


def lambda_handler(event, context):
    logger.info("handling event")

    body_str = event.get("body", "{}")
    body = json.loads(body_str)

    if body_validator.validate(body, body_schema):
        version = body["version"]

        logger.info(f"detected version {version}")

        filename = body["filename"]
        hero_name = body["hero_name"]
        team_radiant = body["team_radiant"]

        logger.info(f"checking image {filename}")

        content_object = s3_resource.Object(upload_bucket, filename)
        img_body = content_object.get()['Body'].read()

        if filetype.is_image(img_body):
            result_messages = []

            logger.info(f"analysing image {filename}")

            screen = cv2.imdecode(np.asarray(bytearray(img_body)), cv2.IMREAD_COLOR)
            screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)

            screen, aspect_ratio = resize_screen(screen)

            ocr_receiver, ocr_sender = Pipe()
            ocr_process = Process(target=ocr_heroes, args=(ocr_sender, screen, aspect_ratio, team_radiant,))
            ocr_process.start()

            players_receiver, players_sender = Pipe()
            players_process = Process(target=analyse_players, args=(players_sender, screen, aspect_ratio,))
            players_process.start()

            main_skills = skill_scraping.analyse_main(screen, aspect_ratio)

            players_process.join()

            player_skills, skill_count = players_receiver.recv()

            skill_count += len(main_skills)

            if skill_count < 44:
                msg_txt = f"{skill_count}/48 skills detected. avoid overlapping popups before refreshing"
                logger.info(msg_txt)

                result_messages.append({
                    "level": "warning",
                    "text": msg_txt
                })

            hero_names = ocr_receiver.recv()

            ocr_process.join()

            win_rates = None

            logger.info(f"provided {hero_name} {team_radiant}")
            logger.info(f"found heroes {hero_names}")

            if hero_name in hero_names:
                idx_player = hero_names.index(hero_name)
                logger.info(f"hero name found {hero_name} at {idx_player}")

                unpicked_heroes = random.sample(all_hero_names.difference(hero_names), 10)

                players = []

                for i, name in enumerate(hero_names):
                    override_name = name

                    if not name:
                        override_name = unpicked_heroes[i]
                        hero_names[i] = override_name
                        logger.info(f"overriding empty name {i} with {override_name}")

                    players.append({
                        "hero_name": override_name,
                        "skills": player_skills[i]
                    })

                logger.info(players)

                matches = []

                matches.append(players)

                picked_skills = len(players[idx_player]["skills"])
                if picked_skills < 4:
                    for skill in main_skills:
                        copy_players = copy.deepcopy(players)
                        copy_players[idx_player]["skills"].append(skill)
                        matches.append(copy_players)

                win_rates = prediction.predict_many(matches)

                if not team_radiant:
                    win_rates = 1 - win_rates
            else:
                msg_txt = f"hero not detected. advantage not available. avoid overlapping popups before refreshing"
                logger.info(msg_txt)

                result_messages.append({
                    "level": "warning",
                    "text": msg_txt
                })

            match_win_rate = win_rates[0].item() if win_rates is not None else 0.5

            skills_win_rate = {s: data_skills[s]["win_ratio"] for s in main_skills}
            skills_win_rate = {k: v for k, v in sorted(skills_win_rate.items(), reverse=True, key=lambda item: item[1])}

            result_skills = {}

            for skill, wr in skills_win_rate.items():
                win_rate_advantage = 0.0

                if win_rates is not None and len(win_rates) > 1:
                    idx_skill = main_skills.index(skill)
                    win_rate_skill = win_rates[idx_skill + 1]
                    win_rate_advantage = (win_rate_skill - match_win_rate).item()

                skill_data = data_skills[skill]
                result_skills[skill] = {
                    "name": skill,
                    "win_rate_advantage": win_rate_advantage,
                    "win_rate_estimated": skill_data['win_ratio'] + win_rate_advantage,
                    'has_scepter_upgrade': skill_data['has_scepter_upgrade'],
                    'has_shard_upgrade': skill_data['has_shard_upgrade'],
                    'has_shard_skill': skill_data['has_shard_skill'],
                    'has_special_bonus': skill_data['has_special_bonus'],
                    'win_ratio': skill_data['win_ratio'],
                    'kd_ratio': skill_data['kd_ratio'],
                    'avg_kills': skill_data['avg_kills'],
                    'avg_gpm': skill_data['avg_gpm'],
                }

            return {
                "body": json.dumps({
                    "abilities": result_skills,
                    "match_win_rate": match_win_rate,
                    "skill_stats": stats_skills,
                    "messages": result_messages
                }),
                "statusCode": 200
            }

        return {
            "body": "no valid image",
            "statusCode": 400
        }

    return {
        "body": json.dumps(body_validator.errors),
        "statusCode": 400
    }
