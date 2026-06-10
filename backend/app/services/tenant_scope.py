"""多用户数据隔离：普通用户仅访问自己的数据，管理员可查看全部。"""
from sqlalchemy import Select

from app.models.article import Article
from app.models.monitor import CrawlTask
from app.models.user import User, UserRoleEnum


def is_admin(user: User) -> bool:
    return UserRoleEnum.ADMIN in {r.name for r in user.roles}


def scope_owner(query: Select, model, user: User, owner_attr: str = "owner_id") -> Select:
    if is_admin(user):
        return query
    col = getattr(model, owner_attr)
    return query.where(col == user.id)


def can_access_owner(user: User, owner_id: int | None) -> bool:
    if is_admin(user):
        return True
    return owner_id == user.id


def assert_task_access(user: User, task: CrawlTask) -> None:
    if not can_access_owner(user, task.owner_id):
        raise PermissionError("无权操作该采集任务")


def assert_article_access(user: User, article: Article) -> None:
    if not can_access_owner(user, article.owner_id):
        raise ValueError("无权访问该文章")
