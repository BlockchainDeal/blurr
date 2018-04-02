from datetime import datetime, timedelta
from typing import Any, List, Tuple

from blurr.core.data_group import DataGroup, DataGroupSchema
from blurr.core.errors import PrepareWindowMissingSessionsError
from blurr.core.evaluation import EvaluationContext
from blurr.core.schema_loader import SchemaLoader
from blurr.core.session_data_group import SessionDataGroup
from blurr.core.store import Key
from blurr.core.base import BaseItem


class WindowDataGroupSchema(DataGroupSchema):
    """
    Schema for WindowAggregate DataGroup.
    """
    ATTRIBUTE_WINDOW_VALUE = 'WindowValue'
    ATTRIBUTE_WINDOW_TYPE = 'WindowType'
    ATTRIBUTE_SOURCE = 'Source'

    def __init__(self, fully_qualified_name: str,
                 schema_loader: SchemaLoader) -> None:
        super().__init__(fully_qualified_name, schema_loader)
        self.window_value = self._spec[self.ATTRIBUTE_WINDOW_VALUE]
        self.window_type = self._spec[self.ATTRIBUTE_WINDOW_TYPE]
        self.source = self.schema_loader.get_schema_object(
            self._spec[self.ATTRIBUTE_SOURCE])


class _Window:
    """
    Represents a window on the pre-aggregated source data.
    """

    def __init__(self):
        self.view: List[SessionDataGroup] = []

    def __getattr__(self, item: str) -> List[Any]:
        return [getattr(session, item) for session in self.view]


class WindowDataGroup(DataGroup):
    """
    Manages the generation of WindowAggregate as defined in the schema.
    """

    def __init__(self, schema: WindowDataGroupSchema, identity: str,
                 evaluation_context: EvaluationContext) -> None:
        super().__init__(schema, identity, evaluation_context)
        self.window = _Window()

    def prepare_window(self, start_time: datetime) -> None:
        """
        Prepares window if any is specified.
        :param start_time: The anchor session start_time from where the window
        should be generated.
        """
        # evaluate window first which sets the correct window in the store
        store = self.schema.source.store
        if self.schema.window_type == 'day' or self.schema.window_type == 'hour':
            self.window.view = self._load_sessions(
                store.get_range(
                    Key(self.identity, self.schema.source.name, start_time),
                    Key(self.identity, self.schema.source.name,
                        self._get_end_time(start_time))))
        else:
            self.window.view = self._load_sessions(
                store.get_range(
                    Key(self.identity, self.schema.source.name, start_time),
                    None, self.schema.window_value))

        self._validate_view()

    def _validate_view(self):
        if self.schema.window_type == 'count' and len(self.window.view) != abs(
                self.schema.window_value):
            raise PrepareWindowMissingSessionsError(
                'Expecting {} but not found {} sessions'.format(
                    abs(self.schema.window_value), len(self.window.view)))

        if len(self.window.view) == 0:
            raise PrepareWindowMissingSessionsError(
                'No matching sessions found')

    # TODO: Handle end time which is beyond the expected range of data being
    # processed. In this case a PrepareWindowMissingSessionsError error should
    # be raised.
    def _get_end_time(self, start_time: datetime) -> datetime:
        """
        Generates the end time to be used for the store range query.
        :param start_time: Start time to use as an offset to calculate the end time
        based on the window type in the schema.
        :return:
        """
        if self.schema.window_type == 'day':
            return start_time + timedelta(days=self.schema.window_value)
        elif self.schema.window_type == 'hour':
            return start_time + timedelta(hours=self.schema.window_value)

    def _load_sessions(self,
                       sessions: List[Tuple[Key, Any]]) -> List[BaseItem]:
        """
        Converts [(Key, Session)] to [SessionDataGroup]
        :param sessions: List of (Key, Session) sessions.
        :return: List of SessionDataGroup
        """
        return [
            SessionDataGroup(self.schema.source, self.identity,
                             EvaluationContext()).restore(session)
            for (_, session) in sessions
        ]

    def evaluate(self) -> None:
        self.evaluation_context.local_context.add('source', self.window)
        super().evaluate()
