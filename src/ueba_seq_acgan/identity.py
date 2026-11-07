"""Stable presentation identities for anonymized CERT users."""

from __future__ import annotations

import hashlib

_MALE_NAMES = ("Александр", "Михаил", "Дмитрий", "Андрей", "Сергей", "Николай", "Илья", "Максим", "Антон", "Павел", "Роман", "Виктор")
_FEMALE_NAMES = ("Анна", "Елена", "Мария", "Ольга", "Наталья", "Ирина", "Светлана", "Татьяна", "Дарья", "Виктория", "Ксения", "Юлия")
_MALE_PATRONYMICS = ("Александрович", "Михайлович", "Дмитриевич", "Андреевич", "Сергеевич", "Николаевич", "Ильич", "Максимович")
_FEMALE_PATRONYMICS = ("Александровна", "Михайловна", "Дмитриевна", "Андреевна", "Сергеевна", "Николаевна", "Ильинична", "Максимовна")
_SURNAMES = ("Соколов", "Кузнецов", "Морозов", "Волков", "Лебедев", "Новиков", "Фёдоров", "Орлов", "Макаров", "Захаров", "Белов", "Комаров", "Гусев", "Титов", "Крылов", "Виноградов", "Богданов", "Воробьёв", "Ковалёв", "Мельников", "Поляков", "Соловьёв", "Яковлев", "Громов")


def demo_full_name(user_id: str) -> str:
    """Return a deterministic, natural-looking Russian full name based on user_id hash."""
    digest = hashlib.blake2b(str(user_id).encode("utf-8"), digest_size=8).digest()
    number = int.from_bytes(digest, "big")
    female = bool(number & 1)
    surname = _SURNAMES[(number >> 1) % len(_SURNAMES)]
    if female:
        surname += "а"
        name = _FEMALE_NAMES[(number >> 9) % len(_FEMALE_NAMES)]
        patronymic = _FEMALE_PATRONYMICS[(number >> 17) % len(_FEMALE_PATRONYMICS)]
    else:
        name = _MALE_NAMES[(number >> 9) % len(_MALE_NAMES)]
        patronymic = _MALE_PATRONYMICS[(number >> 17) % len(_MALE_PATRONYMICS)]
    return f"{surname} {name} {patronymic}"


def build_demo_identities(user_ids: list[str]) -> dict[str, str]:
    """Assign unique, deterministic and stable names to a known population."""
    return {str(user_id): demo_full_name(str(user_id)) for user_id in user_ids}
