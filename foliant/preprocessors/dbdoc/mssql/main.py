import pyodbc

from copy import deepcopy
from jinja2 import Template
from pkg_resources import resource_filename
from foliant.preprocessors.utils.combined_options import CombinedOptions
from logging import getLogger
from .queries import (TablesQuery, ColumnsQuery, ForeignKeysQuery,
                      FunctionsQuery, TriggersQuery, ViewsQuery)

logger = getLogger('flt.dbdoc.pgsql')


def process(config, tag_options) -> str:
    defaults = {
        'doc': True,
        'scheme': True,
        'host': 'localhost',
        'port': '1433',
        'dbname': 'TestDB',
        'user': 'SA',
        'password': '<YourStrong@Passw0rd>',
        'driver': '{ODBC Driver 17 for SQL Server}',
        'components': [
            'tables',
            'functions',
            'triggers',
            'views'
        ]
    }
    options = CombinedOptions(
        {
            'config': config,
            'tag': tag_options
        },
        priority='tag',
        defaults=defaults
    )

    logger.debug(f'Config: {options}')

    con = connect(options)
    return gen_docs(options, con)


def connect(options: CombinedOptions):
    """
    Connect to Oracle database using parameters from options.
    Save connection object into self._con.

    options(CombinedOptions) — CombinedOptions object with options from tag
                               and config.
    """
    connection_string = (
        f"DRIVER={options['driver']};"
        f"SERVER={options['host']},{options['port']};"
        f"DATABASE={options['dbname']};"
        f"UID={options['user']};PWD={options['password']}"
    )
    logger.debug(
        f"Trying to connect: {connection_string}"
    )
    con = pyodbc.connect(connection_string)
    return con


def get_template(options: CombinedOptions, key: str, default_name: str):
    template_path = options.get(key)
    if template_path:
        return template_path
    else:
        return resource_filename(
            __name__,
            f"templates/{default_name}"
        )


def gen_docs(options: CombinedOptions, connection) -> str:
    data = collect_datasets(connection, options)

    docs = ''

    if options['doc']:
        docs += to_md(data, get_template(options, 'doc_template', 'doc.j2'))
    if options['scheme']:
        docs += '\n\n' + to_diag(data, get_template(options, 'scheme_template', 'scheme.j2'))
    return docs


def collect_datasets(connection,
                     options: CombinedOptions) -> dict:

    result = {}
    filters = options.get('filters', {})
    components = options['components']

    if 'tables' in components:
        q_tables = TablesQuery(connection, filters)
        logger.debug(f'Tables query:\n\n {q_tables.sql}')
        tables = q_tables.run()

        q_columns = ColumnsQuery(connection, filters)
        logger.debug(f'Columns query:\n\n {q_columns.sql}')
        columns = q_columns.run()

        q_fks = ForeignKeysQuery(connection, filters)
        logger.debug(f'Foreign keys query:\n\n {q_fks.sql}')
        fks = q_fks.run()

        # fill each table with columns and foreign keys
        result['tables'] = collect_tables(tables, columns, fks)

    if 'views' in components:
        q_views = ViewsQuery(connection, filters)
        logger.debug(f'Views query:\n\n {q_views.sql}')
        result['views'] = q_views.run()

    if 'functions' in components:
        q_functions = FunctionsQuery(connection, filters)
        logger.debug(f'Functions query:\n\n {q_functions.sql}')
        result['functions'] = q_functions.run()

    if 'triggers' in components:
        q_triggers = TriggersQuery(connection, filters)
        logger.debug(f'Triggers query:\n\n {q_triggers.sql}')
        result['triggers'] = q_triggers.run()

    return result


def collect_tables(tables: list,
                   columns: list,
                   fks: list) -> list:
    '''
    Parse table and column query results got from db and:

    - add 'columns' attribute to each table row with list of table columns;
    - add 'foreign_keys' attribute to each column with list of fks if it is a
      forign key column.

    returns transformed list of tables.
    '''

    result = deepcopy(tables)
    for table in result:
        # get columns for this table
        table_columns = list(filter(lambda x: x['TABLE_NAME'] == table['TABLE_NAME'],
                                    columns))
        for col in table_columns:
            # get foreign keys for this column
            fks_fltr = list(
                filter(
                    lambda x: x['TABLE_NAME'] == table['TABLE_NAME']
                    and x['COLUMN_NAME'] == col['COLUMN_NAME'], fks
                )
            )
            col['foreign_keys'] = fks_fltr
        table['columns'] = table_columns
    return result


def to_md(data: dict, template: str) -> str:
    with open(template, encoding='utf8') as f:
        template = Template(f.read())

    return template.render(**data)


def to_diag(data: dict, template: str) -> str:
    with open(template, encoding='utf8') as f:
        template = Template(f.read())

    return template.render(
        tables=data['tables']
    )
