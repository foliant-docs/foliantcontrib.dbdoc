# tests/test_dbdoc_basic.py
from unittest import TestCase
from foliant_test.preprocessor import PreprocessorTestFramework

class TestDbdocBasic(TestCase):
    """Basic tests"""
    def setUp(self):
        self.ptf = PreprocessorTestFramework('dbdoc')
        self.ptf.options = {}

    def test_simple_documentation(self):
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
        # Входные файлы
        input_files = {
            'index.md': '# Database Documentation\n\n<pgsql></pgsql>'
        }

        # Ожидаемые файлы с функцией проверки
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

        # Запускаем тест
        self.ptf.test_preprocessor(
            input_mapping=input_files,
            expected_mapping=expected_files
        )
