from abc import ABCMeta

SCHEMA = 'schema'
TABLE_NAME = 'table_name'


class QueryBase(metaclass=ABCMeta):

    base_query = ''

    _filter_fields = {}
    # sort_fields = {}

    def __init__(self,
                 con,
                 filters: dict = {}):
        self._con = con
        self._filters = self._resolve_filters(filters)

    def _resolve_filters(self, filters: dict) -> str:
        resolvers = {'in': self._in,
                     'not_in': self._not_in,
                     'eq': self._eq,
                     'not_eq': self._not_eq,
                     'regex': self._regex,
                     'not_regex': self._not_regex}

        result = ''
        for key in filters:
            if key not in resolvers:
                continue
            result += self._get_predicate(filters[key], resolvers[key])
        return result

    def _get_predicate(self, filters: dict, func) -> str:
        filter_str = ''
        for filter_ in filters:
            if filter_ not in self._filter_fields:
                continue
            field = self._filter_fields[filter_]
            filter_str += f'AND ' + func(field, filters[filter_]) + '\n'
        return filter_str

    def _in(self, field: str, value: list) -> str:
        """filters = [('field_name', ['values',]), ...]"""

        in_str = ''
        values = value
        if type(values[0]) == str:
            values = [f"'{v}'" for v in value]
        in_str = ', '.join(values)
        return f'{field} IN ({in_str})'

    def _not_in(self, field: str, value: list) -> str:
        """filters = [('field_name', ['values',]), ...]"""

        in_str = ''
        values = value
        if type(values[0]) == str:
            values = [f"'{v}'" for v in value]
        in_str = ', '.join(values)
        return f'{field} NOT IN ({in_str})'

    def _regex(self, field: str, value: str) -> str:
        return f"{field} REGEXP '{value}'"

    def _not_regex(self, field: str, value: str) -> str:
        return f"{field} NOT REGEXP '{value}'"

    def _eq(self, field: str, value) -> str:
        if type(value) == str:
            value = f"'{value}'"
        return f"{field} = {value}"

    def _not_eq(self, field: str, value: str) -> str:
        if type(value) == str:
            value = f"'{value}'"
        return f"{field} != {value}"

    def _get_rows(self, sql) -> list:
        """Run query from sql param and return a list of dicts key=column name,
        value = field value"""
        self._con.query(sql)
        result = []
        query = self._con.store_result()
        keys = tuple((d[0] for d in query.describe()))
        for row in query.fetch_row(0):
            row_dict = {}
            for i in range(len(keys)):
                row_dict[keys[i]] = row[i].decode() if row[i] else ''
            result.append(row_dict)
        return result

    @property
    def sql(self):
        return self.base_query.format(filters=self._filters)

    def run(self):
        return self._get_rows(self.sql)


class TablesQuery(QueryBase):

    base_query = '''SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    TABLE_COMMENT
    FROM information_schema.tables
    WHERE TABLE_TYPE  = 'BASE TABLE'
    {filters}
    ORDER BY TABLE_NAME'''

    _filter_fields = {SCHEMA: 'TABLE_SCHEMA',
                      TABLE_NAME: 'TABLE_NAME'}


class ColumnsQuery(QueryBase):

    base_query = '''SELECT
        c.TABLE_NAME,
        c.COLUMN_NAME,
        c.ORDINAL_POSITION,
        c.IS_NULLABLE,
        c.DATA_TYPE,
        c.COLUMN_DEFAULT,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.NUMERIC_PRECISION,
        c.COLUMN_COMMENT
    FROM information_schema.tables t
    JOIN information_schema.`COLUMNS` c
      ON c.TABLE_SCHEMA = t.TABLE_SCHEMA
     AND c.TABLE_NAME =t.TABLE_NAME
    WHERE t.TABLE_TYPE = 'BASE TABLE'
    {filters}
    ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION'''

    _filter_fields = {SCHEMA: 'c.TABLE_SCHEMA',
                      TABLE_NAME: 'c.TABLE_NAME'}


class ForeignKeysQuery(QueryBase):

    base_query = '''SELECT
        CONSTRAINT_SCHEMA,
        CONSTRAINT_NAME,
        TABLE_NAME,
        COLUMN_NAME,
        REFERENCED_TABLE_SCHEMA,
        REFERENCED_TABLE_NAME,
        REFERENCED_COLUMN_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE REFERENCED_COLUMN_NAME IS NOT NULL
    {filters}'''


class FunctionsQuery(QueryBase):

    base_query = """SELECT
        ROUTINE_NAME,
        ROUTINE_TYPE,
        ROUTINE_SCHEMA,
        ROUTINE_DEFINITION
    FROM information_schema.ROUTINES r
    WHERE 1=1
    {filters}
    ORDER BY ROUTINE_NAME"""

    _filter_fields = {SCHEMA: 'ROUTINE_SCHEMA'}


class TriggersQuery(QueryBase):

    base_query = """SELECT
        TRIGGER_SCHEMA,
        TRIGGER_NAME,
        ACTION_TIMING,
        EVENT_MANIPULATION,
        EVENT_OBJECT_SCHEMA,
        EVENT_OBJECT_TABLE,
        ACTION_STATEMENT
    FROM information_schema.TRIGGERS t
    WHERE 1=1
    {filters}
    ORDER BY TRIGGER_SCHEMA, TRIGGER_NAME"""

    _filter_fields = {SCHEMA: 'TRIGGER_SCHEMA'}


class ViewsQuery(QueryBase):

    base_query = """SELECT
        TABLE_SCHEMA,
        TABLE_NAME,
        VIEW_DEFINITION,
        IS_UPDATABLE
    FROM information_schema.VIEWS v
    WHERE 1=1
    {filters}
    ORDER BY TABLE_SCHEMA, TABLE_NAME"""

    _filter_fields = {SCHEMA: 'TABLE_SCHEMA'}
