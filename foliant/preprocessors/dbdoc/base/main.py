import os

from jinja2 import Environment, FileSystemLoader
from pkg_resources import resource_filename
from foliant.preprocessors.utils.combined_options import CombinedOptions
from logging import getLogger


logger = getLogger('unbound.dbdoc.pgsql')


class DBRendererBase:
    defaults = {}
    module_name = __name__

    def __init__(self, config):
        self.config = config

    def process(self, tag_options) -> str:
        self.options = CombinedOptions(
            {
                'config': self.config,
                'tag': tag_options
            },
            priority='tag',
            defaults=self.defaults
        )

        self.connect()
        return self.gen_docs()

    def connect(self):
        """
        Connect to database using parameters from options.
        """
        raise NotImplementedError

    def get_template(self, key: str, default_name: str):
        template_path = self.options.get(key)
        if template_path:
            return template_path
        else:
            return resource_filename(
                self.module_name,
                f"templates/{default_name}"
            )

    def get_doc_template(self):
        KEY = 'doc_template'
        DEFAULT_NAME = 'doc.j2'
        return self.get_template(KEY, DEFAULT_NAME)

    def get_scheme_template(self):
        KEY = 'scheme_template'
        DEFAULT_NAME = 'scheme.j2'
        return self.get_template(KEY, DEFAULT_NAME)

    def gen_docs(self) -> str:
        data = self.collect_datasets()

        docs = ''

        if self.options['doc']:
            docs += self.to_md(data, self.get_doc_template())
        if self.options['scheme']:
            docs += '\n\n' + self.to_diag(data, self.get_scheme_template())
        return docs

    def collect_datasets(self) -> dict:
        raise NotImplementedError

    def to_md(self, data: dict, template: str) -> str:
        template_root, template_name = os.path.split(template)
        with open(template, encoding='utf8') as f:
            # template = Template(f.read())
            template = Environment(loader=FileSystemLoader(template_root)).from_string(f.read())

        return template.render(**data)

    def to_diag(self, data: dict, template: str) -> str:
        template_root, template_name = os.path.split(template)
        with open(template, encoding='utf8') as f:
            # template = Template(f.read())
            template = Environment(loader=FileSystemLoader(template_root)).from_string(f.read())

        return template.render(
            tables=data['tables']
        )
