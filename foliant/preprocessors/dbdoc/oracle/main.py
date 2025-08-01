import os
from copy import deepcopy
from logging import getLogger

from .queries import ColumnsQuery
from .queries import ForeignKeysQuery
from .queries import FunctionsQuery
from .queries import TablesQuery
from .queries import TriggersQuery
from .queries import ViewsQuery
from ..base.main import LibraryNotInstalledError
from foliant.preprocessors.dbdoc.base.main import DBRendererBase
from foliant.utils import output

logger = getLogger('unbound.dbdoc.oracle')


class OracleRenderer(DBRendererBase):
    defaults = {
        'doc': True,
        'scheme': True,
        'host': 'localhost',
        'port': '1521',
        'dbname': 'orcl',
        'user': 'hr',
        'password': 'oracle',
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
        Connect to Oracle database using parameters from options.
        Save connection object into self.con.
        """
        try:
            import cx_Oracle
        except ModuleNotFoundError:
            raise LibraryNotInstalledError(
                'cx_Oracle not installed. Please run `pip3 install cx_Oracle` '
                'and make sure that Oracle Instant Client is installed on the machine'
            )

        logger.debug(
            f"Trying to connect: host={self.options['host']} port={self.options['port']}"
            f" dbname={self.options['dbname']}, user={self.options['user']} "
            f"password={self.options['password']}."
        )
        try:
            self.con = cx_Oracle.connect(
                f"{self.options['user']}/{self.options['password']}@"
                f"{self.options['host']}:{self.options['port']}/"
                f"{self.options['dbname']}",
                encoding='UTF-8',
                nencoding='UTF-8'
            )
        except cx_Oracle.Error as e:
            msg = f"\nOracle database connection error: {e}"
            if self.options['strict']:
                logger.error(msg)
                output(f"ERROR: {msg}")
                os._exit(1)
            else:
                logger.debug(f"{msg}. Skipping.")

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

    def collect_functions(self,
                          functions: list,
                          parameters: list) -> list:
        '''
        Parse function and parameter query results got from db and add 'parameters'
        key to each function filled with its parameters
        '''

        result = deepcopy(functions)
        for func in result:
            # get parameters for this function
            function_params = list(
                filter(
                    lambda x: x['specific_name'] == func['specific_name'], parameters
                )
            )
            func['parameters'] = function_params
        return result


def set_up_logger(logger_):
    '''Set up a global logger for functions in this module'''
    global logger
    logger = logger_.getChild(__package__.split('.')[-1])
