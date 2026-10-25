"""CrisisPulse AI Central Intelligence and Inference Engine: Nagpur Operational Edition.

Orchestrates Bayesian belief updates, anomaly detection, predictive forecasting,
causal dependency analysis, risk-optimal action selection, online source trust learning,
base-rate drift adaptation, alert stability hysteresis, and SQLite persistence.
Enforces strict spatial relevance to Nagpur District and its 10 NMC Municipal Zones.
Integrates evidence-grounded xAI (Grok) reasoning.
"""

from __future__ import annotations
from collections import deque
from datetime import datetime, timezone
from typing import Any
from .schemas import Event
from .normalization.schema import NormalizedEvent
from .inference.bayesian import (
    BayesianInferenceEngine,
    STANDARD_HYPOTHESES,
    HYPOTHESES,
    LABELS,
)
from .inference.base_rate import BaseRateAdapter
from .inference.anomaly_detector import AnomalyDetector
from .causal_analysis.graph import CausalDependencyGraph
from .forecasting.forecaster import PredictiveForecaster
from .decision_engine.decider import DecisionEngine, RESPONSE_COSTS
from .database.database import CrisisDatabase
from .data_quality.scorer import DataQualityScorer
from .data_quality.source_health import SourceReliabilityTracker
from .data_quality.online_learning import OnlineTrustLearner
from .validation.validator import EventValidator
from .deduplication.deduplicator import EventDeduplicator
from .deduplication.retractions import EventRetractionManager
from .geography.spatial_filter import NagpurSpatialFilter
from .geography.nagpur_registry import (
    NAGPUR_CENTER_LAT,
    NAGPUR_CENTER_LON,
    NAGPUR_DISTRICT_NAME,
    NAGPUR_STATE,
    NMC_ZONES,
)
from .xai.client import XAIClient
from .xai.models import EvidencePacket, ObservationEvidence, XAIExplanationResponse


class InferenceEngine:
    """Integrated engine serving real-time decision support for Nagpur emergency intelligence."""

    def __init__(self):
        self.base_rate_adapter = BaseRateAdapter()
        self.bayesian = BayesianInferenceEngine(base_rate_adapter=self.base_rate_adapter)
        self.anomaly_detector = AnomalyDetector()
        self.causal_graph = CausalDependencyGraph()
        self.decision_engine = DecisionEngine()
        self.validator = EventValidator()
        self.deduplicator = EventDeduplicator()
        self.retraction_manager = EventRetractionManager()
        self.quality_scorer = DataQualityScorer()
        self.source_tracker = SourceReliabilityTracker()
        self.online_learner = OnlineTrustLearner(tracker=self.source_tracker)
        self.spatial_filter = NagpurSpatialFilter()
        self.xai_client = XAIClient()
        self.db = CrisisDatabase()

        # Operational State
        self.priors = self.bayesian.default_priors.copy()
        self.probabilities = self.bayesian.probabilities.copy()
        self.events: deque[dict[str, Any]] = deque(maxlen=250)
        self.ledger: deque[dict[str, Any]] = deque(maxlen=300)
        self.seen_ids: set[str] = set()
        self.previous_action = "WATCH"
        self.tick = 0
        self.active_anomalies: list[dict[str, Any]] = []
        self.last_assessment_timestamp: datetime = datetime.now(timezone.utc)

        # Zone-specific tracking
        self.zone_events: dict[str, list[dict[str, Any]]] = {z: [] for z in NMC_ZONES}
        self.active_zone_id: str = "zone-3-hanuman-nagar"
        self.latest_xai_explanation: XAIExplanationResponse | None = None

    @property
    def source_health(self) -> dict[str, dict[str, Any]]:
        """Backward-compatible source health dict."""
        return {s.source_id: s.to_dict() for s in self.source_tracker.sources.values()}

    def reset(self):
        self.base_rate_adapter.reset()
        self.bayesian.reset()
        self.anomaly_detector.reset()
        self.deduplicator.reset()
        self.retraction_manager.reset()
        self.source_tracker.reset()
        self.decision_engine.reset()
        self.priors = self.bayesian.default_priors.copy()
        self.probabilities = self.bayesian.probabilities.copy()
        self.events.clear()
        self.ledger.clear()
        self.seen_ids.clear()
        self.previous_action = "WATCH"
        self.tick = 0
        self.active_anomalies.clear()
        self.zone_events = {z: [] for z in NMC_ZONES}
        self.active_zone_id = "zone-3-hanuman-nagar"
        self.latest_xai_explanation = None
        self.last_assessment_timestamp = datetime.now(timezone.utc)

    def tick_minute(self) -> dict[str, Any]:
        """
        Executes a periodic 1-minute system assessment tick even when no new events arrive.
        Updates data freshness decay, checks for stale sensors, re-evaluates risk posture,
        and records the assessment timestamp.
        """
        self.tick += 1
        now_utc = datetime.now(timezone.utc)
        self.last_assessment_timestamp = now_utc

        # 1. Flag stale sensor telemetry
        stale_ids = self.source_tracker.mark_stale_sources(now_utc, timeout_seconds=300.0)

        # 2. Get active non-retracted chronological events
        recent_norm_events = self.retraction_manager.get_valid_chronological_events(limit=30)

        # 3. Re-evaluate decision and alert stability
        decision_result = self.decision_engine.evaluate(
            probabilities=self.probabilities,
            recent_events=recent_norm_events,
            source_health_map=self.source_health,
            now=now_utc,
        )
        action = decision_result["action"]
        expected_costs = decision_result["expected_costs"]
        forecasts = self.forecast(self.active_zone_id)

        # 4. Generate periodic explanation if action changed or periodic audit entry
        explanation_summary = decision_result.get("reasons", "Routine 1-minute operational assessment; baseline equilibrium maintained.")

        ledger_entry = {
            "tick": self.tick,
            "event_id": f"periodic-tick-{self.tick}",
            "event_type": "periodic_assessment",
            "source_id": "engine-scheduler",
            "zone_id": self.active_zone_id,
            "zone_name": NMC_ZONES.get(self.active_zone_id, {}).get("name", "Nagpur Central"),
            "prior": self.probabilities.copy(),
            "posterior": self.probabilities.copy(),
            "action": action,
            "expected_costs": expected_costs,
            "quality_weight": 1.0,
            "explanation": explanation_summary,
            "timestamp": now_utc.isoformat(),
        }
        self.ledger.appendleft(ledger_entry)
        self.previous_action = action

        return {
            "tick": self.tick,
            "action": action,
            "probabilities": self.probabilities.copy(),
            "expected_costs": expected_costs,
            "forecasts": forecasts,
            "stale_sources_flagged": stale_ids,
            "last_assessment_timestamp": now_utc.isoformat(),
        }

    def process(self, raw_event: Event | NormalizedEvent) -> dict[str, Any]:
        """
        Processes an incoming event through the complete pipeline:
          spatial filtering -> retractions/corrections -> deduplication -> source reliability ->
          quality scoring -> Bayesian update -> anomaly detection -> forecasting ->
          decision engine with hysteresis -> xAI explanation -> persistence.
        """
        # Convert legacy Event to NormalizedEvent if necessary
        if isinstance(raw_event, Event):
            norm_event = raw_event.to_normalized()
        else:
            norm_event = raw_event

        # 1. Spatial Relevance Filter for Nagpur
        spatial_meta = self.spatial_filter.classify_event(
            norm_event.latitude,
            norm_event.longitude,
            region_str=norm_event.region,
            event_type=norm_event.event_type,
            magnitude=norm_event.magnitude,
            source_is_district_level=(norm_event.geographic_precision == "district_level"),
        )

        if not spatial_meta.is_relevant:
            return {
                "accepted": False,
                "reason": spatial_meta.exclusion_reason or "out_of_nagpur_monitoring_region",
                "event": norm_event.to_legacy_dict(),
            }

        # Enrich event with spatial attributes
        if spatial_meta.assigned_zone_id and not norm_event.assigned_zone_id:
            norm_event.assigned_zone_id = spatial_meta.assigned_zone_id
            norm_event.assigned_zone_name = spatial_meta.assigned_zone_name
            norm_event.zone_id = spatial_meta.assigned_zone_name or norm_event.zone_id
        norm_event.geographic_precision = spatial_meta.precision
        norm_event.admin_level = spatial_meta.admin_level
        norm_event.is_nagpur_relevant = True

        if norm_event.assigned_zone_id:
            self.active_zone_id = norm_event.assigned_zone_id

        # 2. Retraction & Correction Processing
        lifecycle_res = self.retraction_manager.process_incoming_event(norm_event)
        if lifecycle_res["action"] == "duplicate_retraction":
            return {
                "accepted": False,
                "reason": "duplicate_retraction_already_processed",
                "event": norm_event.to_legacy_dict(),
            }

        # 3. Deduplication check
        if norm_event.event_id in self.seen_ids and not lifecycle_res["is_correction"]:
            return {
                "accepted": False,
                "reason": "duplicate_event_id",
                "event": norm_event.to_legacy_dict(),
            }

        dedup_res = self.deduplicator.check_and_register(norm_event)
        if dedup_res.is_duplicate and not lifecycle_res["is_correction"] and not lifecycle_res["is_retraction"]:
            return {
                "accepted": False,
                "reason": dedup_res.reason or "duplicate_event",
                "event": norm_event.to_legacy_dict(),
            }

        self.seen_ids.add(norm_event.event_id)
        self.tick += 1
        now_utc = datetime.now(timezone.utc)
        self.last_assessment_timestamp = now_utc

        # 4. Update Source Reliability Tracker (Gateway groupings, uncertainty, repeated values)
        src_status = self.source_tracker.register_event(norm_event)
        source_factor = 1.0 if src_status["status"] == "healthy" else 0.45

        # 5. Quality scoring (freshness decay, flags, gateway correlation)
        quality_weight = self.quality_scorer.score_event(norm_event, source_factor)

        # 6. Environmental Drift Monitoring
        if norm_event.event_type == "rainfall" and norm_event.magnitude is not None:
            self.base_rate_adapter.update_environmental_drift(norm_event.magnitude)

        # 7. Bayesian Belief Update
        prior, posterior = self.bayesian.update(norm_event, quality_weight)
        self.probabilities = posterior

        # 8. Anomaly Detection
        anomalies = self.anomaly_detector.evaluate(norm_event)
        if anomalies:
            self.active_anomalies = [a.to_dict() for a in anomalies] + self.active_anomalies[:10]

        # 9. Event Recording in Local History
        entry = norm_event.to_legacy_dict()
        entry["accepted"] = True
        self.events.appendleft(entry)

        if norm_event.assigned_zone_id in self.zone_events:
            self.zone_events[norm_event.assigned_zone_id].insert(0, entry)
            self.zone_events[norm_event.assigned_zone_id] = self.zone_events[norm_event.assigned_zone_id][:30]

        # 10. Decision Engine with Alert Stability & Hysteresis
        recent_norm_events = self.retraction_manager.get_valid_chronological_events(limit=30)
        decision_result = self.decision_engine.evaluate(
            probabilities=self.probabilities,
            recent_events=recent_norm_events,
            source_health_map=self.source_health,
            now=now_utc,
        )
        action = decision_result["action"]
        expected_costs = decision_result["expected_costs"]
        forecasts = self.forecast(self.active_zone_id)

        # 11. Assembling Analytical EvidencePacket and xAI Explanation
        target_name = norm_event.assigned_zone_name or "Nagpur District"
        obs_evidence = []
        for e in list(self.events)[:6]:
            e_ts = datetime.fromisoformat(e["event_timestamp"])
            obs_evidence.append(
                ObservationEvidence(
                    source_id=e["source_id"],
                    event_type=e["event_type"],
                    title=e["title"],
                    magnitude=e.get("magnitude"),
                    magnitude_unit=e.get("magnitude_unit"),
                    severity=e.get("severity", 0.5),
                    confidence=e.get("confidence", 0.8),
                    data_provenance=e.get("data_provenance", "LIVE"),
                    geographic_precision=e.get("geographic_precision", "approximate"),
                    assigned_zone_name=e.get("assigned_zone_name"),
                    timestamp_utc=e["event_timestamp"],
                    age_seconds=max(0.0, (now_utc - e_ts).total_seconds()),
                    quality_flags=e.get("quality_flags", []),
                )
            )

        evidence_packet = EvidencePacket(
            packet_id=f"packet-{self.tick}-{norm_event.event_id}",
            timestamp_utc=now_utc.isoformat(),
            target_region="Nagpur District & NMC Urban Area",
            target_zone_id=norm_event.assigned_zone_id or self.active_zone_id,
            target_zone_name=target_name,
            authoritative_action=action,
            probabilities=self.probabilities.copy(),
            dominant_hypothesis=max(self.probabilities, key=self.probabilities.get),  # type: ignore
            expected_costs=expected_costs,
            supporting_observations=obs_evidence,
            contradictory_observations=decision_result.get("conflicting_evidence", []),
            missing_data_gaps=[
                "NMC stormwater IoT sensor gateway awaiting token",
                "Hospital emergency occupancy awaiting ABDM token",
            ],
            active_corroborated_sources_count=decision_result.get("effective_independent_sources", len({o.source_id for o in obs_evidence})),
            data_quality_factor=round(quality_weight, 3),
        )

        xai_explanation = self.xai_client.generate_deterministic_explanation(evidence_packet)
        self.latest_xai_explanation = xai_explanation

        # 12. Audit Ledger
        ledger_entry = {
            "tick": self.tick,
            "event_id": norm_event.event_id,
            "event_type": norm_event.event_type,
            "source_id": norm_event.source_id,
            "zone_id": norm_event.assigned_zone_id,
            "zone_name": target_name,
            "prior": prior,
            "posterior": posterior.copy(),
            "action": action,
            "expected_costs": expected_costs,
            "quality_weight": round(quality_weight, 3),
            "explanation": xai_explanation.summary,
            "xai_explanation": xai_explanation.model_dump(),
            "timestamp": norm_event.ingestion_timestamp.isoformat(),
        }
        self.ledger.appendleft(ledger_entry)
        self.previous_action = action

        # 13. Persist to SQLite
        try:
            self.db.insert_event(norm_event)
            self.db.record_hypothesis(self.tick, norm_event.event_id, self.probabilities, quality_weight)
            self.db.record_decision(self.tick, action, expected_costs, xai_explanation.summary)
            self.db.record_ledger(
                self.tick, norm_event.event_id, norm_event.event_type, norm_event.source_id,
                prior, posterior, action, quality_weight, xai_explanation.summary
            )
        except Exception:
            pass

        return {
            "accepted": True,
            "event": entry,
            "prior": prior,
            "probabilities": self.probabilities.copy(),
            "action": action,
            "expected_costs": expected_costs,
            "forecasts": forecasts,
            "explanation": xai_explanation.summary,
            "xai_explanation": xai_explanation.model_dump(),
            "quality_weight": round(quality_weight, 3),
            "anomalies": [a.to_dict() for a in anomalies],
            "decision_metadata": decision_result,
            "lifecycle_action": lifecycle_res["action"],
            "effective_independent_sources": decision_result.get("effective_independent_sources", 1),
        }

    def choose_action(self):
        """Backward-compatible action selection."""
        decision = self.decision_engine.evaluate(self.probabilities, [])
        return decision["action"], decision["expected_costs"]

    def forecast(self, zone_id: str | None = None):
        """Generates multi-horizon forecasts conditioned on selected Nagpur zone."""
        zid = zone_id or self.active_zone_id
        zname = NMC_ZONES.get(zid, {}).get("name", "Nagpur Central")
        norm_events = self.retraction_manager.get_valid_chronological_events(limit=20)
        return PredictiveForecaster.generate_forecasts(self.probabilities, norm_events, zid, zname)

    def get_region_assessment(self, zone_id: str) -> dict[str, Any]:
        """Returns deep subregion intelligence for a selected Nagpur zone."""
        zone_meta = NMC_ZONES.get(zone_id)
        if not zone_meta:
            zone_id = "zone-3-hanuman-nagar"
            zone_meta = NMC_ZONES[zone_id]

        zone_events = self.zone_events.get(zone_id, [])
        forecasts = self.forecast(zone_id)

        target_name = zone_meta["name"]
        action, costs = self.choose_action()

        obs_evidence = []
        for e in zone_events[:5]:
            obs_evidence.append(
                ObservationEvidence(
                    source_id=e["source_id"],
                    event_type=e["event_type"],
                    title=e["title"],
                    magnitude=e.get("magnitude"),
                    magnitude_unit=e.get("magnitude_unit"),
                    severity=e.get("severity", 0.5),
                    confidence=e.get("confidence", 0.8),
                    data_provenance=e.get("data_provenance", "LIVE"),
                    geographic_precision=e.get("geographic_precision", "zone_level"),
                    assigned_zone_name=target_name,
                    timestamp_utc=e["event_timestamp"],
                    age_seconds=120.0,
                )
            )

        packet = EvidencePacket(
            packet_id=f"zone-packet-{zone_id}-{self.tick}",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            target_region="Nagpur Municipal Corporation",
            target_zone_id=zone_id,
            target_zone_name=target_name,
            authoritative_action=action,
            probabilities=self.probabilities.copy(),
            dominant_hypothesis=max(self.probabilities, key=self.probabilities.get),  # type: ignore
            expected_costs=costs,
            supporting_observations=obs_evidence,
            missing_data_gaps=["Local storm grate sensors awaiting deployment"],
            active_corroborated_sources_count=len({o.source_id for o in obs_evidence}),
            data_quality_factor=0.85,
        )

        zone_explanation = self.xai_client.generate_deterministic_explanation(packet)

        return {
            "zone_id": zone_id,
            "name": zone_meta["name"],
            "marathi_name": zone_meta["marathi_name"],
            "centroid": zone_meta["centroid"],
            "localities": zone_meta["localities"],
            "critical_infrastructure": zone_meta["critical_infrastructure"],
            "flood_vulnerability": zone_meta["known_flood_vulnerability"],
            "action": action,
            "probabilities": self.probabilities.copy(),
            "expected_costs": costs,
            "events_count": len(zone_events),
            "events": zone_events[:15],
            "forecasts": forecasts,
            "xai_explanation": zone_explanation.model_dump(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def snapshot(self) -> dict[str, Any]:
        """Provides full operational state for live dashboards and clients."""
        action, costs = self.choose_action()
        decision = self.decision_engine.evaluate(self.probabilities, [])

        recent_norm_events = self.retraction_manager.get_valid_chronological_events(limit=30)
        causal_data = self.causal_graph.evaluate_active_pathways(recent_norm_events)

        verified_count = sum(1 for e in self.events if e.get("verification_status") in ("confirmed", "official"))
        unverified_count = sum(1 for e in self.events if e.get("verification_status") in ("unverified", "preliminary"))

        zone_summaries = {}
        for zid, zmeta in NMC_ZONES.items():
            ze_count = len(self.zone_events.get(zid, []))
            zone_summaries[zid] = {
                "zone_id": zid,
                "name": zmeta["name"],
                "marathi_name": zmeta["marathi_name"],
                "centroid": zmeta["centroid"],
                "event_count": ze_count,
                "action": action if ze_count > 0 else "WATCH",
            }

        most_affected_zone = max(
            NMC_ZONES.keys(),
            key=lambda zid: len(self.zone_events.get(zid, []))
        )
        most_affected_name = NMC_ZONES[most_affected_zone]["name"]

        if not self.latest_xai_explanation:
            fallback_packet = EvidencePacket(
                packet_id=f"snap-packet-{self.tick}",
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                target_region="Nagpur District & NMC Urban Area",
                target_zone_id=self.active_zone_id,
                target_zone_name=most_affected_name,
                authoritative_action=action,
                probabilities=self.probabilities.copy(),
                dominant_hypothesis=max(self.probabilities, key=self.probabilities.get),  # type: ignore
                expected_costs=costs,
                supporting_observations=[],
                active_corroborated_sources_count=len(self.source_health),
                data_quality_factor=0.88,
            )
            self.latest_xai_explanation = self.xai_client.generate_deterministic_explanation(fallback_packet)

        # Formulate canonical 4 hypotheses output
        canonical_hypotheses = [
            {"key": h, "label": LABELS[h], "probability": round(self.probabilities.get(h, 0.0), 4)}
            for h in STANDARD_HYPOTHESES
        ]

        return {
            "monitored_region": {
                "name": f"{NAGPUR_DISTRICT_NAME}, {NAGPUR_STATE}, India",
                "center": [NAGPUR_CENTER_LAT, NAGPUR_CENTER_LON],
                "district_code": "505",
                "urban_authority": "Nagpur Municipal Corporation (NMC)",
            },
            "hypotheses": canonical_hypotheses,
            "standard_hypotheses": canonical_hypotheses,
            "probabilities": self.probabilities.copy(),
            "action": action,
            "expected_costs": costs,
            "decision": decision,
            "risk_overview": {
                "dominant_hazard": LABELS.get(max(self.probabilities, key=self.probabilities.get), "Baseline"),  # type: ignore
                "most_affected_area": most_affected_name,
                "estimated_probability": round(max(self.probabilities.values()), 3),
                "severity_index": round(max([e.get("severity", 0.2) for e in list(self.events)[:10]] or [0.25]), 2),
                "data_quality_score": 0.88,
                "uncertainty_level": self.latest_xai_explanation.uncertainty_level,
                "response_recommendation": action,
                "evidence_summary": self.latest_xai_explanation.summary,
            },
            "xai_explanation": self.latest_xai_explanation.model_dump(),
            "event_counts": {
                "total_active": len(self.events),
                "verified": verified_count,
                "unverified": unverified_count,
                "retracted": len(self.retraction_manager.retracted_event_ids),
            },
            "subregions": zone_summaries,
            "events": list(self.events),
            "ledger": list(self.ledger),
            "sources": list(self.source_health.values()),
            "sources_summary": self.source_tracker.get_summary(),
            "forecasts": self.forecast(self.active_zone_id),
            "causal_graph": causal_data,
            "active_anomalies": self.active_anomalies[:5],
            "drift_status": self.base_rate_adapter.update_environmental_drift(0.0),
            "simulation_time": self.tick,
            "last_assessment_timestamp": self.last_assessment_timestamp.isoformat(),
            "model_status": "NAGPUR OPERATIONAL · PROBABILISTIC & XAI GROUNDED",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
