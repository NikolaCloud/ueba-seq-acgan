"""Leakage-safe lookup of organisational role metadata published by CERT."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def roles_for_windows(users: np.ndarray, end_days: np.ndarray, ldap_dir: Path) -> np.ndarray:
    """Return the role recorded in the LDAP snapshot for each window's month."""
    wanted = {(str(user), str(np.datetime64(day, "M"))) for user, day in zip(users, end_days)}
    result = {key: "unknown" for key in wanted}
    for path in ldap_dir.glob("*.csv"):
        month = path.stem
        frame = pd.read_csv(path, usecols=["user_id", "role"])
        for user, role in frame.itertuples(index=False):
            key = (str(user), month)
            if key in result:
                result[key] = str(role)
    return np.asarray([result[(str(user), str(np.datetime64(day, "M")))] for user, day in zip(users, end_days)])
