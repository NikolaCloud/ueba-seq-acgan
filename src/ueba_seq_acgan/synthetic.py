"""Runtime normal-forecast generation and auditable MITRE scenario simulation."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import torch

from ueba_seq_acgan.identity import build_demo_identities
from ueba_seq_acgan.ldap import roles_for_windows
from ueba_seq_acgan.models import RoleConditionalForecastGenerator, SequenceDiscriminator
from ueba_seq_acgan.risk import UEBARiskScorer

FEATURE_LABELS = {
    "logon_events": "События входа",
    "after_hours_events": "Активность вне графика",
    "weekend_events": "Активность в выходные",
    "logon_count": "Входы",
    "logoff_count": "Выходы",
    "device_events": "События устройств",
    "device_connect": "Подключения USB",
    "file_events": "Файловые операции",
    "file_content_chars": "Объём файлов",
    "http_events": "Веб-запросы",
    "http_job_search": "Поиск работы в вебе",
    "http_leak_site": "Обращения к leak-сайтам",
    "email_events": "Почтовые события",
    "email_external": "Внешние письма",
    "email_size": "Объём почты",
    "email_attachments": "Вложения",
    "day_of_week": "День недели",
    "month": "Месяц",
}

ROLE_LABELS = {
    "Accountant": "бухгалтер",
    "AdministrativeAssistant": "административный помощник",
    "AdministrativeStaff": "административный сотрудник",
    "Attorney": "юрист",
    "ChiefEngineer": "главный инженер",
    "ChiefExecutiveOfficer": "генеральный директор",
    "ComputerProgrammer": "программист",
    "ComputerScientist": "специалист по вычислительным системам",
    "Director": "директор",
    "ElectricalEngineer": "инженер-электрик",
    "Engineer": "инженер",
    "FieldServiceEngineer": "выездной инженер",
    "FinancialAnalyst": "финансовый аналитик",
    "HardwareEngineer": "инженер аппаратного обеспечения",
    "HealthSafetyEngineer": "инженер по охране труда",
    "HumanResourceSpecialist": "специалист по персоналу",
    "ITAdmin": "системный администратор",
    "IndustrialEngineer": "промышленный инженер",
    "InstructionalCoordinator": "координатор обучения",
    "LabManager": "руководитель лаборатории",
    "Manager": "менеджер",
    "MaterialsEngineer": "инженер по материалам",
    "Mathematician": "математик",
    "MechanicalEngineer": "инженер-механик",
    "Nurse": "медицинский работник",
    "NursePractitioner": "старший медицинский работник",
    "Physicist": "физик",
    "President": "президент компании",
    "ProductionLineWorker": "работник производства",
    "ProjectManager": "руководитель проекта",
    "PurchasingClerk": "специалист по закупкам",
    "QualityEngineer": "инженер по качеству",
    "Salesman": "специалист по продажам",
    "Scientist": "научный сотрудник",
    "SecurityGuard": "сотрудник охраны",
    "SoftwareDeveloper": "разработчик ПО",
    "SoftwareEngineer": "инженер-программист",
    "SoftwareQualityEngineer": "инженер по качеству ПО",
    "Statistician": "статистик",
    "StockroomClerk": "кладовщик",
    "Supervisor": "руководитель группы",
    "SystemsEngineer": "системный инженер",
    "TechnicalTrainer": "технический тренер",
    "TechnicalWriter": "технический писатель",
    "Technician": "технический специалист",
    "TestEngineer": "инженер-тестировщик",
    "VicePresident": "вице-президент",
    "WebDeveloper": "веб-разработчик",
}


class MITREScenarioSimulator:
    """Generate a normal forecast, apply a declared profile and score both."""

    def __init__(
        self,
        sequences_path: Path,
        manifest_path: Path,
        normal_gan_dir: Path,
        mitre_dir: Path,
        baseline_dir: Path,
        ldap_dir: Path,
        profiles_path: Path,
    ) -> None:
        loaded = np.load(sequences_path)
        self.x = loaded["x"].astype(np.float32)
        self.y = loaded["y"].astype(np.int8)
        self.users = loaded["user"].astype(str)
        self.identities = build_demo_identities(self.users.tolist())
        self.days = loaded["end_day"].astype("datetime64[D]")
        self.features = json.loads(manifest_path.read_text(encoding="utf-8"))["features"]
        self.profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
        self.profile_by_id = {profile["id"]: profile for profile in self.profiles}

        state = torch.load(normal_gan_dir / "checkpoint.pt", map_location="cpu", weights_only=True)
        bundle = joblib.load(normal_gan_dir / "transformer_users_roles.joblib")
        self.transformer = bundle["transformer"]
        self.user_index = bundle["user_index"]
        self.role_index = bundle["role_index"]
        self.count_indices = list(state["count_indices"])
        self.calendar_indices = list(state["calendar_indices"])
        self.generator = RoleConditionalForecastGenerator(
            state["feature_dim"],
            self.count_indices,
            len(self.user_index),
            len(self.role_index),
        ).eval()
        self.generator.load_state_dict(state["generator"])

        mitre_state = torch.load(mitre_dir / "checkpoint.pt", map_location="cpu", weights_only=True)
        self.detector = SequenceDiscriminator(mitre_state["feature_dim"]).eval()
        self.detector.load_state_dict(mitre_state["discriminator"])
        self.risk = UEBARiskScorer(baseline_dir, manifest_path)
        self.roles = roles_for_windows(self.users, self.days, ldap_dir).astype(str)
        self.clean = np.flatnonzero(self.y == 0)

    def scenario_catalogue(self) -> list[dict]:
        return [
            {
                "id": profile["id"],
                "name": profile["ru_name"],
                "description": profile["description"],
                "features": [FEATURE_LABELS[name] for name in profile["features"]],
            }
            for profile in self.profiles
        ]

    def _base_index(self, rng: np.random.Generator, user: str | None) -> int:
        if user and str(user).strip():
            target_user = str(user).strip()
            matching = np.flatnonzero((self.users == target_user) & (self.y == 0))
            if len(matching):
                return int(rng.choice(matching))
            all_user_windows = np.flatnonzero(self.users == target_user)
            if len(all_user_windows):
                return int(rng.choice(all_user_windows))
        return int(rng.choice(self.clean))

    def _calendar(self, day: np.datetime64) -> np.ndarray:
        raw = np.zeros((1, len(self.features)), dtype=np.float32)
        date = day.astype(object)
        raw[0, self.features.index("day_of_week")] = date.weekday()
        raw[0, self.features.index("month")] = date.month
        return self.transformer.transform(raw)[0, self.calendar_indices]

    @torch.inference_mode()
    def generate(
        self,
        scenario_id: str,
        intensity: float = 1.0,
        seed: int | None = None,
        user: str | None = None,
        custom_profile: dict | None = None,
    ) -> dict:
        if custom_profile is None and scenario_id not in self.profile_by_id:
            raise ValueError("Неизвестный MITRE-сценарий")
        if not 0.25 <= intensity <= 1.5:
            raise ValueError("Интенсивность должна быть от 0.25 до 1.5")
        if seed is None:
            seed = int(np.random.SeedSequence().generate_state(1)[0])
        rng = np.random.default_rng(seed)
        index = self._base_index(rng, user)
        chosen_user = self.users[index]
        role = self.roles[index]
        user_code = self.user_index.get(chosen_user, 0)
        role_code = self.role_index.get(role, 0)

        scaled = self.transformer.transform(self.x[index])
        history = scaled[-13:].copy()
        first_day = self.days[index]
        generated = []
        for offset in range(14):
            day = first_day + np.timedelta64(offset, "D")
            calendar = self._calendar(day)
            target = self.generator(
                torch.from_numpy(history[None]).float(),
                torch.tensor([user_code]),
                torch.tensor([role_code]),
                torch.from_numpy(calendar[None]).float(),
            )[0].numpy()
            generated.append(target)
            history = np.concatenate((history[1:], target[None]), axis=0)
        normal_scaled = np.asarray(generated, dtype=np.float32)
        scenario_scaled = normal_scaled.copy()
        if custom_profile is None:
            profile = self.profile_by_id[scenario_id]
            feature_weights = {name: 1.0 for name in profile["features"]}
            start_day, duration = 14, 1
        else:
            if not isinstance(custom_profile, dict):
                raise ValueError("Профиль конструктора должен быть объектом")
            raw_features = custom_profile.get("features", {})
            if not isinstance(raw_features, dict) or not raw_features:
                raise ValueError("Выберите хотя бы один канал конструктора")
            allowed = set(self.features) - {"day_of_week", "month"}
            if len(raw_features) > 8 or not set(raw_features).issubset(allowed):
                raise ValueError("Недопустимый набор каналов конструктора")
            feature_weights = {name: float(weight) for name, weight in raw_features.items()}
            if any(not 0.25 <= weight <= 2.0 for weight in feature_weights.values()):
                raise ValueError("Коэффициент канала должен быть от 0.25 до 2.0")
            start_day = int(custom_profile.get("start_day", 14))
            duration = int(custom_profile.get("duration", 1))
            if not 1 <= start_day <= 14 or not 1 <= duration <= 7:
                raise ValueError("День начала должен быть 1–14, длительность — 1–7")
            profile = {
                "id": "CUSTOM-MITRE",
                "ru_name": str(custom_profile.get("name", "Пользовательский сценарий"))[:80],
                "description": "Сценарий собран в интерактивном конструкторе.",
                "features": list(feature_weights),
            }
        changes = []
        affected_days = list(range(start_day - 1, min(14, start_day - 1 + duration)))
        for name, weight in feature_weights.items():
            feature_index = self.features.index(name)
            delta = float(rng.uniform(0.45, 1.10) * intensity)
            for day_index in affected_days:
                scenario_scaled[day_index, feature_index] = np.clip(
                    scenario_scaled[day_index, feature_index] + delta * weight, -1, 1
                )
            changes.append((name, delta * weight))

        normal = self.transformer.inverse_transform(normal_scaled)
        scenario = self.transformer.inverse_transform(scenario_scaled)
        normal_result = self.risk.score(normal)
        scenario_result = self.risk.score(scenario)
        _, normal_logits = self.detector(torch.from_numpy(normal_scaled[None]))
        _, scenario_logits = self.detector(torch.from_numpy(scenario_scaled[None]))
        normal_mitre = float(torch.softmax(normal_logits, dim=1)[0, 1])
        scenario_mitre = float(torch.softmax(scenario_logits, dim=1)[0, 1])
        dates = [(first_day + np.timedelta64(i, "D")).astype(str) for i in range(14)]

        series = []
        for name, transformed_delta in changes:
            feature_index = self.features.index(name)
            series.append(
                {
                    "feature": name,
                    "label": FEATURE_LABELS[name],
                    "normal": np.round(normal[:, feature_index], 2).tolist(),
                    "scenario": np.round(scenario[:, feature_index], 2).tolist(),
                    "transformed_delta": transformed_delta,
                }
            )
        return {
            "mode": "Условный GAN нормального поведения + управляемая MITRE-симуляция",
            "scenario": {
                "id": profile["id"],
                "name": profile["ru_name"],
                "description": profile["description"],
            },
            "seed": seed,
            "intensity": intensity,
            "custom": custom_profile is not None,
            "affected_days": [day + 1 for day in affected_days],
            "user": chosen_user,
            "display_name": self.identities[chosen_user],
            "role": role,
            "role_display": ROLE_LABELS.get(role, role),
            "dates": dates,
            "series": series,
            "scores": {
                "normal_risk": normal_result.risk_score,
                "scenario_risk": scenario_result.risk_score,
                "normal_mitre_probability": normal_mitre,
                "scenario_mitre_probability": scenario_mitre,
                "baseline_alert": scenario_result.risk_score >= 80,
                "mitre_alert": scenario_mitre >= 0.5,
                "alert": scenario_result.risk_score >= 80 or scenario_mitre >= 0.5,
            },
            "generation_summary": (
                "Сформирован 14-дневный прогноз нормы с симуляцией техники MITRE "
                "и оценкой системы обнаружения."
            ),
        }
