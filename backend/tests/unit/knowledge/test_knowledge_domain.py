import pytest
from datetime import datetime
import uuid

from syncsphere.knowledge.domain.value_objects import (
    ChunkingStrategy,
    RetrievalPolicy,
    KnowledgeSourceType,
    KnowledgePolicy
)
from syncsphere.knowledge.domain.entities import (
    KnowledgeSource,
    KnowledgeDocument,
    KnowledgeChunk,
    SemanticCacheEntry
)
from syncsphere.knowledge.application.services.chunking import ChunkingEngine
from syncsphere.knowledge.application.services.vector import cosine_similarity
from syncsphere.knowledge.application.services.cache import SimilarityThreshold
from syncsphere.knowledge.application.services.graph import (
    KnowledgeGraphBuilder,
    GraphTraversal,
    GraphSearch
)

def test_chunking_strategies():
    text = "Line one.\nLine two.\nLine three."
    
    # 1. Sentence strategy split
    chunks = ChunkingEngine.chunk(text, ChunkingStrategy.SENTENCE, chunk_size=12, chunk_overlap=0)
    assert len(chunks) == 3
    assert "Line one." in chunks
    assert "Line two." in chunks
    assert "Line three." in chunks

    # 2. Fixed size strategy split
    chunks_fixed = ChunkingEngine.chunk(text, ChunkingStrategy.FIXED_SIZE, chunk_size=10, chunk_overlap=0)
    assert len(chunks_fixed) > 0
    assert chunks_fixed[0] == text[:10]

    # 3. Paragraph strategy split
    text_p = "Paragraph one.\n\nParagraph two."
    chunks_p = ChunkingEngine.chunk(text_p, ChunkingStrategy.PARAGRAPH, chunk_size=20, chunk_overlap=0)
    assert len(chunks_p) == 2
    assert "Paragraph one." in chunks_p
    assert "Paragraph two." in chunks_p


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    v4 = [1.0, 1.0, 0.0]
    
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)
    assert cosine_similarity(v1, v3) == pytest.approx(0.0)
    assert cosine_similarity(v1, v4) == pytest.approx(0.7071, abs=1e-3)
    
    # Similarity threshold matching
    assert SimilarityThreshold.is_match(v1, v2, threshold=0.9) is True
    assert SimilarityThreshold.is_match(v1, v3, threshold=0.9) is False


def test_knowledge_graph_builder_and_traversal():
    doc_id = str(uuid.uuid4())
    doc = KnowledgeDocument(
        source_id="src_1",
        org_id="org_1",
        title="Doc A",
        content="Document content here",
        id=doc_id
    )
    
    target_id = "doc_target_id"
    doc.add_relationship(target_id, "REFERENCES", weight=1.0)
    
    # Build graph
    res = KnowledgeGraphBuilder.build([doc])
    nodes = res["nodes"]
    edges = res["edges"]
    
    assert len(nodes) == 1
    assert len(edges) == 1
    assert edges[0].source_id == doc_id
    assert edges[0].target_id == target_id
    
    # Traversal (depth limit = 3)
    visited = GraphTraversal.traverse(start_node_id=doc_id, edges=edges, max_depth=3)
    assert doc_id in visited
    assert target_id in visited

    # Path Search
    paths = GraphSearch.find_paths(start_id=doc_id, target_id=target_id, edges=edges)
    assert len(paths) == 1
    assert paths[0] == [doc_id, target_id]
