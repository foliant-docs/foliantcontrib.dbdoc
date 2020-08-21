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
                     'not_eq': self._not_eq}

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
        return f"REGEXP_LIKE({field}, '{value}')"

    def _not_regex(self, field: str, value: str) -> str:
        return f"REGEXP_LIKE({field}, '{value}')"

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
      T.TABLE_SCHEMA,
      T.TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES T
    WHERE TABLE_TYPE = 'BASE TABLE'
    {filters}
    ORDER BY TABLE_SCHEMA, TABLE_NAME'''

    _filter_fields = {SCHEMA: 'SCHEMA_NAME',
                      TABLE_NAME: 'TABLE_NAME'}


class ColumnsQuery(QueryBase):

    base_query = '''SELECT
      c.TABLE_NAME,
      sc.COLUMN_ID,
      c.COLUMN_NAME,
      c.IS_NULLABLE,
      c.DATA_TYPE,
      c.COLUMN_DEFAULT,
      c.CHARACTER_MAXIMUM_LENGTH,
      c.NUMERIC_PRECISION,
      CAST(prop.value AS nvarchar(4000)) AS COMMENT
    FROM INFORMATION_SCHEMA.TABLES AS tbl
    INNER JOIN INFORMATION_SCHEMA.COLUMNS AS c ON c.TABLE_NAME = tbl.TABLE_NAME
    INNER JOIN sys.columns AS sc ON sc.object_id = object_id(tbl.table_schema + '.' + tbl.table_name)
        AND sc.NAME = c.COLUMN_NAME
    LEFT JOIN sys.extended_properties prop ON prop.major_id = sc.object_id
        AND prop.minor_id = sc.column_id
        AND prop.NAME = 'MS_Description'
    WHERE TABLE_TYPE = 'BASE TABLE'
    {filters}
    ORDER BY c.TABLE_NAME, sc.COLUMN_ID'''

    _filter_fields = {SCHEMA: 'tbl.SCHEMA_NAME',
                      TABLE_NAME: 'c.TABLE_NAME'}


class ForeignKeysQuery(QueryBase):

    base_query = '''SELECT
      s.name as SCHEMA_NAME,
      p.name as TABLE_NAME,
      pc.name as COLUMN_NAME,
      rs.name as REF_SCHEMA_NAME,
      r.name as REF_TABLE_NAME,
      rc.name as REF_COLUMN_NAME
    FROM sys.foreign_key_columns f
    JOIN sys.objects p
      ON p.object_id  = f.parent_object_id
    JOIN sys.schemas s
      ON p.schema_id = s.schema_id
    JOIN sys.columns pc
      ON pc.object_id = f.parent_object_id
      AND f.parent_column_id = pc.column_id
    JOIN sys.objects r
      ON r.object_id  = f.referenced_object_id
    JOIN sys.schemas rs
      ON r.schema_id = rs.schema_id
    JOIN sys.columns rc
      ON rc.object_id = f.referenced_object_id
      AND rc.column_id = f.referenced_column_id
    WHERE 1 = 1
    {filters}'''


class FunctionsQuery(QueryBase):

    base_query = '''SELECT
      o.name AS NAME,
      s.name AS SCHEMA_NAME,
      sm.definition AS DEFINITION
    FROM sys.sql_modules sm
    JOIN sys.objects o on sm.object_id = o.object_id
    JOIN sys.schemas s on o.schema_id = s.schema_id
    WHERE type_desc like '%FUNCTION%'
    {filters}
    ORDER BY NAME
    '''
    _filter_fields = {SCHEMA: 'SCHENA_NAME'}


class TriggersQuery(QueryBase):

    base_query = '''SELECT
      s.name AS TABLE_SCHEMA,
      syo.name AS TRIGGER_NAME,
      CONCAT(
          IIF(OBJECTPROPERTY(id, 'ExecIsAfterTrigger') = 1, 'AFTER ', ''),
          IIF(OBJECTPROPERTY(id, 'ExecIsInsteadOfTrigger') = 1, 'INSTEAD OF ', ''),
          IIF(OBJECTPROPERTY(id, 'ExecIsUpdateTrigger') = 1, 'UPDATE ', ''),
          IIF(OBJECTPROPERTY(id, 'ExecIsDeleteTrigger') = 1, 'DELETE ', ''),
          IIF(OBJECTPROPERTY(id, 'ExecIsInsertTrigger') = 1, 'INSERT ', '')
      ) AS TRIGGER_TYPE,
      OBJECT_NAME(parent_obj) AS TABLE_NAME,
      sm.definition AS DEFINITION,
      OBJECTPROPERTY(id, 'ExecIsTriggerDisabled') AS DISABLED
    FROM sysobjects  syo
    INNER JOIN sys.tables t
        ON syo.parent_obj = t.object_id
    INNER JOIN sys.schemas s
        ON t.schema_id = s.schema_id
    INNER JOIN sys.sql_modules sm
        ON sm.object_id = syo.id
    WHERE syo.type = 'TR'
    {filters}
    ORDER BY table_name, trigger_name'''

    _filter_fields = {SCHEMA: 'table_schema'}


class ViewsQuery(QueryBase):

    base_query = '''SELECT
      s.name AS SCHEMA_NAME,
      v.name AS VIEW_NAME,
      sm.definition AS DEFINITION
    FROM sys.views v
    JOIN sys.schemas s ON v.schema_id = s.schema_id
    JOIN sys.sql_modules sm ON v.object_id = sm.object_id
    WHERE type_desc = 'VIEW'
    {filters}
    ORDER BY VIEW_NAME
    '''

    _filter_fields = {SCHEMA: 'SCHEMA_NAME'}
