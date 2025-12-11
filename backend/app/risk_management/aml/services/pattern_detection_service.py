"""
Pattern Detection Service

Advanced pattern detection for AML suspicious activity identification.
"""

from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from collections import defaultdict

from ..models.transaction_pattern_models import (
    PatternType, PatternSeverity, PatternStatus, TransactionNode, TransactionEdge,
    TransactionFlow, StructuringPattern, LayeringPattern, VelocityPattern,
    GeographicPattern, DetectedPattern, PatternRule, PatternAnalysisRequest,
    PatternAnalysisResult, TransactionProfileDeviation
)


class PatternDetectionService:
    """Service for detecting suspicious transaction patterns"""

    def __init__(self):
        self._detected_patterns: Dict[UUID, DetectedPattern] = {}
        self._transaction_flows: Dict[UUID, TransactionFlow] = {}

    async def detect_structuring(
        self, customer_id: str, transactions: List[Dict[str, Any]], reporting_threshold: float = 10000.0
    ) -> Optional[StructuringPattern]:
        """Detect potential structuring (smurfing) patterns"""
        if not transactions:
            return None

        # Filter cash transactions
        cash_transactions = [
            t for t in transactions
            if t.get("type") == "cash" and t.get("amount", 0) > 0
        ]

        if len(cash_transactions) < 2:
            return None

        # Check for amounts just below threshold
        below_threshold = [
            t for t in cash_transactions
            if t.get("amount", 0) >= reporting_threshold * 0.7
            and t.get("amount", 0) < reporting_threshold
        ]

        if len(below_threshold) < 2:
            return None

        # Analyze timing
        amounts = [t.get("amount", 0) for t in below_threshold]
        total_amount = sum(amounts)

        # Calculate confidence based on patterns
        confidence = 0.0

        # Many transactions just below threshold
        if len(below_threshold) >= 3:
            confidence += 0.3

        # Total exceeds threshold significantly
        if total_amount > reporting_threshold * 1.5:
            confidence += 0.3

        # Amounts are suspiciously similar
        avg_amount = total_amount / len(below_threshold)
        variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)
        if variance < 1000000:  # Low variance indicates similar amounts
            confidence += 0.2

        # Round numbers
        round_count = sum(1 for a in amounts if a % 100 == 0)
        if round_count / len(amounts) > 0.5:
            confidence += 0.2

        if confidence < 0.5:
            return None

        return StructuringPattern(
            customer_id=customer_id,
            transactions=[t.get("transaction_id", "") for t in below_threshold],
            total_amount=total_amount,
            individual_amounts=amounts,
            reporting_threshold=reporting_threshold,
            amount_below_threshold_count=len(below_threshold),
            amount_below_threshold_total=total_amount,
            average_amount=avg_amount,
            max_amount=max(amounts),
            time_window_days=1,
            confidence_score=min(confidence, 1.0),
            indicators=[
                "multiple_below_threshold",
                "total_exceeds_threshold" if total_amount > reporting_threshold else None,
                "similar_amounts" if variance < 1000000 else None,
                "round_numbers" if round_count / len(amounts) > 0.5 else None
            ]
        )

    async def detect_layering(
        self, transactions: List[Dict[str, Any]], max_hops: int = 10
    ) -> List[LayeringPattern]:
        """Detect potential layering patterns"""
        patterns = []

        # Build transaction graph
        graph = defaultdict(list)
        for t in transactions:
            source = t.get("source_account", "")
            target = t.get("target_account", "")
            if source and target:
                graph[source].append({
                    "target": target,
                    "amount": t.get("amount", 0),
                    "timestamp": t.get("timestamp"),
                    "transaction_id": t.get("transaction_id", "")
                })

        # Find chains
        visited: Set[str] = set()

        def find_chains(start: str, path: List[str], transactions_in_path: List[str], depth: int):
            if depth > max_hops:
                return

            for edge in graph[start]:
                target = edge["target"]
                if target in visited:
                    continue

                visited.add(target)
                new_path = path + [target]
                new_transactions = transactions_in_path + [edge["transaction_id"]]

                if len(new_path) >= 3:
                    # Potential layering detected
                    pattern = LayeringPattern(
                        origin_entity=path[0],
                        intermediate_entities=new_path[1:-1],
                        final_entity=new_path[-1],
                        transaction_chain=new_transactions,
                        layer_count=len(new_path) - 1,
                        confidence_score=0.6 + (len(new_path) - 3) * 0.1
                    )
                    patterns.append(pattern)

                find_chains(target, new_path, new_transactions, depth + 1)
                visited.remove(target)

        for start_node in graph.keys():
            visited.add(start_node)
            find_chains(start_node, [start_node], [], 0)
            visited.remove(start_node)

        return patterns

    async def detect_velocity_anomaly(
        self, customer_id: str, current_transactions: List[Dict[str, Any]],
        historical_stats: Dict[str, Any]
    ) -> Optional[VelocityPattern]:
        """Detect velocity anomalies"""
        if not current_transactions or not historical_stats:
            return None

        current_count = len(current_transactions)
        current_amount = sum(t.get("amount", 0) for t in current_transactions)

        baseline_count = historical_stats.get("avg_transaction_count", 0)
        baseline_amount = historical_stats.get("avg_transaction_amount", 0)
        std_count = historical_stats.get("std_transaction_count", 1)
        std_amount = historical_stats.get("std_transaction_amount", 1)

        # Calculate z-scores
        count_z = (current_count - baseline_count) / std_count if std_count > 0 else 0
        amount_z = (current_amount - baseline_amount) / std_amount if std_amount > 0 else 0

        # Significant deviation threshold
        if abs(count_z) < 2 and abs(amount_z) < 2:
            return None

        confidence = min((abs(count_z) + abs(amount_z)) / 10, 1.0)

        return VelocityPattern(
            customer_id=customer_id,
            account_id=current_transactions[0].get("account_id", "") if current_transactions else "",
            current_period_start=datetime.utcnow() - timedelta(days=7),
            current_period_end=datetime.utcnow(),
            current_transaction_count=current_count,
            current_transaction_amount=current_amount,
            baseline_avg_count=baseline_count,
            baseline_avg_amount=baseline_amount,
            baseline_std_count=std_count,
            baseline_std_amount=std_amount,
            count_deviation=current_count - baseline_count,
            amount_deviation=current_amount - baseline_amount,
            count_z_score=count_z,
            amount_z_score=amount_z,
            confidence_score=confidence
        )

    async def detect_geographic_anomaly(
        self, customer_id: str, transactions: List[Dict[str, Any]],
        expected_countries: List[str], high_risk_countries: List[str]
    ) -> Optional[GeographicPattern]:
        """Detect geographic anomalies"""
        if not transactions:
            return None

        transaction_countries = [t.get("country", "") for t in transactions if t.get("country")]
        actual_countries = list(set(transaction_countries))

        # Find unusual countries
        unusual = [c for c in actual_countries if c not in expected_countries]
        high_risk = [c for c in actual_countries if c in high_risk_countries]
        new_countries = [c for c in actual_countries if c not in expected_countries]

        if not unusual and not high_risk:
            return None

        # Calculate high-risk exposure
        high_risk_transactions = [t for t in transactions if t.get("country") in high_risk_countries]
        high_risk_amount = sum(t.get("amount", 0) for t in high_risk_transactions)
        total_amount = sum(t.get("amount", 0) for t in transactions)
        high_risk_percentage = (high_risk_amount / total_amount * 100) if total_amount > 0 else 0

        confidence = 0.5
        if high_risk:
            confidence += 0.3
        if len(unusual) > 2:
            confidence += 0.2

        return GeographicPattern(
            customer_id=customer_id,
            transaction_ids=[t.get("transaction_id", "") for t in transactions],
            unusual_countries=unusual,
            high_risk_countries=high_risk,
            new_countries=new_countries,
            expected_countries=expected_countries,
            actual_countries=actual_countries,
            high_risk_amount=high_risk_amount,
            high_risk_percentage=high_risk_percentage,
            confidence_score=min(confidence, 1.0)
        )

    async def detect_rapid_movement(
        self, account_id: str, transactions: List[Dict[str, Any]], time_threshold_hours: int = 24
    ) -> List[DetectedPattern]:
        """Detect rapid movement of funds (in and out quickly)"""
        patterns = []

        # Sort by timestamp
        sorted_txns = sorted(
            [t for t in transactions if t.get("timestamp")],
            key=lambda x: x["timestamp"]
        )

        credits = [t for t in sorted_txns if t.get("direction") == "credit"]
        debits = [t for t in sorted_txns if t.get("direction") == "debit"]

        for credit in credits:
            credit_time = credit.get("timestamp")
            credit_amount = credit.get("amount", 0)

            # Look for debits shortly after
            for debit in debits:
                debit_time = debit.get("timestamp")
                debit_amount = debit.get("amount", 0)

                if debit_time <= credit_time:
                    continue

                time_diff = (debit_time - credit_time).total_seconds() / 3600

                if time_diff > time_threshold_hours:
                    break

                # Check if amounts are similar
                amount_ratio = debit_amount / credit_amount if credit_amount > 0 else 0

                if amount_ratio >= 0.8:
                    pattern = DetectedPattern(
                        pattern_type=PatternType.RAPID_MOVEMENT,
                        severity=PatternSeverity.HIGH,
                        primary_entity_id=account_id,
                        primary_entity_type="account",
                        primary_entity_name=account_id,
                        transaction_ids=[credit.get("transaction_id", ""), debit.get("transaction_id", "")],
                        transaction_count=2,
                        total_amount=credit_amount + debit_amount,
                        detection_rule_id="rapid_movement_001",
                        detection_rule_name="Rapid Fund Movement",
                        confidence_score=0.7 + (0.3 * amount_ratio),
                        pattern_details={
                            "credit_amount": credit_amount,
                            "debit_amount": debit_amount,
                            "time_diff_hours": time_diff,
                            "amount_ratio": amount_ratio
                        }
                    )
                    patterns.append(pattern)

        return patterns

    async def detect_round_tripping(
        self, transactions: List[Dict[str, Any]]
    ) -> List[DetectedPattern]:
        """Detect round-tripping (funds returning to origin)"""
        patterns = []

        # Build transaction map
        account_flows = defaultdict(lambda: {"out": [], "in": []})

        for t in transactions:
            source = t.get("source_account", "")
            target = t.get("target_account", "")
            if source:
                account_flows[source]["out"].append(t)
            if target:
                account_flows[target]["in"].append(t)

        # Look for funds returning
        for account, flows in account_flows.items():
            out_counterparties = {t.get("target_account"): t for t in flows["out"]}
            in_counterparties = {t.get("source_account"): t for t in flows["in"]}

            # Check for circular flow
            for counterparty in out_counterparties:
                if counterparty in in_counterparties:
                    out_txn = out_counterparties[counterparty]
                    in_txn = in_counterparties[counterparty]

                    out_amount = out_txn.get("amount", 0)
                    in_amount = in_txn.get("amount", 0)

                    # Similar amounts returning
                    if in_amount >= out_amount * 0.8:
                        pattern = DetectedPattern(
                            pattern_type=PatternType.ROUND_TRIPPING,
                            severity=PatternSeverity.HIGH,
                            primary_entity_id=account,
                            primary_entity_type="account",
                            primary_entity_name=account,
                            transaction_ids=[
                                out_txn.get("transaction_id", ""),
                                in_txn.get("transaction_id", "")
                            ],
                            transaction_count=2,
                            total_amount=out_amount + in_amount,
                            detection_rule_id="round_trip_001",
                            detection_rule_name="Round Tripping Detection",
                            confidence_score=0.8,
                            pattern_details={
                                "outgoing_amount": out_amount,
                                "incoming_amount": in_amount,
                                "counterparty": counterparty
                            }
                        )
                        patterns.append(pattern)

        return patterns

    async def analyze_transaction_flow(
        self, transactions: List[Dict[str, Any]], root_entity: str
    ) -> TransactionFlow:
        """Build and analyze transaction flow"""
        flow = TransactionFlow(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )

        nodes: Dict[str, TransactionNode] = {}
        edges: List[TransactionEdge] = []

        for t in transactions:
            source = t.get("source_account", "")
            target = t.get("target_account", "")

            # Add nodes
            if source and source not in nodes:
                nodes[source] = TransactionNode(
                    node_id=source,
                    node_type="account",
                    node_name=source,
                    account_id=source,
                    is_internal=t.get("source_internal", True)
                )

            if target and target not in nodes:
                nodes[target] = TransactionNode(
                    node_id=target,
                    node_type="account",
                    node_name=target,
                    account_id=target,
                    is_internal=t.get("target_internal", True)
                )

            # Add edge
            if source and target:
                edge = TransactionEdge(
                    source_node_id=source,
                    target_node_id=target,
                    transaction_id=t.get("transaction_id", ""),
                    amount=t.get("amount", 0),
                    currency=t.get("currency", "USD"),
                    transaction_date=t.get("timestamp", datetime.utcnow()),
                    transaction_type=t.get("type", "transfer")
                )
                edges.append(edge)

        flow.nodes = list(nodes.values())
        flow.edges = edges
        flow.total_amount = sum(e.amount for e in edges)
        flow.transaction_count = len(edges)
        flow.unique_entities = len(nodes)

        # Get countries
        countries = set()
        for node in nodes.values():
            if node.country:
                countries.add(node.country)
        flow.countries_involved = list(countries)

        self._transaction_flows[flow.flow_id] = flow
        return flow

    async def run_comprehensive_analysis(
        self, request: PatternAnalysisRequest
    ) -> PatternAnalysisResult:
        """Run comprehensive pattern analysis"""
        result = PatternAnalysisResult(
            request_id=request.request_id
        )

        # This would normally process real transaction data
        # For now, return empty result
        result.analysis_date = datetime.utcnow()
        result.processing_time_seconds = 0.5

        return result


# Global service instance
pattern_detection_service = PatternDetectionService()
