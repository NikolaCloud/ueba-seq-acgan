"""Build labeled daily UEBA feature vectors from a local CERT r3.1 release.

The output contains one row per user and active day.  An anomaly is assigned
only when an event's (source, id) pair occurs in the official answer key.
This avoids a false match because CERT identifiers are unique only per log.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pandas as pd


TIME_FORMAT = "%m/%d/%Y %H:%M:%S"
CHUNK_SIZE = 250_000
EVENT_SOURCES = ("logon", "device", "file", "http", "email")


def load_anomaly_ids(answer_dir: Path, release: str) -> set[tuple[str, str]]:
    """Load answer-key events for a CERT release, including nested r4.2 files."""
    anomaly_ids: set[tuple[str, str]] = set()
    paths = list(answer_dir.glob(f"{release}-*.csv")) + list(answer_dir.glob(f"{release}-*/*.csv"))
    if not paths:
        raise FileNotFoundError(f"No answer-key files found for CERT {release} in {answer_dir}")
    for path in paths:
        with path.open(encoding="utf-8", newline="") as file:
            for row in csv.reader(file):
                anomaly_ids.add((row[0], row[1]))
    return anomaly_ids


def email_user_map(release_dir: Path) -> dict[str, str]:
    """Map corporate e-mail addresses to CERT user IDs using LDAP snapshots."""
    mapping: dict[str, str] = {}
    for ldap_file in (release_dir / "LDAP").glob("*.csv"):
        header = pd.read_csv(ldap_file, nrows=0).columns
        email_column = next((column for column in header if column.lower() == "email"), None)
        if email_column is None:
            raise ValueError(f"No e-mail address column in {ldap_file}")
        ldap = pd.read_csv(ldap_file, usecols=["user_id", email_column])
        mapping.update(
            {
                str(email).lower(): str(user)
                for user, email in ldap[["user_id", email_column]].itertuples(index=False)
            }
        )
    return mapping


def prepare_common(frame: pd.DataFrame, source: str, anomaly_ids: set[tuple[str, str]]) -> pd.DataFrame:
    frame["timestamp"] = pd.to_datetime(frame["date"], format=TIME_FORMAT)
    frame["day"] = frame["timestamp"].dt.floor("D")
    frame["hour"] = frame["timestamp"].dt.hour
    # Counts may exceed 127 in a single day (especially r4.2 HTTP/device logs);
    # int8 groupby sums would silently overflow and corrupt anomaly labels.
    frame["is_after_hours"] = ((frame["hour"] < 6) | (frame["hour"] >= 19)).astype("int32")
    frame["is_weekend"] = (frame["timestamp"].dt.dayofweek >= 5).astype("int32")
    frame["is_anomaly_event"] = frame["id"].map(lambda value: (source, value) in anomaly_ids).astype("int32")
    return frame


def aggregate_source(
    release_dir: Path,
    source: str,
    anomaly_ids: set[tuple[str, str]],
    mail_users: dict[str, str],
) -> list[pd.DataFrame]:
    """Read a source in chunks and return daily aggregate chunks."""
    columns = None
    results: list[pd.DataFrame] = []
    for frame in pd.read_csv(release_dir / f"{source}.csv", chunksize=CHUNK_SIZE, usecols=columns):
        if source == "email":
            # r5.2 provides the sender user directly; earlier releases require
            # resolving the sender address through LDAP.
            if "user" not in frame.columns:
                frame["user"] = frame["from"].astype(str).str.lower().map(mail_users)
            frame = frame.dropna(subset=["user"])
        frame = prepare_common(frame, source, anomaly_ids)
        keys = ["user", "day"]
        aggregates: dict[str, tuple[str, str]] = {
            f"{source}_events": ("id", "size"),
            "after_hours_events": ("is_after_hours", "sum"),
            "weekend_events": ("is_weekend", "sum"),
            "anomaly_events": ("is_anomaly_event", "sum"),
        }
        if source == "logon":
            frame["logon_count"] = (frame["activity"] == "Logon").astype("int32")
            frame["logoff_count"] = (frame["activity"] == "Logoff").astype("int32")
            aggregates.update(logon_count=("logon_count", "sum"), logoff_count=("logoff_count", "sum"))
        elif source == "device":
            frame["device_connect"] = (frame["activity"] == "Connect").astype("int32")
            aggregates["device_connect"] = ("device_connect", "sum")
        elif source == "file":
            frame["file_bytes_text"] = frame["content"].fillna("").str.len()
            aggregates["file_content_chars"] = ("file_bytes_text", "sum")
        elif source == "http":
            url = frame["url"].fillna("").str.lower()
            frame["job_search"] = url.str.contains(r"job|career|resume|linkedin|indeed", regex=True).astype("int32")
            frame["leak_site"] = url.str.contains(r"wikileaks", regex=True).astype("int32")
            aggregates.update(http_job_search=("job_search", "sum"), http_leak_site=("leak_site", "sum"))
        elif source == "email":
            recipients = frame["to"].fillna("").str.lower()
            frame["external_recipient"] = (~recipients.str.contains("@dtaa\.com", regex=True)).astype("int32")
            frame["email_size"] = pd.to_numeric(frame["size"], errors="coerce").fillna(0)
            frame["attachments"] = pd.to_numeric(frame["attachments"], errors="coerce").fillna(0)
            aggregates.update(
                email_external=("external_recipient", "sum"),
                email_size=("email_size", "sum"),
                email_attachments=("attachments", "sum"),
            )
        results.append(frame.groupby(keys, observed=True).agg(**aggregates).reset_index())
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, default=Path("data/raw/cert/r3.1/r3.1"))
    parser.add_argument("--release", default="r3.1", help="CERT release used to select answer-key files")
    parser.add_argument("--answer-dir", type=Path, default=Path("data/raw/cert/answers/answers"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/r3.1_daily_features.parquet"))
    args = parser.parse_args()

    anomaly_ids = load_anomaly_ids(args.answer_dir, args.release)
    mail_users = email_user_map(args.release_dir)
    daily_parts: list[pd.DataFrame] = []
    for source in EVENT_SOURCES:
        print(f"Aggregating {source}...")
        daily_parts.extend(aggregate_source(args.release_dir, source, anomaly_ids, mail_users))

    daily = pd.concat(daily_parts, ignore_index=True)
    numeric = daily.select_dtypes(include="number").columns
    daily = daily.groupby(["user", "day"], as_index=False)[list(numeric)].sum()
    daily["anomaly"] = (daily.pop("anomaly_events") > 0).astype("int8")
    daily["day_of_week"] = daily["day"].dt.dayofweek.astype("int8")
    daily["month"] = daily["day"].dt.month.astype("int8")
    daily = daily.sort_values(["day", "user"]).reset_index(drop=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(args.output, index=False)
    print(f"Saved {len(daily):,} daily rows for {daily['user'].nunique():,} users: {args.output}")
    print(f"Anomalous days: {daily['anomaly'].sum():,}")


if __name__ == "__main__":
    main()
