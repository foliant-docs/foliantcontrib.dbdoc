from unittest import TestCase
from unittest.mock import patch
from foliant_test.preprocessor import PreprocessorTestFramework

class TestDbdocMySQL(TestCase):
    """MySQL tests"""
    def setUp(self):
        self.ptf = PreprocessorTestFramework('dbdoc')
        self.ptf.options = {}

    def test_simple_documentation_mysql(self):
        """mysql test"""
        self.ptf.options = {
            'dbms': 'mysql',
            'host': 'testdb',
            'dbname': 'testdb',
            'user': 'testuser',
            'password': 'testpassword',
            'port': 3306,
            'doc': True,
            'scheme': False,
            'filters':{
                'eq': {'table_name':'users'},
            },
            'components':['tables']
        }

        input_files = {
            'index.md': '# Database Documentation\n\n<mysql></mysql>'
        }
        expected_files = {
            'index.md': '''# Database Documentation\n\n


# Tables


## users



column | nullable | type | descr | fkey
------ | -------- | ---- | ----- | ----
id | NO | int |  |
name | YES | varchar |  |
email | YES | varchar |  |








'''
        }

        self.ptf.test_preprocessor(
            input_mapping=input_files,
            expected_mapping=expected_files
        )

    def test_strict_mysql(self):
        """mysql  test strict mode"""
        self.ptf.options = {
            'dbms': 'mysql',
            'host': 'invalid-host-name',
            'dbname': 'testdb',
            'user': 'testuser',
            'password': 'testpassword',
            'port': 3306,
            'strict': True
        }

        input_files = {
            'index.md': '# Database Documentation\n\n<mysql></mysql>'
        }

        with patch('os._exit') as mock_exit:
            result = self.ptf.test_preprocessor(
                input_mapping=input_files,
                expected_mapping=input_files
            )
        mock_exit.assert_called_once_with(1)
