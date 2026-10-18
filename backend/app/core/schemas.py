from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for API schemas: snake_case in Python, camelCase on the wire (api.md)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
