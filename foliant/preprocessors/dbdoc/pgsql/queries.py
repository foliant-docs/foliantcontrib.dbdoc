import psycopg2
from abc import ABCMeta

SCHEMA = 'schema'
TABLE_NAME = 'table_name'


class QueryBase(metaclass=ABCMeta):

    base_query = ''

    _filter_fields = {}
    # sort_fields = {}

    def __init__(self,
                 con: psycopg2.extensions.connection,
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
            filter_str += f'AND {field} ' + func(filters[filter_]) + '\n'
        return filter_str

    def _in(self, value: list) -> str:
        """filters = [('field_name', ['values',]), ...]"""

        in_str = ''
        values = value
        if type(values[0]) == str:
            values = [f"'{v}'" for v in value]
        in_str = ', '.join(values)
        return f'IN ({in_str})'

    def _not_in(self, value: list) -> str:
        """filters = [('field_name', ['values',]), ...]"""

        in_str = ''
        values = value
        if type(values[0]) == str:
            values = [f"'{v}'" for v in value]
        in_str = ', '.join(values)
        return f'NOT IN ({in_str})'

    def _regex(self, value: str) -> str:
        return f"~ '{value}'"

    def _not_regex(self, value: str) -> str:
        return f"!~ '{value}'"

    def _eq(self, value) -> str:
        if type(value) == str:
            value = f"'{value}'"
        return f"= {value}"

    def _not_eq(self, value: str) -> str:
        if type(value) == str:
            value = f"'{value}'"
        return f"!= {value}"

    def _get_rows(self, sql) -> list:
        """Run query from sql param and return a list of dicts key=column name,
        value = field value"""
        cur = self._con.cursor()
        cur.execute(sql)
        result = []
        keys = tuple((d[0] for d in cur.description))
        for row in cur.fetchall():
            row_dict = {}
            for i in range(len(keys)):
                row_dict[keys[i]] = row[i] or ''
            result.append(row_dict)
        return result

    @property
    def sql(self):
        return self.base_query.format(filters=self._filters)

    def run(self):
        return self._get_rows(self.sql)


class TablesQuery(QueryBase):

    base_query = '''SELECT
      st.schemaname,
      st.relname,
      pd.description
    FROM pg_catalog.pg_statio_all_tables AS st
    LEFT JOIN pg_catalog.pg_description pd
           ON st.relid = pd.objoid
          AND pd.objsubid = 0
    WHERE 1 = 1
    {filters}
    ORDER BY st.relname'''

    _filter_fields = {SCHEMA: 'schemaname',
                      TABLE_NAME: 'st.relname'}


class ColumnsQuery(QueryBase):

    base_query = '''SELECT
      c.table_name,
      c.ordinal_position,
      c.column_name,
      c.is_nullable,
      c.data_type,
      c.column_default,
      c.character_maximum_length,
      c.numeric_precision,
      pd.description
    FROM information_schema.columns c
    JOIN pg_catalog.pg_statio_all_tables st
      ON st.schemaname = c.table_schema
     AND st.relname = c.table_name
    LEFT JOIN pg_catalog.pg_description pd
           ON pd.objoid = st.relid
          AND pd.objsubid = c.ordinal_position
    WHERE 1=1
    {filters}
    ORDER BY c.table_name, c.ordinal_position'''

    _filter_fields = {SCHEMA: 'c.table_schema',
                      TABLE_NAME: 'c.table_name'}


class ForeignKeysQuery(QueryBase):

    base_query = '''SELECT
        tc.table_schema,
        tc.constraint_name,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM
        information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
    WHERE constraint_type = 'FOREIGN KEY'
    {filters}'''


class FunctionsQuery(QueryBase):

    base_query = """SELECT
        r.routine_name,
        r.specific_name,
        r.data_type,
        r.routine_definition,
        r.external_language,
        pd.description
    FROM information_schema.routines r
    JOIN pg_catalog.pg_namespace n ON r.routine_schema = n.nspname
    JOIN pg_catalog.pg_proc pgp on pgp.pronamespace = n.oid and pgp.proname = r.routine_name
    LEFT JOIN pg_catalog.pg_description pd
        on pd.objoid = pgp.oid
    WHERE 1=1
    {filters}
    ORDER BY routine_name"""

    _filter_fields = {SCHEMA: 'routine_schema'}


class ParametersQuery(QueryBase):

    base_query = """SELECT
        specific_name,
        parameter_name,
        parameter_mode,
        data_type,
        parameter_default
    FROM information_schema.parameters
    WHERE 1=1
    {filters}"""

    _filter_fields = {SCHEMA: 'specific_schema'}


class TriggersQuery(QueryBase):

    base_query = """SELECT
       event_object_table,
       trigger_name,
       event_manipulation,
       trigger_schema,
       action_timing,
       action_orientation,
       action_statement
    FROM information_schema.triggers
    WHERE 1=1
    {filters}
    ORDER BY event_object_table, trigger_name"""

    _filter_fields = {SCHEMA: 'trigger_schema'}
