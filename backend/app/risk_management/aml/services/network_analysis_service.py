"""
Network Analysis Service

Handles network/link analysis for AML investigations.
"""

from typing import Optional, List, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from collections import defaultdict
import math

from ..models.network_analysis_models import (
    NodeType, EdgeType, NetworkRiskLevel, NetworkNode, NetworkEdge,
    NetworkCluster, NetworkPath, NetworkAnalysis, NetworkQuery,
    LinkAnalysisResult, CommunityDetectionResult, CircularFlowDetection,
    NetworkVisualization, NetworkStatistics
)


class NetworkAnalysisService:
    """Service for network and link analysis"""

    def __init__(self):
        self._analyses: Dict[UUID, NetworkAnalysis] = {}
        self._nodes_cache: Dict[str, NetworkNode] = {}
        self._edges_cache: Dict[UUID, NetworkEdge] = {}

    async def build_network(self, query: NetworkQuery) -> NetworkAnalysis:
        """Build a network from the given query parameters"""
        analysis = NetworkAnalysis(
            analysis_name=f"Network Analysis - {query.root_entity_id}",
            analysis_type=query.root_entity_type,
            root_entity_id=query.root_entity_id,
            root_entity_type=query.root_entity_type,
            depth=query.max_depth
        )

        start_time = datetime.utcnow()

        # Build network (in real implementation, would query actual data)
        nodes, edges = await self._expand_network(
            query.root_entity_id,
            query.root_entity_type,
            query.max_depth,
            query.max_nodes,
            query.node_types,
            query.edge_types
        )

        analysis.nodes = nodes
        analysis.edges = edges
        analysis.total_nodes = len(nodes)
        analysis.total_edges = len(edges)

        # Calculate network metrics
        if nodes:
            analysis.density = self._calculate_density(len(nodes), len(edges))
            analysis.average_degree = (2 * len(edges)) / len(nodes) if nodes else 0

        # Calculate centrality metrics
        if query.calculate_centrality:
            await self._calculate_centrality_metrics(analysis)

        # Detect clusters
        if query.detect_clusters:
            analysis.clusters = await self._detect_clusters(analysis)

        # Find circular flows
        if query.find_circular_flows:
            suspicious_paths = await self._find_circular_flows(analysis)
            analysis.suspicious_paths = suspicious_paths
            analysis.circular_flow_count = len(suspicious_paths)

        # Calculate risk
        if query.calculate_risk:
            await self._calculate_network_risk(analysis)

        # Identify key nodes
        analysis.key_nodes = self._identify_key_nodes(analysis)

        analysis.completed_at = datetime.utcnow()
        analysis.processing_time_seconds = (analysis.completed_at - start_time).total_seconds()

        self._analyses[analysis.analysis_id] = analysis
        return analysis

    async def _expand_network(
        self, root_id: str, root_type: str, max_depth: int, max_nodes: int,
        node_types: Optional[List[NodeType]], edge_types: Optional[List[EdgeType]]
    ) -> Tuple[List[NetworkNode], List[NetworkEdge]]:
        """Expand network from root node"""
        nodes = []
        edges = []
        visited: Set[str] = set()

        # Create root node
        root_node = NetworkNode(
            node_id=root_id,
            node_type=NodeType(root_type) if root_type in [t.value for t in NodeType] else NodeType.CUSTOMER,
            label=root_id,
            display_name=f"Root: {root_id}",
            entity_id=root_id,
            size=2.0,
            color="#FF6B6B"
        )
        nodes.append(root_node)
        visited.add(root_id)

        # Simulate network expansion (in real implementation, would query database)
        # For demo, create a sample network
        current_level = [root_id]

        for depth in range(max_depth):
            if len(nodes) >= max_nodes:
                break

            next_level = []
            for node_id in current_level:
                # Generate connected nodes (simulated)
                num_connections = min(3, max_nodes - len(nodes))
                for i in range(num_connections):
                    new_node_id = f"{node_id}_conn_{i}"
                    if new_node_id in visited:
                        continue

                    visited.add(new_node_id)

                    node = NetworkNode(
                        node_id=new_node_id,
                        node_type=NodeType.ACCOUNT if i % 2 == 0 else NodeType.EXTERNAL_PARTY,
                        label=new_node_id,
                        display_name=f"Node {new_node_id}",
                        entity_id=new_node_id,
                        size=1.0
                    )
                    nodes.append(node)
                    next_level.append(new_node_id)

                    edge = NetworkEdge(
                        source_node_id=node_id,
                        target_node_id=new_node_id,
                        edge_type=EdgeType.TRANSACTS_WITH,
                        transaction_count=5,
                        total_amount=10000.0 * (depth + 1),
                        weight=1.0
                    )
                    edges.append(edge)

            current_level = next_level

        return nodes, edges

    def _calculate_density(self, num_nodes: int, num_edges: int) -> float:
        """Calculate network density"""
        if num_nodes < 2:
            return 0.0
        max_edges = num_nodes * (num_nodes - 1) / 2
        return num_edges / max_edges if max_edges > 0 else 0.0

    async def _calculate_centrality_metrics(self, analysis: NetworkAnalysis):
        """Calculate centrality metrics for all nodes"""
        # Build adjacency list
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        for edge in analysis.edges:
            adjacency[edge.source_node_id].add(edge.target_node_id)
            if not edge.is_directed:
                adjacency[edge.target_node_id].add(edge.source_node_id)

        num_nodes = len(analysis.nodes)

        for node in analysis.nodes:
            # Degree centrality
            degree = len(adjacency[node.node_id])
            node.degree_centrality = degree / (num_nodes - 1) if num_nodes > 1 else 0

            # Simplified betweenness (full calculation is expensive)
            node.betweenness_centrality = degree / num_nodes

            # Simplified closeness
            node.closeness_centrality = degree / num_nodes

            # PageRank approximation
            node.pagerank = 1.0 / num_nodes

    async def _detect_clusters(self, analysis: NetworkAnalysis) -> List[NetworkCluster]:
        """Detect clusters/communities in the network"""
        clusters = []

        # Simple clustering based on connectivity
        # In real implementation, would use proper community detection (Louvain, etc.)

        # Build adjacency
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        for edge in analysis.edges:
            adjacency[edge.source_node_id].add(edge.target_node_id)
            adjacency[edge.target_node_id].add(edge.source_node_id)

        visited: Set[str] = set()
        cluster_num = 0

        for node in analysis.nodes:
            if node.node_id in visited:
                continue

            # BFS to find connected component
            cluster_nodes = []
            queue = [node.node_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                cluster_nodes.append(current)

                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)

            if len(cluster_nodes) >= 2:
                cluster_num += 1
                cluster = NetworkCluster(
                    cluster_name=f"Cluster {cluster_num}",
                    cluster_type="connected_component",
                    node_ids=cluster_nodes,
                    central_node_id=cluster_nodes[0],
                    size=len(cluster_nodes)
                )

                # Calculate cluster metrics
                cluster_edges = [
                    e for e in analysis.edges
                    if e.source_node_id in cluster_nodes and e.target_node_id in cluster_nodes
                ]
                cluster.total_transaction_count = sum(e.transaction_count for e in cluster_edges)
                cluster.total_transaction_amount = sum(e.total_amount for e in cluster_edges)

                clusters.append(cluster)

        return clusters

    async def _find_circular_flows(self, analysis: NetworkAnalysis) -> List[NetworkPath]:
        """Find circular money flows in the network"""
        circular_paths = []

        # Build directed graph
        graph: Dict[str, List[Tuple[str, UUID]]] = defaultdict(list)
        for edge in analysis.edges:
            graph[edge.source_node_id].append((edge.target_node_id, edge.edge_id))

        # Find cycles using DFS
        def find_cycles(start: str, current: str, path: List[str], edges: List[UUID], visited: Set[str]):
            if len(path) > 10:  # Limit cycle length
                return

            for neighbor, edge_id in graph[current]:
                if neighbor == start and len(path) >= 3:
                    # Found a cycle
                    cycle_path = NetworkPath(
                        start_node_id=start,
                        end_node_id=start,
                        node_sequence=path + [start],
                        edge_sequence=edges + [edge_id],
                        path_length=len(path),
                        is_circular=True,
                        risk_score=0.8
                    )
                    circular_paths.append(cycle_path)
                elif neighbor not in visited:
                    visited.add(neighbor)
                    find_cycles(start, neighbor, path + [neighbor], edges + [edge_id], visited)
                    visited.remove(neighbor)

        for node in analysis.nodes[:20]:  # Limit starting nodes for performance
            find_cycles(node.node_id, node.node_id, [node.node_id], [], {node.node_id})

        return circular_paths[:10]  # Return top 10 circular flows

    async def _calculate_network_risk(self, analysis: NetworkAnalysis):
        """Calculate overall network risk"""
        risk_score = 0.0
        risk_factors = 0

        # High-risk nodes
        high_risk_nodes = [n for n in analysis.nodes if n.risk_score > 70]
        if high_risk_nodes:
            risk_score += 20.0
            analysis.high_risk_node_count = len(high_risk_nodes)

        # PEP/Sanctions
        pep_nodes = [n for n in analysis.nodes if n.is_pep]
        sanctioned_nodes = [n for n in analysis.nodes if n.is_sanctioned]

        if pep_nodes:
            risk_score += 15.0
        if sanctioned_nodes:
            risk_score += 30.0

        # Circular flows
        if analysis.suspicious_paths:
            risk_score += len(analysis.suspicious_paths) * 5.0
            analysis.high_risk_path_count = len(analysis.suspicious_paths)

        # Network density (unusually dense networks can be suspicious)
        if analysis.density > 0.5:
            risk_score += 10.0

        analysis.overall_risk_score = min(risk_score, 100.0)
        analysis.risk_level = (
            NetworkRiskLevel.CRITICAL if risk_score >= 80 else
            NetworkRiskLevel.HIGH if risk_score >= 60 else
            NetworkRiskLevel.MEDIUM if risk_score >= 40 else
            NetworkRiskLevel.LOW
        )

    def _identify_key_nodes(self, analysis: NetworkAnalysis) -> List[str]:
        """Identify key nodes in the network"""
        # Sort by degree centrality
        sorted_nodes = sorted(
            analysis.nodes,
            key=lambda n: n.degree_centrality,
            reverse=True
        )
        return [n.node_id for n in sorted_nodes[:5]]

    async def analyze_link(
        self, entity_1_id: str, entity_1_type: str,
        entity_2_id: str, entity_2_type: str
    ) -> LinkAnalysisResult:
        """Analyze link between two entities"""
        result = LinkAnalysisResult(
            entity_1_id=entity_1_id,
            entity_1_type=entity_1_type,
            entity_2_id=entity_2_id,
            entity_2_type=entity_2_type
        )

        # Build network around both entities
        query = NetworkQuery(
            root_entity_type=entity_1_type,
            root_entity_id=entity_1_id,
            max_depth=4,
            max_nodes=100
        )
        network = await self.build_network(query)

        # Check if entity_2 is in the network
        entity_2_in_network = any(n.node_id == entity_2_id for n in network.nodes)

        if entity_2_in_network:
            result.is_connected = True
            # Find shortest path
            path = await self._find_shortest_path(network, entity_1_id, entity_2_id)
            if path:
                result.shortest_path = path
                result.shortest_path_length = path.path_length
                result.all_paths = [path]

        return result

    async def _find_shortest_path(
        self, network: NetworkAnalysis, start: str, end: str
    ) -> Optional[NetworkPath]:
        """Find shortest path between two nodes using BFS"""
        # Build adjacency list
        adjacency: Dict[str, List[Tuple[str, UUID]]] = defaultdict(list)
        for edge in network.edges:
            adjacency[edge.source_node_id].append((edge.target_node_id, edge.edge_id))
            adjacency[edge.target_node_id].append((edge.source_node_id, edge.edge_id))

        # BFS
        queue = [(start, [start], [])]
        visited = {start}

        while queue:
            current, path, edges = queue.pop(0)

            if current == end:
                return NetworkPath(
                    start_node_id=start,
                    end_node_id=end,
                    node_sequence=path,
                    edge_sequence=edges,
                    path_length=len(path) - 1
                )

            for neighbor, edge_id in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], edges + [edge_id]))

        return None

    async def detect_communities(self, analysis_id: UUID) -> CommunityDetectionResult:
        """Run community detection on an existing analysis"""
        analysis = self._analyses.get(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        result = CommunityDetectionResult(
            analysis_id=analysis_id,
            algorithm="simple_components",
            parameters={},
            communities=analysis.clusters,
            community_count=len(analysis.clusters)
        )

        # Identify suspicious communities
        result.suspicious_community_ids = [
            c.cluster_id for c in analysis.clusters
            if c.risk_score > 60
        ]
        result.suspicious_community_count = len(result.suspicious_community_ids)

        return result

    async def generate_visualization(
        self, analysis_id: UUID, layout_algorithm: str = "force_directed"
    ) -> NetworkVisualization:
        """Generate visualization data for a network analysis"""
        analysis = self._analyses.get(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        viz = NetworkVisualization(
            analysis_id=analysis_id,
            layout_algorithm=layout_algorithm
        )

        # Calculate layout positions
        # Simple circular layout for demo
        num_nodes = len(analysis.nodes)
        for i, node in enumerate(analysis.nodes):
            angle = 2 * math.pi * i / num_nodes
            x = math.cos(angle) * 100
            y = math.sin(angle) * 100
            viz.layout_data[node.node_id] = (x, y)

        # Node styles
        for node in analysis.nodes:
            viz.node_styles[node.node_id] = {
                "size": node.size * 10,
                "color": node.color or self._get_node_color(node.node_type),
                "label": node.display_name
            }

        # Edge styles
        for edge in analysis.edges:
            viz.edge_styles[str(edge.edge_id)] = {
                "width": edge.thickness * 2,
                "color": edge.color or "#999999",
                "style": edge.style
            }

        return viz

    def _get_node_color(self, node_type: NodeType) -> str:
        """Get default color for node type"""
        colors = {
            NodeType.CUSTOMER: "#4ECDC4",
            NodeType.ACCOUNT: "#45B7D1",
            NodeType.TRANSACTION: "#96CEB4",
            NodeType.EXTERNAL_PARTY: "#FFEAA7",
            NodeType.ORGANIZATION: "#DDA0DD",
            NodeType.ADDRESS: "#98D8C8",
            NodeType.PHONE: "#F7DC6F",
            NodeType.EMAIL: "#85C1E9",
            NodeType.DEVICE: "#F1948A",
            NodeType.IP_ADDRESS: "#BB8FCE"
        }
        return colors.get(node_type, "#CCCCCC")

    async def get_analysis(self, analysis_id: UUID) -> Optional[NetworkAnalysis]:
        """Get a network analysis by ID"""
        return self._analyses.get(analysis_id)

    async def get_statistics(self) -> NetworkStatistics:
        """Get network analysis statistics"""
        stats = NetworkStatistics()
        stats.total_analyses = len(self._analyses)

        for analysis in self._analyses.values():
            stats.total_nodes_analyzed += analysis.total_nodes
            stats.total_edges_analyzed += analysis.total_edges
            stats.clusters_detected += len(analysis.clusters)
            stats.circular_flows_detected += analysis.circular_flow_count

            if analysis.risk_level in [NetworkRiskLevel.HIGH, NetworkRiskLevel.CRITICAL]:
                stats.high_risk_networks += 1

        if self._analyses:
            stats.average_network_size = stats.total_nodes_analyzed / len(self._analyses)
            stats.average_analysis_time_seconds = sum(
                a.processing_time_seconds for a in self._analyses.values()
            ) / len(self._analyses)

        return stats


# Global service instance
network_analysis_service = NetworkAnalysisService()
