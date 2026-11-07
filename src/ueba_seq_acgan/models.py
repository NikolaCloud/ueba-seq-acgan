"""Sequential ACGAN components for UEBA feature sequences."""

from __future__ import annotations

import torch
from torch import nn


class SequenceGenerator(nn.Module):
    """Generate a normalized feature sequence conditioned on normal/anomaly."""

    def __init__(self, feature_dim: int, latent_dim: int = 32, hidden_dim: int = 64) -> None:
        super().__init__()
        self.class_embedding = nn.Embedding(2, 8)
        self.gru = nn.GRU(latent_dim + 8, hidden_dim, batch_first=True)
        self.output = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.LeakyReLU(0.2), nn.Linear(hidden_dim, feature_dim))
        self.latent_dim = latent_dim

    def forward(self, noise: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        condition = self.class_embedding(labels).unsqueeze(1).expand(-1, noise.size(1), -1)
        encoded, _ = self.gru(torch.cat((noise, condition), dim=-1))
        return self.output(encoded)


class SequenceDiscriminator(nn.Module):
    """GRU encoder with source and anomaly-classification heads."""

    def __init__(self, feature_dim: int, hidden_dim: int = 64) -> None:
        super().__init__()
        self.gru = nn.GRU(feature_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.shared = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.LeakyReLU(0.2), nn.Dropout(0.15))
        self.source_head = nn.Linear(hidden_dim, 1)  # 1 = real, 0 = synthetic
        self.anomaly_head = nn.Linear(hidden_dim, 2)  # 0 = normal, 1 = anomaly

    def forward(self, sequence: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        _, state = self.gru(sequence)
        embedding = self.shared(torch.cat((state[-2], state[-1]), dim=-1))
        return self.source_head(embedding).squeeze(-1), self.anomaly_head(embedding)


class StableSequenceGenerator(SequenceGenerator):
    """Bounded generator for inputs transformed to the [-1, 1] domain."""

    def forward(self, noise: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        return torch.tanh(super().forward(noise, labels))


class StableSequenceDiscriminator(SequenceDiscriminator):
    """Discriminator with normalized input and a reusable feature embedding."""

    def __init__(self, feature_dim: int, hidden_dim: int = 64) -> None:
        super().__init__(feature_dim, hidden_dim)
        self.input_norm = nn.LayerNorm(feature_dim)
        self.source_head = nn.utils.spectral_norm(nn.Linear(hidden_dim, 1))
        self.anomaly_head = nn.utils.spectral_norm(nn.Linear(hidden_dim, 2))

    def encode(self, sequence: torch.Tensor) -> torch.Tensor:
        _, state = self.gru(self.input_norm(sequence))
        return self.shared(torch.cat((state[-2], state[-1]), dim=-1))

    def forward(self, sequence: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        embedding = self.encode(sequence)
        return self.source_head(embedding).squeeze(-1), self.anomaly_head(embedding)


class ScenarioSequenceGenerator(StableSequenceGenerator):
    """Bounded generator conditioned on normal plus individual anomaly scenarios."""

    def __init__(self, feature_dim: int, scenarios: int = 5, latent_dim: int = 32, hidden_dim: int = 64) -> None:
        super().__init__(feature_dim, latent_dim, hidden_dim)
        self.class_embedding = nn.Embedding(scenarios, 8)


class ScenarioSequenceDiscriminator(StableSequenceDiscriminator):
    """Two-head discriminator; source score is conditioned by scenario projection."""

    def __init__(self, feature_dim: int, scenarios: int = 5, hidden_dim: int = 64) -> None:
        super().__init__(feature_dim, hidden_dim)
        self.scenario_projection = nn.Embedding(scenarios, hidden_dim)

    def forward(self, sequence: torch.Tensor, scenario: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        embedding = self.encode(sequence)
        source = self.source_head(embedding).squeeze(-1)
        source = source + (embedding * self.scenario_projection(scenario)).sum(dim=-1) / embedding.size(-1) ** 0.5
        return source, self.anomaly_head(embedding)


class NormalSequenceEncoder(nn.Module):
    def __init__(self, feature_dim: int, latent_dim: int = 32) -> None:
        super().__init__(); self.gru = nn.GRU(feature_dim, 64, batch_first=True, bidirectional=True); self.output = nn.Linear(128, latent_dim)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, h = self.gru(x); return self.output(torch.cat((h[-2], h[-1]), -1))

class NormalSequenceDecoder(nn.Module):
    def __init__(self, feature_dim: int, latent_dim: int = 32) -> None:
        super().__init__(); self.gru = nn.GRU(latent_dim, 64, batch_first=True); self.output = nn.Linear(64, feature_dim)
    def forward(self, z: torch.Tensor, length: int) -> torch.Tensor:
        h, _ = self.gru(z.unsqueeze(1).expand(-1, length, -1)); return torch.tanh(self.output(h))


class GANomalySequenceEncoder(nn.Module):
    """Map a behavioural sequence to a compact normal-manifold representation."""

    def __init__(self, feature_dim: int, latent_dim: int = 48, hidden_dim: int = 96) -> None:
        super().__init__()
        self.gru = nn.GRU(feature_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.output = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.LeakyReLU(0.2), nn.Linear(hidden_dim, latent_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, state = self.gru(x)
        return self.output(torch.cat((state[-2], state[-1]), dim=-1))


class GANomalySequenceDecoder(nn.Module):
    """Decode a latent representation with a learnable position for every day."""

    def __init__(self, feature_dim: int, latent_dim: int = 48, hidden_dim: int = 96, max_length: int = 32) -> None:
        super().__init__()
        self.position = nn.Embedding(max_length, 12)
        self.gru = nn.GRU(latent_dim + 12, hidden_dim, batch_first=True)
        self.output = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.LeakyReLU(0.2), nn.Linear(hidden_dim, feature_dim), nn.Tanh())

    def forward(self, z: torch.Tensor, length: int) -> torch.Tensor:
        positions = torch.arange(length, device=z.device)
        pos = self.position(positions).unsqueeze(0).expand(z.size(0), -1, -1)
        latent = z.unsqueeze(1).expand(-1, length, -1)
        decoded, _ = self.gru(torch.cat((latent, pos), dim=-1))
        return self.output(decoded)


class GANomalySequenceDiscriminator(nn.Module):
    """GAN critic with an explicit feature embedding for feature matching."""

    def __init__(self, feature_dim: int, hidden_dim: int = 96) -> None:
        super().__init__()
        self.input_norm = nn.LayerNorm(feature_dim)
        self.gru = nn.GRU(feature_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.embedding = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.LeakyReLU(0.2), nn.Dropout(0.10))
        self.source = nn.utils.spectral_norm(nn.Linear(hidden_dim, 1))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        _, state = self.gru(self.input_norm(x))
        return self.embedding(torch.cat((state[-2], state[-1]), dim=-1))

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.encode(x)
        return self.source(features).squeeze(-1), features


class ConditionalForecastGenerator(nn.Module):
    """Conditional GAN generator: forecast a user's next behavioural vector."""

    def __init__(self, feature_dim: int, count_indices: list[int], users: int, hidden_dim: int = 96) -> None:
        super().__init__()
        self.count_indices = count_indices
        self.calendar_indices = [i for i in range(feature_dim) if i not in count_indices]
        self.user_embedding = nn.Embedding(users + 1, 24, padding_idx=0)
        self.context = nn.GRU(feature_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.output = nn.Sequential(nn.Linear(hidden_dim * 2 + 24 + len(self.calendar_indices), hidden_dim), nn.LeakyReLU(0.2), nn.Linear(hidden_dim, len(count_indices)), nn.Tanh())

    def forward(self, history: torch.Tensor, user: torch.Tensor, calendar: torch.Tensor) -> torch.Tensor:
        _, state = self.context(history)
        encoded = torch.cat((state[-2], state[-1], self.user_embedding(user), calendar), dim=-1)
        counts = self.output(encoded)
        result = calendar.new_zeros((len(history), history.size(-1)))
        result[:, self.count_indices] = counts
        result[:, self.calendar_indices] = calendar
        return result


class ConditionalForecastDiscriminator(nn.Module):
    """Judge whether a target day is plausible for a context and user identity."""

    def __init__(self, feature_dim: int, users: int, hidden_dim: int = 96) -> None:
        super().__init__()
        self.user_embedding = nn.Embedding(users + 1, 24, padding_idx=0)
        self.context = nn.GRU(feature_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.classifier = nn.Sequential(nn.Linear(hidden_dim * 2 + feature_dim + 24, hidden_dim), nn.LeakyReLU(0.2), nn.Dropout(0.1), nn.utils.spectral_norm(nn.Linear(hidden_dim, 1)))

    def forward(self, history: torch.Tensor, target: torch.Tensor, user: torch.Tensor) -> torch.Tensor:
        _, state = self.context(history)
        encoded = torch.cat((state[-2], state[-1], target, self.user_embedding(user)), dim=-1)
        return self.classifier(encoded).squeeze(-1)


class RoleConditionalForecastGenerator(ConditionalForecastGenerator):
    """Forecast generator conditioned on both individual and LDAP role context."""

    def __init__(self, feature_dim: int, count_indices: list[int], users: int, roles: int, hidden_dim: int = 96) -> None:
        super().__init__(feature_dim, count_indices, users, hidden_dim)
        self.role_embedding = nn.Embedding(roles + 1, 16, padding_idx=0)
        self.output = nn.Sequential(nn.Linear(hidden_dim * 2 + 24 + 16 + len(self.calendar_indices), hidden_dim), nn.LeakyReLU(0.2), nn.Linear(hidden_dim, len(count_indices)), nn.Tanh())

    def forward(self, history: torch.Tensor, user: torch.Tensor, role: torch.Tensor, calendar: torch.Tensor) -> torch.Tensor:
        _, state = self.context(history)
        encoded = torch.cat((state[-2], state[-1], self.user_embedding(user), self.role_embedding(role), calendar), dim=-1)
        counts = self.output(encoded); result = calendar.new_zeros((len(history), history.size(-1))); result[:, self.count_indices] = counts; result[:, self.calendar_indices] = calendar
        return result


class RoleConditionalForecastDiscriminator(ConditionalForecastDiscriminator):
    """Conditional GAN critic that shares normality patterns within a role."""

    def __init__(self, feature_dim: int, users: int, roles: int, hidden_dim: int = 96) -> None:
        super().__init__(feature_dim, users, hidden_dim)
        self.role_embedding = nn.Embedding(roles + 1, 16, padding_idx=0)
        self.classifier = nn.Sequential(nn.Linear(hidden_dim * 2 + feature_dim + 24 + 16, hidden_dim), nn.LeakyReLU(0.2), nn.Dropout(0.1), nn.utils.spectral_norm(nn.Linear(hidden_dim, 1)))

    def forward(self, history: torch.Tensor, target: torch.Tensor, user: torch.Tensor, role: torch.Tensor) -> torch.Tensor:
        _, state = self.context(history)
        encoded = torch.cat((state[-2], state[-1], target, self.user_embedding(user), self.role_embedding(role)), dim=-1)
        return self.classifier(encoded).squeeze(-1)


class MITRESequenceDiscriminator(nn.Module):
    """Two-head sequence critic: source plus normal-or-MITRE-scenario class."""

    def __init__(self, feature_dim: int, scenarios: int = 6, hidden_dim: int = 64) -> None:
        super().__init__()
        self.gru = nn.GRU(feature_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.shared = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.LeakyReLU(0.2), nn.Dropout(0.15))
        self.source_head = nn.Linear(hidden_dim, 1)
        self.scenario_head = nn.Linear(hidden_dim, scenarios + 1)  # 0 normal; 1..N simulated MITRE profiles

    def forward(self, sequence: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        _, state = self.gru(sequence)
        embedding = self.shared(torch.cat((state[-2], state[-1]), dim=-1))
        return self.source_head(embedding).squeeze(-1), self.scenario_head(embedding)
