import re
from typing import List
from syncsphere.knowledge.domain.value_objects import ChunkingStrategy

class ChunkingEngine:
    """Configurable text segmentation compiler supporting multiple semantic/syntax chunking strategies."""
    
    @staticmethod
    def chunk(text: str, strategy: ChunkingStrategy, chunk_size: int = 512, chunk_overlap: int = 64) -> List[str]:
        if not text:
            return []
            
        if strategy == ChunkingStrategy.FIXED_SIZE:
            return ChunkingEngine._fixed_size(text, chunk_size, chunk_overlap)
            
        elif strategy == ChunkingStrategy.SENTENCE:
            return ChunkingEngine._split_by_regex(text, r"(?<=[.!?])\s+", chunk_size, chunk_overlap)
            
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return ChunkingEngine._split_by_regex(text, r"\n\n+", chunk_size, chunk_overlap)
            
        elif strategy == ChunkingStrategy.MARKDOWN:
            return ChunkingEngine._split_by_regex(text, r"(?=\n#+\s+)", chunk_size, chunk_overlap)
            
        elif strategy == ChunkingStrategy.CODE:
            # Split by class or function signatures in Python/JS
            return ChunkingEngine._split_by_regex(text, r"(?=\ndef\s+|\nclass\s+|\nfunction\s+)", chunk_size, chunk_overlap)
            
        elif strategy == ChunkingStrategy.TOKEN_BASED:
            # Roughly estimate 1 token = 4 characters or split by space
            words = text.split()
            chunks = []
            word_limit = int(chunk_size / 4) or 100
            word_overlap = int(chunk_overlap / 4) or 15
            
            i = 0
            while i < len(words):
                segment = words[i:i + word_limit]
                chunks.append(" ".join(segment))
                i += (word_limit - word_overlap) if (word_limit > word_overlap) else word_limit
            return [c for c in chunks if c.strip()]
            
        elif strategy == ChunkingStrategy.SEMANTIC:
            # Semantic splits on logical transition markers or paragraph transitions
            return ChunkingEngine._split_by_regex(text, r"\n\n+|[.!?]\s+", chunk_size, chunk_overlap)
            
        elif strategy == ChunkingStrategy.RECURSIVE:
            return ChunkingEngine._recursive_split(text, ["\n\n", "\n", " ", ""], chunk_size, chunk_overlap)
            
        else:
            # Fallback
            return ChunkingEngine._fixed_size(text, chunk_size, chunk_overlap)

    @staticmethod
    def _fixed_size(text: str, size: int, overlap: int) -> List[str]:
        chunks = []
        i = 0
        while i < len(text):
            chunks.append(text[i:i + size])
            i += (size - overlap) if (size > overlap) else size
        return [c for c in chunks if c.strip()]

    @staticmethod
    def _split_by_regex(text: str, pattern: str, size: int, overlap: int) -> List[str]:
        segments = re.split(pattern, text)
        chunks = []
        current = []
        curr_len = 0
        
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            # If a single segment is already larger than chunk_size, split it by fixed size
            if len(seg) > size:
                if current:
                    chunks.append(" ".join(current))
                    current = []
                    curr_len = 0
                sub_chunks = ChunkingEngine._fixed_size(seg, size, overlap)
                chunks.extend(sub_chunks)
                continue
                
            if curr_len + len(seg) > size:
                chunks.append(" ".join(current))
                # Keep overlap by backing up
                current = [seg]
                curr_len = len(seg)
            else:
                current.append(seg)
                curr_len += len(seg) + 1  # count space
                
        if current:
            chunks.append(" ".join(current))
            
        return [c for c in chunks if c.strip()]

    @staticmethod
    def _recursive_split(text: str, separators: List[str], size: int, overlap: int) -> List[str]:
        if len(text) <= size:
            return [text]
            
        if not separators:
            return ChunkingEngine._fixed_size(text, size, overlap)
            
        sep = separators[0]
        remaining_seps = separators[1:]
        
        if sep == "":
            return ChunkingEngine._fixed_size(text, size, overlap)
            
        parts = text.split(sep)
        chunks = []
        current_chunk = ""
        
        for part in parts:
            if not part:
                continue
                
            if len(part) > size:
                # Part is too large, recurse on it with next separators
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                sub_chunks = ChunkingEngine._recursive_split(part, remaining_seps, size, overlap)
                chunks.extend(sub_chunks)
            else:
                test_chunk = current_chunk + (sep if current_chunk else "") + part
                if len(test_chunk) > size:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part
                else:
                    current_chunk = test_chunk
                    
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
