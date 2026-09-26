from app.models import AIComment, Organization, Repository, User


def test_models_importable() -> None:
    assert AIComment.__tablename__ == "ai_comments"
    assert Organization.__tablename__ == "organizations"
    assert Repository.__tablename__ == "repositories"
    assert User.__tablename__ == "users"
