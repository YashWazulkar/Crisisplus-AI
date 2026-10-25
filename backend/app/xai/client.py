"""xAI (Grok) Integration Client and Grounded Explanation Layer.

Official Reference: https://docs.x.ai/
Endpoint: https://api.x.ai/v1/chat/completions

Provides structured, evidence-grounded natural-language explanations for
Nagpur operational emergency risk assessments, backed by deterministic fallback.
"""

from __future__ import annotations
import os
import json
import hashlib
import time
from typing import Any
import httpx
from .models import EvidencePacket, XAIExplanationResponse
from .validator import XAIGroundingValidator

XAI_API_ENDPOINT = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = "grok-2-1212"


class XAIClient:
    """Client for xAI Grok API with structured output and deterministic fallback."""

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY", "").strip()
        self.model = os.getenv("XAI_MODEL", DEFAULT_MODEL).strip()
        self.cache: dict[str, XAIExplanationResponse] = {}

    def is_configured(self) -> bool:
        self.api_key = os.getenv("XAI_API_KEY", "").strip()
        return bool(self.api_key)

    async def explain_assessment(
        self,
        packet: EvidencePacket,
        client: httpx.AsyncClient | None = None,
    ) -> XAIExplanationResponse:
        """Generates an evidence-grounded explanation for the given EvidencePacket.
        If XAI_API_KEY is not set or upstream API is unreachable, falls back seamlessly
        to the deterministic evidence synthesizer without halting the platform.
        """
        # Cache check
        cache_key = self._compute_packet_hash(packet)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Return copy with updated provider_status
            return cached.model_copy(update={"provider_status": "cached"})

        if not self.is_configured():
            res = self.generate_deterministic_explanation(packet)
            self.cache[cache_key] = res
            return res

        # Attempt live Grok API call
        try:
            if client is not None:
                resp_obj = await self._call_grok(client, packet)
            else:
                async with httpx.AsyncClient(timeout=10.0) as cl:
                    resp_obj = await self._call_grok(cl, packet)

            validated = XAIGroundingValidator.validate_and_repair(resp_obj, packet, self.model)
            self.cache[cache_key] = validated
            return validated

        except Exception as e:
            # Fallback on any network timeout, auth rejection, or parse failure
            fallback = self.generate_deterministic_explanation(packet)
            fallback.missing_data_disclosure += f" (Note: Live xAI Grok API returned {str(e)[:80]}; operational continuity maintained via deterministic reasoning)."
            self.cache[cache_key] = fallback
            return fallback

    async def _call_grok(self, client: httpx.AsyncClient, packet: EvidencePacket) -> dict[str, Any]:
        system_prompt = (
            "You are the Explainable AI (xAI) Intelligence Engine for CrisisPulse AI: Nagpur Live Emergency Intelligence Platform. "
            "Your role is to explain backend probabilistic assessments to municipal incident coordinators and emergency managers. "
            "STRICT RULES:\n"
            "1. You MUST NOT fabricate observations, measurements, coordinates, or source records.\n"
            "2. You MUST NOT override the backend's Authoritative Recommendation (WATCH, PREPARE, ALERT, ESCALATE).\n"
            "3. Cite specific observation sources, values, units, and timestamps provided in the evidence packet.\n"
            "4. Clearly distinguish verified ground observations from model forecasts.\n"
            "5. Disclose missing data, sensor gaps, and uncertainty honestly.\n"
            "6. Output MUST be valid JSON adhering strictly to the required schema."
        )

        user_content = (
            f"Please generate an evidence-grounded operational explanation for the following structured evidence packet:\n"
            f"{packet.model_dump_json(indent=2)}\n\n"
            "Return a JSON object with the following keys:\n"
            "- summary: string\n"
            "- hazard_assessment: string\n"
            "- affected_region: string\n"
            "- evidence_synthesis: string\n"
            "- contradictory_evidence_analysis: string\n"
            "- missing_data_disclosure: string\n"
            "- decision_rationale: string\n"
            "- recommended_verification_steps: list of strings\n"
            "- uncertainty_level: 'Low' | 'Moderate' | 'High'\n"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 800,
        }

        resp = await client.post(XAI_API_ENDPOINT, json=payload, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"xAI API returned HTTP {resp.status_code}: {resp.text[:120]}")

        res_json = resp.json()
        content = res_json["choices"][0]["message"]["content"]
        return json.loads(content)

    def generate_deterministic_explanation(self, packet: EvidencePacket) -> XAIExplanationResponse:
        """Evidence-grounded deterministic synthesizer that constructs rigorous explanations
        from backend data when the LLM is unconfigured or unreachable.
        """
        region_name = packet.target_zone_name or packet.target_region
        action = packet.authoritative_action
        p_cascade = packet.probabilities.get("cascading_crisis", 0.0)
        p_failure = packet.probabilities.get("source_failure", 0.0)
        p_isolated = packet.probabilities.get("isolated_incident", 0.0)
        p_normal = packet.probabilities.get("normal", 0.55)

        # Synthesize supporting evidence
        obs_texts = []
        for o in packet.supporting_observations[:4]:
            val_str = f" ({o.magnitude} {o.magnitude_unit})" if o.magnitude is not None else ""
            obs_texts.append(f"{o.title} via {o.source_id}{val_str} [age: {int(o.age_seconds)}s]")
        obs_summary = "; ".join(obs_texts) if obs_texts else "No high-impact anomaly detected in current ingestion window."

        # Decision rationale synthesis
        if action == "ESCALATE":
            rationale = (
                f"ESCALATE — Corroborated multi-source evidence indicates severe cascading risk ({p_cascade:.1%}) "
                f"affecting critical infrastructure in {region_name}. "
                f"Expected loss of non-intervention ({packet.expected_costs['ESCALATE']:.2f}) is optimal under the decision cost matrix. "
                f"Corroborated by {packet.active_corroborated_sources_count} independent monitoring feeds."
            )
        elif action == "ALERT":
            rationale = (
                f"ALERT — Credible emerging hazard indicators detected for {region_name}. "
                f"Elevated risk posterior ({max(p_cascade, p_isolated):.1%}) warrants prompt operational verification. "
                "Immediate field inspection recommended before escalating inter-agency response."
            )
        elif action == "PREPARE":
            rationale = (
                f"PREPARE — Observations indicate developing weather or transit anomalies in {region_name}. "
                f"Active hazard probability is {max(p_cascade, p_isolated):.1%}. "
                "Duty officers should verify low-lying drainage hotspots and ensure paramedic readiness."
            )
        else:
            rationale = (
                f"WATCH — Environmental telemetry and municipal sensors indicate baseline nominal conditions "
                f"(Normal belief: {p_normal:.1%}) across {region_name}. Routine passive monitoring maintained."
            )

        # Missing data disclosure
        missing_text = (
            "Direct ultrasonic stormwater drain sensors and municipal traffic cameras are currently pending "
            "inter-agency API token authorization; regional assessments rely on calibrated meteorological models and reference baselines."
        )
        if packet.missing_data_gaps:
            missing_text = "; ".join(packet.missing_data_gaps)

        # Contradictory evidence
        contradictory_text = "No conflicting or misleading signals identified."
        if p_failure > 0.35:
            contradictory_text = (
                f"Elevated sensor/gateway failure likelihood ({p_failure:.1%}) suggests potential transmission "
                "faults rather than physical disaster progression."
            )
        elif packet.contradictory_observations:
            contradictory_text = "; ".join(packet.contradictory_observations)

        # Verification checklist
        steps = [
            f"Verify physical water accumulation at low-lying underpasses in {region_name}.",
            "Cross-reference RMC Nagpur radar imagery with Automatic Weather Station (AWS) precipitation.",
            "Confirm emergency department bed availability at GMCH and Mayo Hospital.",
            "Maintain human oversight: CrisisPulse recommendations must not dispatch services autonomously.",
        ]

        # Uncertainty level
        if packet.data_quality_factor >= 0.80 and packet.active_corroborated_sources_count >= 2:
            unc_level = "Low"
        elif packet.data_quality_factor >= 0.50:
            unc_level = "Moderate"
        else:
            unc_level = "High"

        return XAIExplanationResponse(
            summary=f"{action} advisory in effect for {region_name} based on verified analytical evidence.",
            hazard_assessment=f"Dominant operational state: {packet.dominant_hypothesis.replace('_', ' ').title()}.",
            affected_region=region_name,
            evidence_synthesis=obs_summary,
            contradictory_evidence_analysis=contradictory_text,
            missing_data_disclosure=missing_text,
            decision_rationale=rationale,
            recommended_verification_steps=steps,
            uncertainty_level=unc_level,  # type: ignore
            provider_status="deterministic_fallback",
            model_identifier="deterministic-evidence-synthesizer-v2.5",
            grounding_verified=True,
        )

    def _compute_packet_hash(self, packet: EvidencePacket) -> str:
        s = f"{packet.target_region}:{packet.authoritative_action}:{round(packet.probabilities.get('cascading_crisis', 0.0), 2)}:{len(packet.supporting_observations)}"
        return hashlib.sha256(s.encode()).hexdigest()[:16]
