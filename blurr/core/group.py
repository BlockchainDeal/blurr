from typing import Any, Dict
from blurr.core.interpreter import Interpreter
from blurr.core.field import Field, FieldSchema
from blurr.core.base import BaseItem, BaseSchema


class GroupSchema(BaseSchema):
    def __init__(self, schema: dict) -> None:
        super().__init__(schema)
        self.fields = {s['Name']: FieldSchema(s) for s in schema['Fields']}


class Group(BaseItem):
    def __init__(self, schema: GroupSchema) -> None:
        super().__init__(schema)
        self._fields: Dict[str, Field] = {
            name: Field(field_schema)
            for name, field_schema in schema.fields
        }

    def initialize(self, field_values: Dict[str, Any]) -> None:
        for name, value in field_values:
            self.fields[name].initialize(value)

    def changes(self) -> Any:
        return {name: field.changes() for name, field in self.fields}

    def evaluate(self, interpreter: Interpreter) -> None:
        if self.should_evaluate(interpreter):
            for _, field in self.fields:
                field.evaluate(interpreter)

    def __getattr__(self, item):
        if item in self._fields:
            return self._fields[item].value

        self.__getattribute__(item)

    @property
    def name(self):
        return self._schema.name

    @property
    def fields(self):
        return self.fields
