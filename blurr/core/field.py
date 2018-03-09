from typing import Dict, Any

from blurr.core.base import BaseSchema, BaseItem, BaseType
from blurr.core.evaluation import Context, Expression
from blurr.core.loader import TypeLoader


class FieldSchema(BaseSchema):
    """
    An individual field schema.
        1. Field Schema must be defined inside a Group
        2. Contain the attributes:
            a. Name (inherited from base)
            b. Type (inherited from base)
            c. Value (required)
            d. Filter (inherited from base)
    """

    # Field Name Definitions
    FIELD_VALUE = 'Value'

    def __init__(self, spec: Dict[str, Any]) -> None:
        super().__init__(spec)

    def validate(self, spec: Dict[str, Any]) -> None:
        self.validate_required_attribute(spec, self.FIELD_VALUE)

    def load(self, spec: Dict[str, Any]) -> None:
        self.type: BaseType = TypeLoader.load_type(spec[self.FIELD_TYPE])
        self.value: Expression = Expression(spec[self.FIELD_VALUE])


class Field(BaseItem):
    def __init__(self, schema: FieldSchema, global_context: Context,
                 local_context: Context) -> None:
        super().__init__(schema, global_context, local_context)
        self._initial_value = None
        self._value = None

    def initialize(self, value) -> None:
        self._initial_value = value
        self._value = value

    def evaluate(self) -> None:
        new_value = None
        if self.should_evaluate:
            new_value = self.value.evaluate()

        if not self.schema.type.is_type_of(new_value):
            # TODO Give more meaningful error name
            raise ValueError('Type mismatch')

        self._value = new_value

    @property
    def name(self):
        return self.schema.name

    @property
    def value(self):
        return self._value if self._value else self.schema.type.default

    @property
    def items(self):
        return {self.name, self}

    @property
    def export(self):
        return self.value
