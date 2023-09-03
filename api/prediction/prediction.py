import torch
import numpy as np

from prediction.model_mlp import ModelMLP


class Prediction():
    def __init__(self, data_heroes, data_skills):
        hero_size = 32
        skill_size = 48
        player_hidden = 512
        player_out = 256
        team_hidden = 512
        team_out = 256
        match_hidden = 256
        p_dropout = 0.2

        self.model = ModelMLP(hero_size, skill_size, player_hidden, player_out, team_hidden, team_out, match_hidden, p_dropout)

        checkpoint = torch.load("data/model_cpu.pt")
        self.model.load_state_dict(checkpoint['model_state_dict'])

        self.model = self.model.to(torch.device("cpu"))

        self.model.eval()

        self.lookup_skills = {s["name"]: s["index"] for s in data_skills.values()}
        self.lookup_heroes = {h["name"]: h["index"] for h in data_heroes.values()}

    def __encode_players(self, features, index, players):
        for p, player in enumerate(players):
            hero_name = player["hero_name"]
            player_skills = player["skills"]

            features[index, p, 0] = self.lookup_heroes[hero_name]

            for i, skill in enumerate(player_skills):
                features[index, p, i + 1] = self.lookup_skills[skill]

    def predict_one(self, players):
        features = np.zeros((1, 10, 5), dtype=np.int)

        self.__encode_players(features, 0, players)

        y_pred = self.model(torch.from_numpy(features), False)

        return y_pred.detach().numpy()[0, 0]

    def predict_many(self, matches):
        features = np.zeros((len(matches), 10, 5), dtype=np.int)

        for i, players in enumerate(matches):
            self.__encode_players(features, i, players)

        y_pred = self.model(torch.from_numpy(features), False)

        return y_pred.detach().numpy()[:, 0]
