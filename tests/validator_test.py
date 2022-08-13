import asyncio
import os
import typing as t
import uuid

from edgegraph.schema import EdgeModel
from edgegraph.validator import SchemaValidator, ValidationError
import pendulum
from pydantic import Field
import pytest


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def edgedb_dsn():
    dsn = os.getenv("EDGEDB_DSN")
    if not dsn:
        pytest.skip("Cannot test this test without EDGEDB_DSN environment variable.")

    return dsn


@pytest.mark.asyncio
async def test_validator_with_valid_edgemodels(edgedb_dsn):
    class UserModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        email: str
        password: str
        name: str = Field(min_length=3)

        class Config:
            module: str = "default"
            name: str = "User"

    class MemoModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        title: str
        content: str
        tags: t.List[str] = Field(default=[])

        created_by: UserModel
        accessable_users: t.List[UserModel] = Field(default=[])

        class Config:
            module: str = "default"
            name: str = "Memo"

    class CommentModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        created_by: UserModel
        memo: MemoModel
        content: str

        class Config:
            module: str = "default"
            name: str = "Comment"

    validator = SchemaValidator(
        edgedb_dsn,
        models={UserModel, MemoModel, CommentModel},
        tls_security="insecure",
        fail_fast=False,
        check_validation_rules=True,
    )

    try:
        assert await validator.validate() is True
    except ValidationError as e:
        print(e.errors)
        print(e.message)
        pytest.fail(e)
    finally:
        await validator.aclose()


@pytest.mark.asyncio
async def test_validator_with_invalid_classes(edgedb_dsn):
    class UserModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        email: str
        password: str
        name: str = Field(min_length=3)

        class Config:
            module: str = "default"
            name: str = "User"

    class MemoModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        title: str
        content: str
        tags: t.List[str] = Field(default=[])

        created_by: UserModel
        accessable_users: t.List[UserModel] = Field(default=[])

        class Config:
            module: str = "default"
            name: str = "Memo"

    # This Class not inherits EdgeModel and has Invalid name.
    class InvalidCommentName:
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        created_by: UserModel
        memo: MemoModel
        content: str

    validator = SchemaValidator(
        edgedb_dsn,
        models={UserModel, MemoModel, InvalidCommentName},
        tls_security="insecure",
        fail_fast=False,
        check_validation_rules=True,
    )

    with pytest.raises(ValidationError):
        result = await validator.validate()
        assert result is False

    await validator.aclose()


@pytest.mark.asyncio
async def test_validator_with_invalid_edgemodels(edgedb_dsn):
    class UserModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        email: str
        password: str
        name: str = Field(min_length=3)

        class Config:
            module: str = "default"
            # changed type name to make invalid
            name: str = "Ussssser"

    class MemoModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        title: str
        content: str
        tags: t.List[str] = Field(default=[])

        created_by: UserModel
        accessable_users: t.List[UserModel] = Field(default=[])

        class Config:
            # changed module to make invalid
            module: str = "std"
            name: str = "Memo"

    class CommentModel(EdgeModel):
        id: uuid.UUID = Field(default=uuid.uuid1())
        updated_at: pendulum.DateTime = Field(default=pendulum.now())
        created_at: pendulum.DateTime = Field(None)
        deleted_at: t.Optional[pendulum.DateTime] = Field(default=None)
        deleted: bool = Field(default=False)

        created_by: UserModel
        memo: MemoModel
        content: str

        class Config:
            module: str = "default"
            name: str = "Comment"

    validator = SchemaValidator(
        edgedb_dsn,
        models={UserModel, MemoModel, CommentModel},
        tls_security="insecure",
        fail_fast=False,
        check_validation_rules=True,
    )

    with pytest.raises(ValidationError) as e:
        await validator.validate()

    await validator.aclose()
    assert len(e.value.errors) == 2
