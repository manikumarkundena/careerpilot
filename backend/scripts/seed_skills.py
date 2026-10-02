import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.skill_alias import SkillAlias
from app.models.skill_catalog import SkillCatalog

SKILLS = {
    "Python": {
        "category": "Programming Language",
        "aliases": ["Python 3", "Python3", "Python programming"],
    },
    "Java": {
        "category": "Programming Language",
        "aliases": ["Java SE", "Java programming"],
    },
    "JavaScript": {
        "category": "Programming Language",
        "aliases": ["JS", "ECMAScript"],
    },
    "TypeScript": {
        "category": "Programming Language",
        "aliases": ["TS"],
    },
    "C++": {
        "category": "Programming Language",
        "aliases": ["CPP", "C plus plus"],
    },
    "React": {
        "category": "Frontend",
        "aliases": ["React.js", "ReactJS", "React JS"],
    },
    "Next.js": {
        "category": "Frontend",
        "aliases": ["NextJS", "Next JS"],
    },
    "FastAPI": {
        "category": "Backend",
        "aliases": ["Fast API"],
    },
    "Node.js": {
        "category": "Backend",
        "aliases": ["NodeJS", "Node JS", "Node"],
    },
    "PostgreSQL": {
        "category": "Database",
        "aliases": ["Postgres", "PostgresSQL", "PostgreSQL DB"],
    },
    "MySQL": {
        "category": "Database",
        "aliases": ["My SQL"],
    },
    "Docker": {
        "category": "DevOps",
        "aliases": ["Docker Engine", "Docker Containers"],
    },
    "Git": {
        "category": "Developer Tools",
        "aliases": ["Git SCM"],
    },
    "GitHub": {
        "category": "Developer Tools",
        "aliases": ["Github"],
    },
    "AWS": {
        "category": "Cloud",
        "aliases": ["Amazon Web Services"],
    },
    "SQL": {
        "category": "Database",
        "aliases": ["Structured Query Language"],
    },
    "HTML": {
        "category": "Frontend",
        "aliases": ["HTML5"],
    },
    "CSS": {
        "category": "Frontend",
        "aliases": ["CSS3"],
    },
}


async def seed_skills() -> None:
    async with AsyncSessionLocal() as session:
        for skill_name, data in SKILLS.items():
            result = await session.execute(
                select(SkillCatalog).where(
                    SkillCatalog.name == skill_name
                )
            )

            skill = result.scalar_one_or_none()

            if skill is None:
                skill = SkillCatalog(
                    name=skill_name,
                    category=data["category"],
                )
                session.add(skill)
                await session.flush()

            for alias_name in data["aliases"]:
                alias_result = await session.execute(
                    select(SkillAlias).where(
                        SkillAlias.alias == alias_name
                    )
                )

                alias = alias_result.scalar_one_or_none()

                if alias is None:
                    session.add(
                        SkillAlias(
                            skill_id=skill.id,
                            alias=alias_name,
                        )
                    )

        await session.commit()

    print(f"Seeded {len(SKILLS)} canonical skills.")


if __name__ == "__main__":
    asyncio.run(seed_skills())
