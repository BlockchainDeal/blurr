from blurr.core.evaluation import Context
from blurr.core.group import Group, GroupSchema


class SessionGroupSchema(GroupSchema):
    def __init__(self, schema: dict) -> None:
        self.split = schema['Split']
        schema['Fields'][0:0] = self.get_predefined_fields(schema['Name'])
        super(SessionGroupSchema, self).__init__(schema)

    @staticmethod
    def get_predefined_fields(name):
        return [
            {
                'Name': 'start_time',
                'Type': 'datetime',
                'Value': ('time if ' + name +
                          '.start_time is None else time if time < ' + name +
                          '.start_time else ' + name + '.start_time')
            },
            {
                'Name': 'end_time',
                'Type': 'datetime',
                'Value': ('time if ' + name +
                          '.end_time is None else time if time > ' + name +
                          '.end_time else ' + name + '.end_time')
            },
        ]


class StaleSessionError(Exception):
    pass


class SessionGroup(Group):
    def __init__(self, schema: SessionGroupSchema,
                 global_context: Context) -> None:
        super(SessionGroup, self).__init__(schema, global_context)

    def evaluate(self) -> None:
        if self.start_time is not None and self.end_time is not None:
            if not self.schema.split or self.evaluate_expr(
                    self.schema.split):
                raise StaleSessionError()

        super(SessionGroup, self).evaluate()

    def split(self):
        pass
        # TODO Flush the current session to store
