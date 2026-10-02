import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_alias import SkillAlias
from app.models.skill_catalog import SkillCatalog

def normalize_skill_text(text: str) -> str:
    """
    Normalize skill text for consistent catalog/alias matching.
    """
    if not text:
        return ""

    text = text.strip().lower()

    # Normalize common separators.
    text = text.replace("&", " and ")

    # Remove punctuation while preserving common version notation.
    text = re.sub(r"[^\w\s.+#-]", " ", text)

    # Normalize repeated whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def build_skill_lookup(
    skills: list[dict[str, str]],
) -> dict[str, str]:
    """
    Build a normalized alias/name -> canonical skill lookup.

    Expected input:

    [
        {
            "name": "Python",
            "aliases": "python 3, python programming"
        },
        ...
    ]
    """
    lookup: dict[str, str] = {}

    for skill in skills:
        name = skill.get("name", "").strip()

        if not name:
            continue

        canonical = name

        normalized_name = normalize_skill_text(name)

        if normalized_name:
            lookup[normalized_name] = canonical

        aliases = skill.get("aliases", "")

        for alias in aliases.split(","):
            normalized_alias = normalize_skill_text(alias)

            if normalized_alias:
                lookup[normalized_alias] = canonical

    return lookup


def normalize_skill(
    skill_text: str,
    skill_lookup: dict[str, str],
) -> str | None:
    """
    Resolve a raw skill name to its canonical catalog name.
    """
    normalized = normalize_skill_text(skill_text)

    if not normalized:
        return None

    return skill_lookup.get(normalized)

async def load_skill_lookup(
    session: AsyncSession,
) -> dict[str, SkillCatalog]:
    """
    Load canonical skill names and aliases from PostgreSQL.

    Returns:
        normalized skill/alias -> SkillCatalog object
    """
    lookup: dict[str, SkillCatalog] = {}

    result = await session.execute(
        select(SkillCatalog).where(
            SkillCatalog.is_active.is_(True)
        )
    )

    skills = result.scalars().all()

    for skill in skills:
        normalized_name = normalize_skill_text(skill.name)

        if normalized_name:
            lookup[normalized_name] = skill

    alias_result = await session.execute(
        select(SkillAlias)
        .join(SkillCatalog)
        .where(SkillCatalog.is_active.is_(True))
    )

    aliases = alias_result.scalars().all()

    for alias in aliases:
        normalized_alias = normalize_skill_text(alias.alias)

        if normalized_alias and alias.skill:
            lookup[normalized_alias] = alias.skill

    return lookup


async def resolve_skill(
    skill_text: str,
    session: AsyncSession,
) -> SkillCatalog | None:
    """
    Resolve raw skill text to a canonical SkillCatalog record.
    """
    lookup = await load_skill_lookup(session)

    normalized = normalize_skill_text(skill_text)

    if not normalized:
        return None

    return lookup.get(normalized)