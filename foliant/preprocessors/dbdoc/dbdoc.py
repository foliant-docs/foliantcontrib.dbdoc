'''
Preprocessor for Foliant documentation authoring tool.
Generates documentation from PostgreSQL database structure,
'''

from foliant.preprocessors.utils.preprocessor_ext import BasePreprocessorExt
from foliant.preprocessors.utils.preprocessor_ext import allow_fail

from .mssql.main import MSSQLRenderer
from .mssql.main import set_up_logger as set_up_logger_mssql
from .mysql.main import MySQLRenderer
from .mysql.main import set_up_logger as set_up_logger_mysql
from .oracle.main import OracleRenderer
from .oracle.main import set_up_logger as set_up_logger_oracle
from .pgsql.main import PGSQLRenderer
from .pgsql.main import set_up_logger as set_up_logger_pgsql


class Preprocessor(BasePreprocessorExt):
    tags = ('pgsqldoc', 'dbdoc', 'pgsql', 'oracle', 'sqlserver', 'mysql')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = self.logger.getChild('dbdoc')
        set_up_logger_pgsql(self.logger)
        set_up_logger_oracle(self.logger)
        set_up_logger_mssql(self.logger)
        set_up_logger_mysql(self.logger)

        self.logger.debug(f'Preprocessor inited: {self.__dict__}')

    @allow_fail()
    def process_tag(self, match) -> str:
        dbms_class_map = {
            'pgsql': PGSQLRenderer,
            'pgsqldoc': PGSQLRenderer,
            'oracle': OracleRenderer,
            'sqlserver': MSSQLRenderer,
            'mysql': MySQLRenderer
        }
        dbms = match.group('tag')
        tag_options = self.get_options(match.group('options'))

        if dbms == 'dbdoc':
            dbms = tag_options.get('dbms', self.options.get('dbms'))
            if not dbms or dbms not in dbms_class_map:
                raise RuntimeError('Please supply a valid dbms name in the dbms parameter. '
                                   f'Supported values: {list(dbms_class_map.keys())}')
        renderer = dbms_class_map[dbms](self.options)
        return renderer.process(tag_options)

    def apply(self):
        self._process_tags_for_all_files(func=self.process_tag)

        self.logger.info('Preprocessor applied')
