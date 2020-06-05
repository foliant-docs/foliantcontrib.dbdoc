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
      tab.OWNER,
      tab.TABLE_NAME,
      com.COMMENTS
    FROM all_tables tab
    LEFT JOIN USER_TAB_COMMENTS com
           ON tab.TABLE_NAME = com.TABLE_NAME
    WHERE 1 = 1
    {filters}
    ORDER BY tab.TABLE_NAME'''

    _filter_fields = {SCHEMA: 'tab.OWNER',
                      TABLE_NAME: 'tab.TABLE_NAME'}


class ColumnsQuery(QueryBase):

    base_query = '''SELECT
      col.TABLE_NAME,
      col.COLUMN_ID,
      col.COLUMN_NAME,
      col.NULLABLE,
      col.DATA_TYPE,
      col.DATA_DEFAULT,
      col.DATA_LENGTH,
      col.DATA_PRECISION,
      com.COMMENTS
    FROM user_tab_columns col
    JOIN all_tables tab
      ON col.TABLE_NAME = tab.TABLE_NAME
    LEFT JOIN user_col_comments com
           ON col.TABLE_NAME = com.TABLE_NAME
          AND col.COLUMN_NAME = com.COLUMN_NAME
    WHERE 1=1
    {filters}
    ORDER BY col.TABLE_NAME, col.COLUMN_ID'''

    _filter_fields = {SCHEMA: 'tab.OWNER',
                      TABLE_NAME: 'col.TABLE_NAME'}


class ForeignKeysQuery(QueryBase):

    base_query = '''
    SELECT
        c.OWNER,
        a.CONSTRAINT_NAME,
        a.TABLE_NAME,
        a.COLUMN_NAME,
        c.R_OWNER as F_OWNER,
        c_pk.TABLE_NAME as F_TABLE_NAME
    FROM all_cons_columns a
        JOIN all_constraints c
          ON a.OWNER = c.OWNER
         AND a.CONSTRAINT_NAME = c.CONSTRAINT_NAME
        JOIN all_constraints c_pk
          ON c.R_OWNER = c_pk.OWNER
         AND c.R_CONSTRAINT_NAME = c_pk.CONSTRAINT_NAME
    WHERE c.CONSTRAINT_TYPE = 'R'
    {filters}'''


class FunctionsQuery(QueryBase):

    base_query = """SELECT
        NAME,
        TYPE,
        OWNER,
        RTRIM(XMLAGG(XMLELEMENT(E,TEXT).EXTRACT('//text()') ORDER BY LINE).GetClobVal(),',') AS SOURCE
    FROM ALL_SOURCE
    WHERE TYPE in ('FUNCTION', 'PROCEDURE')
    {filters}
    GROUP BY NAME, TYPE, OWNER
    ORDER BY NAME"""

    _filter_fields = {SCHEMA: 'OWNER'}


class TriggersQuery(QueryBase):

    base_query = """SELECT
        tr.OWNER,
        tr.TRIGGER_NAME,
        tr.TRIGGER_TYPE,
        tr.TRIGGERING_EVENT,
        tr.TABLE_OWNER,
        tr.TABLE_NAME,
        tr.DESCRIPTION,
        tr.TRIGGER_BODY,
        (SELECT
            RTRIM(XMLAGG(XMLELEMENT(E,TEXT).EXTRACT('//text()') ORDER BY LINE).GetClobVal(),',') AS SOURCE
        FROM all_source
        WHERE TYPE = 'TRIGGER'
          AND owner = tr.owner
          AND name = tr.TRIGGER_NAME
        GROUP BY name, TYPE, owner) AS SOURCE
            FROM ALL_TRIGGERS tr
            WHERE 1=1
            {filters}
            ORDER BY TABLE_NAME, trigger_name"""

    _filter_fields = {SCHEMA: 'tr.OWNER'}


class ViewsQuery(QueryBase):

    base_query = """SELECT
        OWNER,
        VIEW_NAME,
        TEXT,
        TEXT_VC
    FROM ALL_VIEWS
    WHERE 1=1
    {filters}
    ORDER BY VIEW_NAME"""

    _filter_fields = {SCHEMA: 'OWNER'}
