import json

import h5py


def load_data():
    with h5py.File("data/data.h5", 'r') as hf:
        data_heroes = json.loads(hf['data_heroes'][()])
        data_skills = json.loads(hf['data_skills'][()])

        # stats_heroes = json.loads(hf['stats_heroes'][()])
        stats_skills = json.loads(hf['stats_skills'][()])

        return data_heroes, data_skills, stats_skills


def load_skill_matrix():
    matrix_map = {}

    with h5py.File("data/skillmatrix.h5", 'r') as hf:
        for key, value in hf.items():
            matrix_map[key] = value[()]

    return matrix_map


def load_hero_matrix():
    matrix_map = {}

    with h5py.File("data/heromatrix.h5", 'r') as hf:
        for key, value in hf.items():
            matrix_map[key] = value[()]

    return matrix_map


def load_skill_images():
    skill_images = {}

    with h5py.File("data/skill_images.h5", 'r') as hf:
        for key, value in hf.items():
            skill_images[key] = value[()]

    return skill_images
