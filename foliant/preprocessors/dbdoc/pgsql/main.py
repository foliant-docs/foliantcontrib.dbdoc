import psycopg2

from copy import deepcopy
from logging import getLogger
from .queries import (TablesQuery, ColumnsQuery, ForeignKeysQuery, ViewsQuery,
                      FunctionsQuery, ParametersQuery, TriggersQuery)
from foliant.preprocessors.dbdoc.base.main import DBRendererBase

logger = getLogger('unbound.dbdoc.pgsql')


class PGSQLRenderer(DBRendererBase):
    defaults = {
        'doc': True,
        'scheme': True,
        'host': 'localhost',
        'port': '5432',
        'dbname': 'postgres',
        'user': 'postgres',
        'password': 'postgres',
        'components': [
            'tables',
            'views',
            'functions',
            'triggers'
        ]
    }
    module_name = __name__

    def connect(self):
        """
        Connect to PostgreSQL database using parameters from options.
        Save connection object into self.con.
        """
        logger.debug(
            f"Trying to connect: host={self.options['host']} port={self.options['port']}"
            f" dbname={self.options['dbname']}, user={self.options['user']} "
            f"password={self.options['password']}."
        )
        self.con = psycopg2.connect(
            f"host='{self.options['host']}' "
            f"port='{self.options['port']}' "
            f"dbname='{self.options['dbname']}' "
            f"user='{self.options['user']}'"
            f"password='{self.options['password']}'"
        )

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
            logger.debug(f'Functions keys query:\n\n {q_functions.sql}')
            functions = q_functions.run()

            q_parameters = ParametersQuery(self.con, filters)
            logger.debug(f'Parameters keys query:\n\n {q_parameters.sql}')
            parameters = q_parameters.run()

            # fill each function with its parameters

            result['functions'] = self.collect_functions(functions, parameters)

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
            table_columns = list(filter(lambda x: x['table_name'] == table['relname'],
                                        columns))
            for col in table_columns:
                # get foreign keys for this column
                fks_fltr = list(
                    filter(
                        lambda x: x['table_name'] == table['relname'] and
                        x['column_name'] == col['column_name'], fks
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
