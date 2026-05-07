from __future__ import annotations

import pytest

from ragscaleguard.diagnostics.density import CorpusDensityAnalyser
from ragscaleguard.models import Document


def test_density_analysis_surfaces_crowded_documents() -> None:
    documents = [
        Document("a", "Atlas streaming retry technical specification"),
        Document("b", "Atlas streaming retry spec draft"),
        Document("c", "Facilities lunch menu"),
    ]

    findings = CorpusDensityAnalyser(similarity_threshold=0.2).analyse(documents, nearest_k=1)

    assert findings[0].document_id in {"a", "b"}
    assert findings[0].neighbours_above_threshold >= 1


def test_density_analysis_handles_zero_nearest_neighbours() -> None:
    findings = CorpusDensityAnalyser().analyse(
        [
            Document("a", "Atlas streaming retry technical specification"),
            Document("b", "Atlas streaming retry spec draft"),
        ],
        nearest_k=0,
    )

    assert findings[0].mean_similarity == 0
    assert findings[0].nearest_document_ids == ()


def test_density_analysis_rejects_negative_nearest_k() -> None:
    with pytest.raises(ValueError, match="nearest_k"):
        CorpusDensityAnalyser().analyse([Document("a", "Atlas")], nearest_k=-1)
