from unittest import TestCase
from unittest.mock import patch
from foliant_test.preprocessor import PreprocessorTestFramework

class TestDbdocPostgres(TestCase):
    """Postgres tests"""
    def setUp(self):
        self.ptf = PreprocessorTestFramework('dbdoc')
        self.ptf.options = {}

    def test_simple_documentation_pgsql(self):
        """pgsql test"""
        self.ptf.options = {
            'dbms': 'pgsql',
            'host': 'testdb',
            'dbname': 'testdb',
            'user': 'postgres',
            'password': 'password',
            'port': 5432,
            'doc': True,
            'scheme': False,
            'filters':{
                'eq':
                    {'table_name':'users'},
            },
            'components':[
                'tables'
            ]
        }

        input_files = {
            'index.md': '# Database Documentation\n\n<pgsql></pgsql>'
        }
        expected_files = {
            'index.md': '''# Database Documentation\n\n
# Tables


## users



column | nullable | type | descr | fkey
------ | -------- | ---- | ----- | ----
id | NO | integer |  |
name | YES | character varying |  |
email | YES | character varying |  |

'''
        }

        self.ptf.test_preprocessor(
            input_mapping=input_files,
            expected_mapping=expected_files
        )
    def test_strict_pgsql(self):
        """pgsql test strict mode"""
        self.ptf.options = {
            'dbms': 'pgsql',
            'host': 'invalid-host-name',
            'dbname': 'testdb',
            'user': 'postgres',
            'password': 'password',
            'port': 5432,
            'strict': True
        }

        input_files = {
            'index.md': '# Database Documentation\n\n<pgsql></pgsql>'
        }

        with patch('os._exit') as mock_exit:
            result = self.ptf.test_preprocessor(
                input_mapping=input_files,
                expected_mapping=input_files
            )
        mock_exit.assert_called_once_with(1)
