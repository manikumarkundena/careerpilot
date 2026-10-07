from app.services.resume.content_selector import (
    ContentCandidate,
    select_relevant_content,
)


def test_select_relevant_content_prioritizes_keyword_overlap():
    candidates = [
        ContentCandidate(
            text="Built a web dashboard",
            source_type="project",
            source_id="1",
            keywords=("React", "TypeScript"),
        ),
        ContentCandidate(
            text="Built an API",
            source_type="project",
            source_id="2",
            keywords=("FastAPI", "PostgreSQL"),
        ),
    ]

    result = select_relevant_content(candidates, {"fastapi", "postgresql"})

    assert result[0].source_id == "2"


def test_select_relevant_content_never_changes_source_text():
    candidate = ContentCandidate(
        text="Original factual statement",
        source_type="experience",
        source_id="1",
    )

    result = select_relevant_content([candidate], {"python"})

    assert result[0].text == candidate.text


def test_select_relevant_content_respects_limit():
    candidates = [
        ContentCandidate(
            text=f"Fact {index}",
            source_type="project",
            source_id=str(index),
            priority=index,
        )
        for index in range(3)
    ]

    result = select_relevant_content(candidates, set(), limit=2)

    assert len(result) == 2
    assert [item.source_id for item in result] == ["2", "1"]
