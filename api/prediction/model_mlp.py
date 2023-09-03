import torch
from torch import nn


class ModelMLP(nn.Module):

    def __init__(self, hero_size, skill_size, player_hidden, player_out, team_hidden, team_out, match_hidden, p_dropout):
        super(ModelMLP, self).__init__()

        self.p_dropout = p_dropout

        hero_embed_len = hero_size
        skill_embed_len = skill_size
        player_embed_len = hero_embed_len + (skill_embed_len * 4)

        self.embed_hero = nn.Embedding(120, hero_embed_len)
        self.embed_skill = nn.Embedding(479 + 1, skill_embed_len)

        self.player_model = nn.Sequential(
            nn.Dropout(p_dropout),
            nn.Linear(player_embed_len, player_hidden),
            nn.LeakyReLU(),
            nn.Dropout(p_dropout),
            nn.Linear(player_hidden, player_out),
            nn.LeakyReLU()
        )

        self.team_model = nn.Sequential(
            nn.Dropout(p_dropout),
            nn.Linear(player_out * 5, team_hidden),
            nn.LeakyReLU(),
            nn.Dropout(p_dropout),
            nn.Linear(team_hidden, team_out),
            nn.LeakyReLU()
        )

        self.match_model = nn.Sequential(
            nn.Dropout(p_dropout),
            nn.Linear(team_out * 2, match_hidden),
            nn.LeakyReLU(),
            nn.Dropout(p_dropout),
            nn.Linear(match_hidden, 2),
            nn.Softmax(dim=1)
        )

    def forward(self, x, randomize):
        device = next(self.parameters()).device

        # embed
        h = self.embed_hero(x[:, :, 0])
        s = x[:, :, 1:] + 1

        if randomize:
            probs = torch.zeros(s.size(), dtype=torch.float32, device=device).uniform_(0, 1)
            s = torch.where(probs > self.p_dropout, s, torch.zeros_like(s))

        s = self.embed_skill(s)

        # shuffle skills
        if randomize:
            r = torch.randperm(s.size(2))
            s = s[:, :, r, :]

        s = s.view(s.size(0), s.size(1), s.size(2) * s.size(3))

        hs = torch.cat((h, s), 2)

        p = self.player_model(hs)

        # shuffle players
        if randomize:
            r1 = torch.randperm(5)
            r2 = torch.randperm(5) + 5

            t1_in = p[:, r1, :]
            t2_in = p[:, r2, :]
        else:
            t1_in = p[:, 0:5, :]
            t2_in = p[:, 5:, :]

        t1_in = t1_in.view(p.size(0), 5 * p.size(2))
        t2_in = t2_in.view(p.size(0), 5 * p.size(2))

        t1 = self.team_model(t1_in)
        t2 = self.team_model(t2_in)

        m = torch.cat((t1, t2), 1)

        x = self.match_model(m)

        return x
