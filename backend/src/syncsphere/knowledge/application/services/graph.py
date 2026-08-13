import logging
from typing import List, Dict, Any, Optional, Set
from syncsphere.knowledge.domain.entities.document import KnowledgeDocument
from syncsphere.knowledge.domain.value_objects import KnowledgeGraphNode, KnowledgeGraphEdge

logger = logging.getLogger("syncsphere.knowledge.application.services.graph")

class RelationshipExtractor:
    """Extracts semantic relation tuples from parsed document text blocks."""
    @staticmethod
    def extract_relations(doc: KnowledgeDocument) -> List[KnowledgeGraphEdge]:
        edges = []
        for rel in doc.relationships:
            edges.append(KnowledgeGraphEdge(
                source_id=rel.source_node_id,
                target_id=rel.target_node_id,
                type=rel.relationship_type,
                weight=rel.weight
            ))
        return edges


class EntityLinker:
    """Resolves duplicate entity descriptors by linking them to unique identifier nodes."""
    @staticmethod
    def link_entities(nodes: List[KnowledgeGraphNode]) -> List[KnowledgeGraphNode]:
        # Dedup nodes based on node_id
        seen = set()
        unique_nodes = []
        for n in nodes:
            if n.node_id not in seen:
                seen.add(n.node_id)
                unique_nodes.append(n)
        return unique_nodes


class ReferenceResolver:
    """Resolves cross-document hyperlinks or mentions into explicit graph edges."""
    @staticmethod
    def resolve_references(edges: List[KnowledgeGraphEdge]) -> List[KnowledgeGraphEdge]:
        return edges


class GraphTraversal:
    """Walks the relational graph topology with strict depth constraints (default max depth = 3)."""
    @staticmethod
    def traverse(
        start_node_id: str,
        edges: List[KnowledgeGraphEdge],
        max_depth: int = 3
    ) -> Set[str]:
        visited = {start_node_id}
        current_tier = {start_node_id}
        
        for _ in range(max_depth):
            next_tier = set()
            for node in current_tier:
                for edge in edges:
                    if edge.source_id == node and edge.target_id not in visited:
                        next_tier.add(edge.target_id)
                        visited.add(edge.target_id)
            if not next_tier:
                break
            current_tier = next_tier
            
        return visited


class GraphSearch:
    """Performs topological path queries over the concept graph network."""
    @staticmethod
    def find_paths(
        start_id: str,
        target_id: str,
        edges: List[KnowledgeGraphEdge],
        max_depth: int = 3
    ) -> List[List[str]]:
        paths = []
        
        def dfs(curr: str, path: List[str], depth: int):
            if curr == target_id:
                paths.append(path)
                return
            if depth >= max_depth:
                return
            for edge in edges:
                if edge.source_id == curr and edge.target_id not in path:
                    dfs(edge.target_id, path + [edge.target_id], depth + 1)
                    
        dfs(start_id, [start_id], 0)
        return paths


class GraphRanking:
    """Ranks nodes by connection density (degree centrality)."""
    @staticmethod
    def rank_nodes(nodes: List[KnowledgeGraphNode], edges: List[KnowledgeGraphEdge]) -> List[Dict[str, Any]]:
        degrees = {n.node_id: 0 for n in nodes}
        for edge in edges:
            if edge.source_id in degrees:
                degrees[edge.source_id] += 1
            if edge.target_id in degrees:
                degrees[edge.target_id] += 1
                
        ranked = [{"node_id": nid, "degree": deg} for nid, deg in degrees.items()]
        ranked.sort(key=lambda x: x["degree"], reverse=True)
        return ranked


class GraphStatistics:
    """Calculates network health metrics: total nodes, total edges, and average degree."""
    @staticmethod
    def calculate(nodes: List[KnowledgeGraphNode], edges: List[KnowledgeGraphEdge]) -> Dict[str, Any]:
        node_count = len(nodes)
        edge_count = len(edges)
        avg_degree = (2.0 * edge_count / node_count) if node_count > 0 else 0.0
        return {
            "nodes_count": node_count,
            "edges_count": edge_count,
            "average_degree": avg_degree
        }


class KnowledgeGraphBuilder:
    """Aggregates documents into a compiled graph of linked concepts, relationships, and traversal logic."""
    
    @staticmethod
    def build(documents: List[KnowledgeDocument]) -> Dict[str, Any]:
        nodes = []
        edges = []
        
        for doc in documents:
            # Create a graph node for each document
            nodes.append(KnowledgeGraphNode(
                node_id=doc.id,
                name=doc.title,
                type="DOCUMENT",
                attributes={"status": doc.status, "version": doc.version}
            ))
            
            # Extract relation edges
            extracted = RelationshipExtractor.extract_relations(doc)
            edges.extend(extracted)
            
        # Link entities and resolve references
        linked_nodes = EntityLinker.link_entities(nodes)
        resolved_edges = ReferenceResolver.resolve_references(edges)
        
        stats = GraphStatistics.calculate(linked_nodes, resolved_edges)
        
        return {
            "nodes": linked_nodes,
            "edges": resolved_edges,
            "statistics": stats
        }
