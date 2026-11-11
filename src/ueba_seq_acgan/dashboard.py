"""Build and serve the compact local UEBA research dashboard."""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from collections import defaultdict
from datetime import UTC, datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import numpy as np

from ueba_seq_acgan.identity import build_demo_identities
from ueba_seq_acgan.risk import FEATURE_DISPLAY_NAMES, UEBARiskScorer
from ueba_seq_acgan.synthetic import MITREScenarioSimulator


def build_payload(
    sequences_path: Path,
    model_dir: Path,
    manifest_path: Path,
    comparison_path: Path,
    limit: int = 100,
) -> dict:
    """Create a compact presentation payload from retained held-out sequences."""
    raw = np.load(sequences_path)
    scorer = UEBARiskScorer(model_dir, manifest_path)
    scores = scorer.probabilities(raw["x"])
    metrics = json.loads((model_dir / "metrics.json").read_text(encoding="utf-8"))
    threshold = float(metrics["validation_selected_threshold"])
    users = raw["user"].astype(str)
    days = raw["end_day"].astype("datetime64[D]").astype(str)
    labels = raw["y"].astype(np.int8)
    feature_names = scorer.feature_names[:16]
    alert_mask = scores >= threshold
    alert_true_positives = int(labels[alert_mask].sum())
    indices_by_user: dict[str, list[int]] = defaultdict(list)
    for index, user in enumerate(users):
        indices_by_user[user].append(index)

    ranked = sorted(
        indices_by_user, key=lambda user: float(scores[indices_by_user[user]].max()), reverse=True
    )
    identities = build_demo_identities(list(indices_by_user))
    rows = []
    timelines = {}
    user_peaks = np.asarray([scores[indices_by_user[user]].max() for user in indices_by_user])
    user_alerts = np.asarray(
        [(scores[indices_by_user[user]] >= threshold).sum() for user in indices_by_user]
    )
    risk_distribution = {
        "Низкий": int((user_peaks < 0.30).sum()),
        "Средний": int(((user_peaks >= 0.30) & (user_peaks < 0.55)).sum()),
        "Высокий": int(((user_peaks >= 0.55) & (user_peaks < 0.80)).sum()),
        "Критический": int((user_peaks >= 0.80).sum()),
    }
    alert_distribution = {
        "0": int((user_alerts == 0).sum()),
        "1–2": int(((user_alerts >= 1) & (user_alerts <= 2)).sum()),
        "3–5": int(((user_alerts >= 3) & (user_alerts <= 5)).sum()),
        "6+": int((user_alerts >= 6).sum()),
    }
    for user in ranked[:limit]:
        indices = np.asarray(indices_by_user[user])
        peak_index = int(indices[np.argmax(scores[indices])])
        latest_index = int(indices[-1])
        peak = scorer.score(raw["x"][peak_index])
        rows.append(
            {
                "user": user,
                "display_name": identities[user],
                "peak_day": days[peak_index],
                "peak_risk": peak.risk_score,
                "risk_band": peak.risk_band,
                "latest_risk": round(100 * scores[latest_index]),
                "alerts": int((scores[indices] >= threshold).sum()),
                "observed_anomalies": int(labels[indices].sum()),
                "drivers": peak.drivers,
            }
        )
        timelines[user] = [
            {
                "day": days[index],
                "risk": round(100 * scores[index]),
                "alert": bool(scores[index] >= threshold),
                "observed_anomaly": bool(labels[index]),
                "values": np.round(raw["x"][index, -1, :16], 2).tolist(),
                "window_mean": np.round(raw["x"][index, :, :16].mean(axis=0), 2).tolist(),
            }
            for index in indices
        ]

    comparison = {}
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    low_shot_path = Path("artifacts/r5.2_low_shot_gan/aggregate.json")
    low_shot = {}
    if low_shot_path.exists():
        low_shot = json.loads(low_shot_path.read_text(encoding="utf-8"))
    return {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "Корпоративный датасет CERT",
            "model": "Классификатор градиентного бустинга",
            "research_only": True,
            "labels_note": "Observed anomaly labels are displayed for retrospective evaluation only.",
        },
        "summary": {
            "windows": len(scores),
            "users": len(indices_by_user),
            "observed_anomalies": int(labels.sum()),
            "alerts_at_validation_threshold": int((scores >= threshold).sum()),
            "true_anomalies_at_threshold": alert_true_positives,
            "precision_at_threshold": float(alert_true_positives / max(int(alert_mask.sum()), 1)),
            "recall_at_threshold": float(alert_true_positives / max(int(labels.sum()), 1)),
            "validation_threshold": threshold,
            "test_pr_auc": float(metrics["test"]["pr_auc"]),
            "test_precision_at_100": float(metrics["test"]["precision_at_100"]),
        },
        "population": {
            "risk_distribution": risk_distribution,
            "alert_distribution": alert_distribution,
            "users_with_alerts": int((user_alerts > 0).sum()),
            "mean_peak_risk": round(float(100 * user_peaks.mean()), 1),
            "median_peak_risk": round(float(100 * np.median(user_peaks)), 1),
            "total_alerts": int(user_alerts.sum()),
        },
        "event_features": [
            {
                "key": name,
                "label": FEATURE_DISPLAY_NAMES.get(name, name),
                "unit": (
                    "байт"
                    if name == "email_size"
                    else "символов"
                    if name == "file_content_chars"
                    else "событий"
                ),
            }
            for name in feature_names
        ],
        "users": rows,
        "timelines": timelines,
        "model_comparison": comparison,
        "low_shot_augmentation": low_shot,
    }


def write_payload(payload: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


from ueba_seq_acgan.paths import resolve_resource


def serve(data_path: Path, web_dir: Path, host: str, port: int, open_browser: bool = False) -> None:
    data_path = resolve_resource(data_path)
    web_dir = resolve_resource(web_dir)
    profiles_path = resolve_resource("configs/mitre_pseudo_scenarios.json")
    if not data_path.exists():
        raise FileNotFoundError(f"Build dashboard data first: missing {data_path}")
    data = data_path.read_bytes()
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    catalogue = json.dumps(
        [
            {
                "id": item["id"],
                "name": item["ru_name"],
                "description": item["description"],
                "features": item["features"],
            }
            for item in profiles
        ],
        ensure_ascii=False,
    ).encode("utf-8")
    simulator = None
    simulator_lock = threading.Lock()
    session_body = json.dumps({"id": uuid4().hex}).encode("utf-8")

    def get_simulator() -> MITREScenarioSimulator:
        nonlocal simulator
        with simulator_lock:
            if simulator is None:
                print("Загрузка генератора и моделей обнаружения...", flush=True)
                simulator = MITREScenarioSimulator(
                    resolve_resource("data/processed/r5.2_sequences/validation.npz"),
                    resolve_resource("data/processed/r5.2_sequences/manifest.json"),
                    resolve_resource("artifacts/r5.2_normal_role_conditional_gan"),
                    resolve_resource("artifacts/r5.2_mitre_augmented_seq_acgan"),
                    resolve_resource("artifacts/r5.2_gpu_detector"),
                    resolve_resource("data/raw/cert/r5.2/r5.2/LDAP"),
                    profiles_path,
                )
        return simulator

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web_dir), **kwargs)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/dashboard":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/api/session":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(session_body)))
                self.end_headers()
                self.wfile.write(session_body)
                return
            if path == "/api/scenarios":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(catalogue)))
                self.end_headers()
                self.wfile.write(catalogue)
                return
            super().do_GET()

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/generate":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 16_384:
                    raise ValueError("Слишком большой запрос")
                request = json.loads(self.rfile.read(length) or b"{}")
                result = get_simulator().generate(
                    str(request.get("scenario_id", "T1052.001")),
                    float(request.get("intensity", 1.0)),
                    int(request["seed"]) if request.get("seed") is not None else None,
                    str(request["user"]) if request.get("user") else None,
                    request.get("custom_profile"),
                )
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
            except (ValueError, KeyError, TypeError) as error:
                body = json.dumps({"ошибка": str(error)}, ensure_ascii=False).encode("utf-8")
                self.send_response(400)
            except (OSError, RuntimeError) as error:
                body = json.dumps(
                    {"ошибка": f"Ошибка генерации: {error}"}, ensure_ascii=False
                ).encode("utf-8")
                self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer((host, port), Handler)
    print("=" * 68)
    print("  Программа обнаружения и симуляции угроз")
    print(f"  Сервер запущен: http://{host}:{port}")
    print("  Для завершения работы нажмите Ctrl+C")
    print("=" * 68)
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    import sys
    if len(sys.argv) == 1:
        serve(
            resolve_resource("artifacts/dashboard/data.json"),
            resolve_resource("src/ueba_seq_acgan/web"),
            "127.0.0.1",
            8765,
            open_browser=True,
        )
        return

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument(
        "--sequences", type=Path, default=Path("data/processed/r5.2_sequences/test.npz")
    )
    build.add_argument("--model-dir", type=Path, default=Path("artifacts/r5.2_gpu_detector"))
    build.add_argument(
        "--manifest", type=Path, default=Path("data/processed/r5.2_sequences/manifest.json")
    )
    build.add_argument(
        "--comparison",
        type=Path,
        default=Path("artifacts/r5.2_model_selection/validation_audit.json"),
    )
    build.add_argument("--output", type=Path, default=Path("artifacts/dashboard/data.json"))
    build.add_argument("--limit", type=int, default=100)
    run = subparsers.add_parser("serve")
    run.add_argument("--data", type=Path, default=Path("artifacts/dashboard/data.json"))
    run.add_argument("--web-dir", type=Path, default=Path("src/ueba_seq_acgan/web"))
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8765)
    run.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        payload = build_payload(
            args.sequences, args.model_dir, args.manifest, args.comparison, args.limit
        )
        write_payload(payload, args.output)
        print(json.dumps(payload["summary"], indent=2))
        print(f"Saved {args.output}")
    else:
        serve(args.data, args.web_dir, args.host, args.port, args.open_browser)


if __name__ == "__main__":
    main()

