import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill
from app.models.skill_catalog import SkillCatalog
from app.services.job_intelligence.service import analyze_and_persist_job


JOB_DESCRIPTION = """
Requirements:
- Strong knowledge of Python and FastAPI
- Experience with PostgreSQL and Docker
- Good understanding of Git

Preferred Qualifications:
- Experience with React.js and TypeScript

Responsibilities:
- Build backend services
- Write automated tests
"""


async def main():
    async with AsyncSessionLocal() as session:

        # Create a test job
        job = Job(
            source="test",
            external_id="job-intelligence-test-v2",
            title="Software Engineering Intern",
            company="CareerPilot Test",
            location="Remote",
            description=JOB_DESCRIPTION,
            employment_type="Internship",
            experience_level="Entry Level",
            application_url="https://example.com/apply",
            is_active=True,
        )

        session.add(job)
        await session.flush()

        print("\n=== JOB INTELLIGENCE ===")

        result = await analyze_and_persist_job(job.id, session)

        for requirement in result["requirements"]:
            print(
                f"{requirement['requirement_type']:<15} | "
                f"{requirement['importance']:<3} | "
                f"{requirement['text']} | "
                f"{[skill['name'] for skill in requirement['skills']]}"
            )

        print("\n=== STORED IN DATABASE ===")

        db_result = await session.execute(
            select(JobRequirement)
            .where(JobRequirement.job_id == job.id)
            .order_by(JobRequirement.created_at)
        )

        requirements = db_result.scalars().all()

        for requirement in requirements:

            skill_result = await session.execute(
                select(SkillCatalog.name)
                .join(
                    JobRequirementSkill,
                    JobRequirementSkill.skill_id == SkillCatalog.id,
                )
                .where(
                    JobRequirementSkill.requirement_id == requirement.id
                )
                .order_by(SkillCatalog.name)
            )

            skills = skill_result.scalars().all()

            print(
                f"{requirement.requirement_type:<15} | "
                f"{requirement.importance:<3} | "
                f"{requirement.text}"
            )

            print(f"    skills → {skills}")

        print(
            f"\nTotal requirements stored: "
            f"{len(requirements)}"
        )

        skill_link_result = await session.execute(
            select(JobRequirementSkill)
            .join(
                JobRequirement,
                JobRequirementSkill.requirement_id == JobRequirement.id,
            )
            .where(JobRequirement.job_id == job.id)
        )

        skill_links = skill_link_result.scalars().all()

        print(
            f"Total requirement-skill links: "
            f"{len(skill_links)}"
        )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())