import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.resource import ResourceDetail


def test_resource_detail_requires_payload_for_its_type():
    adapter = TypeAdapter(ResourceDetail)
    resource = adapter.validate_python(
        {
            "id": "res-1",
            "resource_type": "code",
            "title": "ROS2 publisher",
            "payload": {
                "language": "python",
                "code": "print('ok')",
                "description": "发布节点示例",
            },
            "media_url": None,
        }
    )
    assert resource.payload.language == "python"

    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "id": "res-2",
                "resource_type": "code",
                "title": "broken",
                "payload": {"markdown": "wrong payload"},
                "media_url": None,
            }
        )


def test_resource_detail_rejects_an_unknown_resource_type():
    adapter = TypeAdapter(ResourceDetail)

    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "id": "res-unknown",
                "resource_type": "slides",
                "title": "unsupported",
                "payload": {},
                "media_url": None,
            }
        )
