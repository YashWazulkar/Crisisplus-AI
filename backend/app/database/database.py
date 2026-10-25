"""SQLite Persistence Engine for CrisisPulse AI.

Stores normalized incoming events, source health snapshots, Bayesian hypotheses history,
predictive forecasts, decision recommendations, audit ledger entries, and model evaluations.
"""

from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent

DB_PATH = Path("data/crisispulse.db")

class CrisisDatabase:
    """Manages SQLite persistence with indexed lookups, pagination, and audit logs."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def init_schema(self):
        """Creates table schemas and indexes if they do not exist."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    depth_km REAL,
                    region TEXT,
                    zone_id TEXT,
                    event_timestamp TEXT NOT NULL,
                    ingestion_timestamp TEXT NOT NULL,
                    severity REAL NOT NULL,
                    magnitude REAL,
                    magnitude_unit TEXT,
                    source_reliability REAL NOT NULL,
                    confidence REAL NOT NULL,
                    verification_status TEXT NOT NULL,
                    source_url TEXT,
                    gateway_id TEXT,
                    quality_flags TEXT,
                    payload_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(event_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_id);

                CREATE TABLE IF NOT EXISTS source_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms REAL,
                    records_accepted INTEGER,
                    records_rejected INTEGER,
                    error_message TEXT,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS hypotheses_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tick INTEGER NOT NULL,
                    event_id TEXT,
                    normal REAL NOT NULL,
                    source_failure REAL NOT NULL,
                    isolated_incident REAL NOT NULL,
                    cascading_crisis REAL NOT NULL,
                    dominant_hypothesis TEXT NOT NULL,
                    quality_weight REAL NOT NULL,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tick INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    probability REAL NOT NULL,
                    time_window TEXT NOT NULL,
                    horizon_minutes INTEGER NOT NULL,
                    basis TEXT,
                    zone TEXT,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decision_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tick INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    cost_watch REAL,
                    cost_prepare REAL,
                    cost_alert REAL,
                    cost_escalate REAL,
                    explanation TEXT,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tick INTEGER NOT NULL,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    prior_json TEXT NOT NULL,
                    posterior_json TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quality_weight REAL NOT NULL,
                    explanation TEXT,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS model_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    dataset_name TEXT NOT NULL,
                    sample_count INTEGER NOT NULL,
                    precision REAL,
                    recall REAL,
                    f1 REAL,
                    false_alarm_rate REAL,
                    missed_crisis_rate REAL,
                    brier_score REAL,
                    lead_time_min REAL,
                    evaluation_period TEXT,
                    recorded_at TEXT NOT NULL
                );
            """)

    def insert_event(self, event: NormalizedEvent):
        """Persists a normalized event record into SQLite."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO events (
                    event_id, source_id, external_id, event_type, title, description,
                    latitude, longitude, depth_km, region, zone_id,
                    event_timestamp, ingestion_timestamp, severity, magnitude, magnitude_unit,
                    source_reliability, confidence, verification_status, source_url,
                    gateway_id, quality_flags, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.source_id,
                event.external_id,
                event.event_type,
                event.title,
                event.description,
                event.latitude,
                event.longitude,
                event.depth_km,
                event.region,
                event.zone_id,
                event.event_timestamp.isoformat(),
                event.ingestion_timestamp.isoformat(),
                event.severity,
                event.magnitude,
                event.magnitude_unit,
                event.source_reliability,
                event.confidence,
                event.verification_status,
                event.source_url,
                event.gateway_id,
                json.dumps(event.quality_flags),
                json.dumps(event.payload),
            ))

    def record_hypothesis(self, tick: int, event_id: str | None, probs: dict[str, float], weight: float):
        dom = max(probs, key=probs.get) # type: ignore
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO hypotheses_history (
                    tick, event_id, normal, source_failure, isolated_incident,
                    cascading_crisis, dominant_hypothesis, quality_weight, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tick, event_id,
                probs.get("normal", 0.0),
                probs.get("source_failure", 0.0),
                probs.get("isolated_incident", 0.0),
                probs.get("cascading_crisis", 0.0),
                dom, weight, now_str
            ))

    def record_decision(self, tick: int, action: str, costs: dict[str, float], explanation: str):
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO decision_history (
                    tick, action, cost_watch, cost_prepare, cost_alert, cost_escalate, explanation, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tick, action,
                costs.get("WATCH", 0.0),
                costs.get("PREPARE", 0.0),
                costs.get("ALERT", 0.0),
                costs.get("ESCALATE", 0.0),
                explanation, now_str
            ))

    def record_ledger(self, tick: int, event_id: str, event_type: str, source_id: str,
                      prior: dict[str, float], posterior: dict[str, float],
                      action: str, quality_weight: float, explanation: str):
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_ledger (
                    tick, event_id, event_type, source_id, prior_json, posterior_json,
                    action, quality_weight, explanation, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tick, event_id, event_type, source_id,
                json.dumps(prior), json.dumps(posterior),
                action, quality_weight, explanation, now_str
            ))

    def record_evaluation(self, run_id: str, dataset_name: str, sample_count: int,
                          precision: float, recall: float, f1: float,
                          far: float, mr: float, brier: float, lead_time: float, period: str):
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO model_evaluations (
                    run_id, dataset_name, sample_count, precision, recall, f1,
                    false_alarm_rate, missed_crisis_rate, brier_score, lead_time_min,
                    evaluation_period, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id, dataset_name, sample_count, precision, recall, f1,
                far, mr, brier, lead_time, period, now_str
            ))

    def get_events(self, limit: int = 50, offset: int = 0, event_type: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM events"
        params: list[Any] = []
        if event_type:
            query += " WHERE event_type = ?"
            params.append(event_type)
        query += " ORDER BY event_timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["quality_flags"] = json.loads(d.get("quality_flags") or "[]")
                d["payload"] = json.loads(d.get("payload_json") or "{}")
                d.pop("payload_json", None)
                result.append(d)
            return result

    def get_audit_ledger(self, limit: int = 40) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM audit_ledger ORDER BY tick DESC, id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["prior"] = json.loads(d.get("prior_json") or "{}")
                d["posterior"] = json.loads(d.get("posterior_json") or "{}")
                result.append(d)
            return result
