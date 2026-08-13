from syncsphere.shared_kernel.domain.domain_exception import DomainException

class KnowledgeSourceNotFoundException(DomainException):
    def __init__(self, source_id: str) -> None:
        super().__init__(
            code="KNOWLEDGE_SOURCE_NOT_FOUND",
            message=f"Knowledge source '{source_id}' was not found in active workspace."
        )

class KnowledgeDocumentNotFoundException(DomainException):
    def __init__(self, doc_id: str) -> None:
        super().__init__(
            code="KNOWLEDGE_DOCUMENT_NOT_FOUND",
            message=f"Knowledge document '{doc_id}' was not found in namespace."
        )

class ChunkingException(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="CHUNKING_FAILED",
            message=message
        )

class EmbeddingException(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="EMBEDDING_FAILED",
            message=message
        )

class VectorStoreException(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="VECTOR_STORE_ERROR",
            message=message
        )

class CacheException(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="CACHE_ERROR",
            message=message
        )
