from __future__ import annotations

from ragscaleguard.models import Document


def validate_top_k(top_k: int) -> None:
    if top_k < 0:
        raise ValueError("top_k must be greater than or equal to zero")


def validate_unique_document_ids(documents: list[Document]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for document in documents:
        if document.id in seen:
            duplicates.add(document.id)
        seen.add(document.id)
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise ValueError(f"Document IDs must be unique: {duplicate_list}")
