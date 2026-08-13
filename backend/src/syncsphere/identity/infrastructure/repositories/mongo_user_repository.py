from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.identity.domain.repositories.user_repository import UserRepository
from syncsphere.identity.domain.entities.user import User
from syncsphere.identity.infrastructure.documents.user_document import UserDocument
from syncsphere.identity.infrastructure.mappers import IdentityMappers
# from syncsphere.identity.infrastructure.documents import UserDocument
from syncsphere.identity.infrastructure.documents.user_document import UserDocument

class MongoUserRepository(UserRepository):
    """Concrete Mongo repository implementing UserRepository interface using Beanie ODM."""
    
    async def save(self, user: User) -> None:
        doc = IdentityMappers.user_to_document(user)
        if user.id:
            # Check if document already exists
            try:
                existing_doc = await UserDocument.get(PydanticObjectId(user.id))
                if existing_doc:
                    # Update fields on existing
                    existing_doc.email = doc.email
                    existing_doc.password_hash = doc.password_hash
                    existing_doc.first_name = doc.first_name
                    existing_doc.last_name = doc.last_name
                    existing_doc.role_ids = doc.role_ids
                    existing_doc.status = doc.status
                    await existing_doc.save()
                    return
            except Exception:
                pass
        # Else create new
        await doc.insert()
        user.id = str(doc.id)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            doc = await UserDocument.get(PydanticObjectId(user_id))
            return IdentityMappers.user_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_email(self, email: str) -> Optional[User]:
        doc = await UserDocument.find_one(UserDocument.email == email.lower().strip())
        return IdentityMappers.user_to_domain(doc) if doc else None

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[User]:
        skip = (page - 1) * page_size
        docs = await UserDocument.find(
            UserDocument.org_id == org_id
        ).skip(skip).limit(page_size).to_list()
        return [IdentityMappers.user_to_domain(doc) for doc in docs]

    async def count_by_org(self, org_id: str) -> int:
        return await UserDocument.find(UserDocument.org_id == org_id).count()
    
    async def update_github_connection(
            self,
            user_id: str,
            github_id: str,
            github_username: str,
            access_token: str,
            ):
        user = await UserDocument.get(PydanticObjectId(user_id))
        if user is None:
            return None
        user.github.connected = True
        user.github.github_id = str(github_id["id"])
        user.github.github_username = github_username["login"]
        user.github.access_token = access_token

        await user.save()
        return user
    async def connect_slack(
            self,
            user_id: str,
            access_token: str,
            team_id: str,
            team_name: str,
            bot_user_id: str,
            ):
        user = await UserDocument.get(user_id)
        if not user:
            return None
        
        user.slack.connected = True
        user.slack.access_token = access_token
        user.slack.team_id = team_id
        user.slack.team_name = team_name
        user.slack.bot_user_id = bot_user_id

        await user.save()

        return user
