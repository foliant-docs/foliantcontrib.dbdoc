import psycopg2
from unittest import TestCase
from unittest.mock import Mock, patch, call, DEFAULT
from pathlib import Path
from pgsqldoc.pgsqldoc import Preprocessor
from foliant.preprocessors.utils.combined_options import CombinedOptions


class TestPreprocessorDB(TestCase):
    def setUp(self):
        self.preprocessor = Mock()
        self.options = {'host': 'host',
                        'port': 'port',
                        'dbname': 'dbname',
                        'user': 'user',
                        'password': 'password'}
        self.connect_string = f"host='{self.options['host']}' "\
                              f"port='{self.options['port']}' "\
                              f"dbname='{self.options['dbname']}' "\
                              f"user='{self.options['user']}'"\
                              f"password='{self.options['password']}'"

    def test_connect_success(self):
        with patch('pgsqldoc.pgsqldoc.psycopg2') as mock:
            Preprocessor._connect(self.preprocessor, self.options)
            mock.assert_has_calls([call.connect(self.connect_string)])
            self.assertIsNotNone(self.preprocessor._con)

    def test_connect_fail(self):
        psycopg2_mock = Mock()
        psycopg2_mock.OperationalError = psycopg2.OperationalError
        psycopg2_mock.connect.side_effect = psycopg2.OperationalError()
        with patch.multiple('pgsqldoc.pgsqldoc',
                            psycopg2=psycopg2_mock,
                            output=DEFAULT) as mock:
            with self.assertRaises(psycopg2.OperationalError):
                Preprocessor._connect(self.preprocessor, self.options)
            psycopg2_mock.assert_has_calls([call.connect(self.connect_string)])
            self.assertTrue(mock['output'].called)
            self.assertIsNone(self.preprocessor._con)
            # logger was called 2 times: first 'Trying to connect'
            # second 'Failed to connect'
            self.assertEqual(self.preprocessor.logger.debug.call_count, 2)


class TestPreprocessorDefaultTemplates(TestCase):
    def setUp(self):
        self.preprocessor = Mock()
        self.preprocessor.project_path = Path('/project_path')

    def test_create_default_doc_template(self):
        options_dict = {'doc_template': 'doc',
                        'scheme_template': 'scheme'}
        options = CombinedOptions(options_dict,
                                  defaults={**options_dict,
                                            'scheme_template': 'modified'})
        mock_resource = Mock(side_effect=['doc_resource'])
        with patch.multiple('pgsqldoc.pgsqldoc',
                            copy_if_not_exists=DEFAULT,
                            resource_filename=mock_resource) as mocks:
            Preprocessor._create_default_templates(self.preprocessor, options)
            self.assertEqual(mocks['copy_if_not_exists'].mock_calls,
                             [call(self.preprocessor.project_path / options_dict['doc_template'],
                                   'doc_resource')])

    def test_create_default_scheme_template(self):
        options_dict = {'doc_template': 'doc',
                        'scheme_template': 'scheme'}
        options = CombinedOptions(options_dict,
                                  defaults={**options_dict,
                                            'doc_template': 'modified'})
        mock_resource = Mock(side_effect=['scheme_resource'])
        with patch.multiple('pgsqldoc.pgsqldoc',
                            copy_if_not_exists=DEFAULT,
                            resource_filename=mock_resource) as mocks:
            Preprocessor._create_default_templates(self.preprocessor, options)
            self.assertEqual(mocks['copy_if_not_exists'].mock_calls,
                             [call(self.preprocessor.project_path / options_dict['scheme_template'],
                                   'scheme_resource')])

    def test_create_both_default_templates(self):
        options_dict = {'doc_template': 'doc',
                        'scheme_template': 'scheme'}
        options = CombinedOptions(options_dict,
                                  defaults=options_dict)
        mock_resource = Mock(side_effect=['doc_resource', 'scheme_resource'])
        with patch.multiple('pgsqldoc.pgsqldoc',
                            copy_if_not_exists=DEFAULT,
                            resource_filename=mock_resource) as mocks:
            Preprocessor._create_default_templates(self.preprocessor, options)
            self.assertEqual(mocks['copy_if_not_exists'].mock_calls,
                             [call(self.preprocessor.project_path / options_dict['doc_template'],
                                   'doc_resource'),
                              call(self.preprocessor.project_path / options_dict['scheme_template'],
                                   'scheme_resource')])

    def test_nothing_creates_with_undefault_template_names(self):
        options_dict = {'doc_template': 'undefault_doc',
                        'scheme_template': 'undefault_scheme'}
        defaults_dict = {'doc_template': 'doc',
                         'scheme_template': 'scheme'}
        options = CombinedOptions(options_dict,
                                  defaults=defaults_dict)
        with patch.multiple('pgsqldoc.pgsqldoc',
                            copy_if_not_exists=DEFAULT,
                            resource_filename=DEFAULT) as mocks:
            Preprocessor._create_default_templates(self.preprocessor, options)
            self.assertEqual(mocks['copy_if_not_exists'].call_count, 0)
            self.assertEqual(mocks['resource_filename'].call_count, 0)
