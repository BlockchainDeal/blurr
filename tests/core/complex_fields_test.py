from typing import Dict, Any

from pytest import fixture

from blurr.core.complex_fields import Map
from blurr.core.data_group import DataGroup, DataGroupSchema
from blurr.core.evaluation import EvaluationContext
from blurr.core.schema_loader import SchemaLoader
from blurr.core.variable_data_group import VariableDataGroup, \
    VariableDataGroupSchema

# Test custom functions implemented for complex fields


def test_map_set():
    sample = Map()

    assert 'key' not in sample
    assert sample.set('key', 'value') is sample
    assert sample.get('key') == 'value'


def test_map_increment():
    sample = Map()

    assert 'key' not in sample
    assert sample.increment('key') is sample
    assert sample['key'] == 1
    assert sample.increment('key', 100) is sample
    assert sample.get('key') == 101


# Test the Complex object evaluation


@fixture(scope='module')
def data_group_schema_spec() -> Dict[str, Any]:
    return {
        'Type': 'ProductML:DTC:DataGroup:VariableAggregate',
        'Name': 'test',
        'Fields': [{
            'Name': 'map_field',
            'Type': 'map',
            'Value': 'test.map_field.set("set", "value").increment("incr", 10).update({"update": "value"})'
        }, {
            'Name': 'list_field',
            'Type': 'list',
            'Value': 'test.list_field.append(1).insert(0, 0).extend([2, 3]).remove(3)'
        }, {
            'Name': 'set_field',
            'Type': 'set',
            'Value': 'test.set_field.add(1).copy().union({2, 3}).update({3, 4, 5}).discard(0).remove(1).intersection({2, 4, 5}).symmetric_difference_update({4, 6})'
        }]
    }


@fixture(scope='module')
def schema_loader() -> SchemaLoader:
    return SchemaLoader()


@fixture(scope='module')
def data_group_schema(
        schema_loader: SchemaLoader,
        data_group_schema_spec: Dict[str, Any]) -> DataGroupSchema:
    return VariableDataGroupSchema(
        schema_loader.add_schema(data_group_schema_spec), schema_loader)


@fixture
def data_group(data_group_schema: DataGroupSchema) -> DataGroup:
    context = EvaluationContext()

    dg = VariableDataGroup(
        schema=data_group_schema, identity="12345", evaluation_context=context)
    context.global_add('test', dg)

    return dg


def test_field_evaluation(data_group: DataGroup) -> None:
    assert len(data_group.map_field) == 0
    assert len(data_group.set_field) == 0
    assert len(data_group.list_field) == 0

    data_group.evaluate()

    assert len(data_group.map_field) == 3
    assert data_group.map_field['incr'] == 10
    assert data_group.map_field['set'] == 'value'
    assert data_group.map_field['update'] == 'value'

    assert len(data_group.set_field) == 3
    assert data_group.set_field == {2, 5, 6}

    assert len(data_group.list_field) == 3
    assert data_group.list_field == [0, 1, 2]