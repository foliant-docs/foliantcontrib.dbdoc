'''
Preprocessor for Foliant documentation authoring tool.
Generates documentation from PostgreSQL database structure,
'''

from foliant.preprocessors.utils.preprocessor_ext import (BasePreprocessorExt,
                                                          allow_fail)

from .pgsql.main import process as process_pgsql
from .oracle.main import process as process_oracle


class Preprocessor(BasePreprocessorExt):
    tags = ('pgsqldoc', 'dbdoc', 'pgsql', 'oracle')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = self.logger.getChild('dbdoc')

        self.logger.debug(f'Preprocessor inited: {self.__dict__}')

    @allow_fail()
    def process_tag(self, match) -> str:
        dbms_func = {
            'pgsql': process_pgsql,
            'pgsqldoc': process_pgsql,
            'oracle': process_oracle
        }
        dbms = match.group('tag')
        tag_options = self.get_options(match.group('options'))

        if dbms == 'dbdoc':
            dbms = tag_options.get('dbms', self.options.get('dbms'))
            if not dbms or dbms not in dbms_func:
                raise RuntimeError('Please supply a valid dbms name in the dbms parameter. '
                                   f'Supported values: {list(dbms_func.keys())}')
        return dbms_func[dbms](self.options, tag_options)

    def apply(self):
        self._process_tags_for_all_files(func=self.process_tag)

        self.logger.info('Preprocessor applied')
