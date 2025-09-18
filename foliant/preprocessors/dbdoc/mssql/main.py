import os
from copy import deepcopy
from logging import getLogger

from ..base.main import LibraryNotInstalledError
from .queries import ColumnsQuery
from .queries import ForeignKeysQuery
from .queries import FunctionsQuery
from .queries import TablesQuery
from .queries import TriggersQuery
from .queries import ViewsQuery
from foliant.preprocessors.dbdoc.base.main import DBRendererBase
from foliant.utils import output


logger = getLogger('unbound.dbdoc.mssql')


class MSSQLRenderer(DBRendererBase):
    defaults = {
        'doc': True,
        'scheme': True,
        'host': 'localhost',
        'port': '1433',
        'dbname': 'mssql',
        'user': 'SA',
        'password': '<YourStrong@Passw0rd>',
        'driver': '{ODBC Driver 17 for SQL Server}',
        'trusted_connection': False,
        'components': [
            'tables',
            'functions',
            'triggers',
            'views'
        ],
        'strict': False
    }
    module_name = __name__

    def connect(self):
        """
        Connect to MS SQL database using parameters from options.
        Save connection object into self.con.
        """
        try:
            import pyodbc
        except ModuleNotFoundError:
            raise LibraryNotInstalledError(
                'pyodbc not installed. Please run `pip3 install pyodbc` '
                'and make sure that MS SQL Server is installed on the machine'
            )

        try:
            if self.options['trusted_connection']:
                connection_string = (
                    f"DRIVER={self.options['driver']};"
                    f"SERVER={self.options['host']},{self.options['port']};"
                    f"DATABASE={self.options['dbname']};Trusted_Connection=yes"
                )

            else:
                connection_string = (
                    f"DRIVER={self.options['driver']};"
                    f"SERVER={self.options['host']},{self.options['port']};"
                    f"DATABASE={self.options['dbname']};"
                    f"UID={self.options['user']};PWD={self.options['password']}"
                )
            logger.debug(
                f"Trying to connect: {connection_string}"
            )
            self.con = pyodbc.connect(connection_string)
            logger.debug("Successfully connected to the database")
        except pyodbc.Error as e:
            msg = f"\MS SQL database database connection error: {e}"
            if self.options['strict']:
                logger.error(msg)
                output(f'ERROR: {msg}. Exit.')
                os._exit(1)
            else:
                logger.debug(f'{msg}. Skipping.')

    def collect_datasets(self) -> dict:

        result = {}
        filters = self.options.get('filters', {})
        components = self.options['components']

        if 'tables' in components:
            q_tables = TablesQuery(self.con, filters)
            logger.debug(f'Tables query:\n\n {q_tables.sql}')
            tables = q_tables.run()

            q_columns = ColumnsQuery(self.con, filters)
            logger.debug(f'Columns query:\n\n {q_columns.sql}')
            columns = q_columns.run()

            q_fks = ForeignKeysQuery(self.con, filters)
            logger.debug(f'Foreign keys query:\n\n {q_fks.sql}')
            fks = q_fks.run()

            # fill each table with columns and foreign keys
            result['tables'] = self.collect_tables(tables, columns, fks)

        if 'views' in components:
            q_views = ViewsQuery(self.con, filters)
            logger.debug(f'Views query:\n\n {q_views.sql}')
            result['views'] = q_views.run()

        if 'functions' in components:
            q_functions = FunctionsQuery(self.con, filters)
            logger.debug(f'Functions query:\n\n {q_functions.sql}')
            result['functions'] = q_functions.run()

        if 'triggers' in components:
            q_triggers = TriggersQuery(self.con, filters)
            logger.debug(f'Triggers query:\n\n {q_triggers.sql}')
            result['triggers'] = q_triggers.run()

        return result

    def collect_tables(self,
                       tables: list,
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


def set_up_logger(logger_):
    '''Set up a global logger for functions in this module'''
    global logger
    logger = logger_.getChild(__package__.split('.')[-1])
