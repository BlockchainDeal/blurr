from typing import Dict, Any, List

from blurr.core.evaluation import Expression, EvaluationContext
from blurr.core.data_group import DataGroup, DataGroupSchema


class SessionDataGroupSchema(DataGroupSchema):
    """
    Data group that handles the session rollup aggregation
    """

    ATTRIBUTE_SPLIT = 'Split'

    def __init__(self, spec: Dict[str, Any]) -> None:
        super().__init__(spec)

    def validate(self, spec: Dict[str, Any]):
        """
        Overrides the Base Schema validation specifications to include validation for nested schema
        """
        # Validate base attributes first
        super().validate(spec)

        # Validate type specific attributes
        self.validate_required_attribute(spec, self.ATTRIBUTE_SPLIT)

    def load(self, spec: Dict[str, Any]) -> None:
        """
        Overrides base load to include loads for nested items
        """
        # Alter the spec to introduce the session start and end time implicitly handled fields
        spec[self.ATTRIBUTE_FIELDS][0:0] = self.build_predefined_fields_spec(
            spec[self.ATTRIBUTE_NAME])

        # Loading the base attributes first
        super().load(spec)

        # Load type specific attributes
        self.split: Expression = Expression(spec[
            self.ATTRIBUTE_SPLIT]) if self.ATTRIBUTE_SPLIT in spec else None

    @staticmethod
    def build_predefined_fields_spec(
            name_in_context: str) -> List[Dict[str, Any]]:
        """
        Constructs the spec for predefined fields that are to be included in the master spec prior to schema load
        :param name_in_context: Name of the current object in the context
        :return:
        """
        return [
            {
                'Name': 'start_time',
                'Type': 'datetime',
                'Value': (
                    'time if {data_group}.start_time is None else time '
                    'if time < {data_group}.start_time else {data_group}.start_time'
                ).format(data_group=name_in_context)
            },
            {
                'Name': 'end_time',
                'Type': 'datetime',
                'Value': (
                    'time if {data_group}.end_time is None else time '
                    'if time > {data_group}.end_time else {data_group}.end_time'
                ).format(data_group=name_in_context)
            },
        ]


class SessionDataGroup(DataGroup):
    """
    Manages the aggregates for session based roll-ups of streaming data
    """

    def __init__(self, schema: SessionDataGroupSchema,
                 evaluation_context: EvaluationContext) -> None:
        super(SessionDataGroup, self).__init__(schema, evaluation_context)

    @property
    def split_now(self) -> bool:
        # Check if current session is stale for the event being processed
        if self.schema.split is None:
            return False

        if self.start_time is None or self.end_time is None:
            return False

        if self.schema.split.evaluate(self.evaluation_context):
            return True

        return False

    def reset(self):
        self.__init__(self.schema, self.evaluation_context)