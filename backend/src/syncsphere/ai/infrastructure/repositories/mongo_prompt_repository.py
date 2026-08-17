from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.ai.domain.repositories import PromptTemplateRepository, PromptVersionRepository
from syncsphere.ai.domain.entities.prompt import PromptTemplate, PromptVersion
from syncsphere.ai.infrastructure.documents import PromptTemplateDocument, PromptVersionDocument
from syncsphere.ai.infrastructure.mappers import AIMappers

class MongoPromptTemplateRepository(PromptTemplateRepository):
    """Concrete Mongo repository implementing PromptTemplateRepository using Beanie ODM."""
    async def save(self, template: PromptTemplate) -> None:
        doc = AIMappers.template_to_document(template)
        if template.id:
            try:
                existing = await PromptTemplateDocument.get(PydanticObjectId(template.id))
                if existing:
                    existing.name = doc.name
                    existing.description = doc.description
                    existing.latest_version = doc.latest_version
                    existing.tags = doc.tags
                    existing.author = doc.author
                    existing.purpose = doc.purpose
                    existing.variables = doc.variables
                    await existing.save()
                    return
            except Exception:
                pass
        await doc.insert()
        template.id = str(doc.id)

    async def get_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        try:
            doc = await PromptTemplateDocument.get(PydanticObjectId(template_id))
            return AIMappers.template_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_name(self, org_id: str, name: str) -> Optional[PromptTemplate]:
        doc = await PromptTemplateDocument.find_one({"org_id": org_id, "name": name.strip()})
        return AIMappers.template_to_domain(doc) if doc else None

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[PromptTemplate]:
        skip = (page - 1) * page_size
        docs = await PromptTemplateDocument.find({"org_id": org_id}).skip(skip).limit(page_size).to_list()
        return [AIMappers.template_to_domain(doc) for doc in docs]

    async def count_by_org(self, org_id: str) -> int:
        return await PromptTemplateDocument.find({"org_id": org_id}).count()

    async def delete(self, template_id: str) -> None:
        try:
            doc = await PromptTemplateDocument.get(PydanticObjectId(template_id))
            if doc:
                await doc.delete()
        except Exception:
            pass


class MongoPromptVersionRepository(PromptVersionRepository):
    """Concrete Mongo repository implementing PromptVersionRepository using Beanie ODM."""
    async def save(self, version: PromptVersion) -> None:
        doc = AIMappers.version_to_document(version)
        if version.id:
            try:
                existing = await PromptVersionDocument.get(PydanticObjectId(version.id))
                if existing:
                    existing.prompt_template_id = doc.prompt_template_id
                    existing.version = doc.version
                    existing.system_template = doc.system_template
                    existing.user_template = doc.user_template
                    existing.hash = doc.hash
                    existing.description = doc.description
                    existing.parent_version_id = doc.parent_version_id
                    await existing.save()
                    return
            except Exception:
                pass
        await doc.insert()
        version.id = str(doc.id)

    async def get_by_version(self, template_id: str, version: int) -> Optional[PromptVersion]:
        doc = await PromptVersionDocument.find_one({
            "prompt_template_id": template_id,
            "version": version
        })
        return AIMappers.version_to_domain(doc) if doc else None

    async def list_versions(self, template_id: str) -> List[PromptVersion]:
        docs = await PromptVersionDocument.find({"prompt_template_id": template_id}).to_list()
        return [AIMappers.version_to_domain(doc) for doc in docs]
