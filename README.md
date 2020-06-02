[![](https://img.shields.io/pypi/v/foliantcontrib.dbdoc.svg)](https://pypi.org/project/foliantcontrib.dbdoc/)  [![](https://img.shields.io/github/v/tag/foliant-docs/foliantcontrib.dbdoc.svg?label=GitHub)](https://github.com/foliant-docs/foliantcontrib.dbdoc)

# Database Documentation Generator for Foliant

This preprocessor generates simple documentation based on the structure of the database. It uses [Jinja2](http://jinja.pocoo.org/) templating engine for customizing the layout and [PlantUML](http://plantuml.com/) for drawing the database scheme.

Currently supported databases:

* **PostgreSQL**,
* **Oracle**.

## Installation

### Prerequisites

DBDoc generates documentation by querying database structure. That's why you will need client libraries installed on your computer before running the preprocessor.

PostgreSQL will be installed automatically with the preprocessor.

But Oracle libraries are proprietary, so we cannot include them even in our [Docker distribution](https://hub.docker.com/r/foliant/foliant/tags). So, if you are planning on using DBDoc to document Oracle databases, first install the [Instant Client](https://www.oracle.com/database/technologies/instant-client.html).

> If you search the web, you can find ways to install Oracle Instant Client inside your Docker image, just saying.

### Preprocessor

```bash
$ pip install foliantcontrib.dbdoc
```

## Config

To enable the preprocessor, add `dbdoc` to `preprocessors` section in the project config:

```yaml
preprocessors:
    - dbdoc
```

The preprocessor has a number of options:

```yaml
preprocessors:
    - dbdoc:
        host: localhost
        port: 5432
        dbname: postgres
        user: postgres
        password: ''
        doc: True
        scheme: True
        filters:
            ...
        doc_template: dbdoc.j2
        scheme_template: scheme.j2
        components:
          - tables
          - functions
          - triggers
```

`host`
:   Database host address. Default: `localhost`

`port`
:   Database port. Default: `5432` for pgsql, `1521` for Oracle.

`dbname`
:   PostgreSQL database name. Default: `postgres` for pgsql, `orcl` for oracle.

`user`
:   PostgreSQL user name. Default: `postgres` for pgsql, `hr` for oracle.

`password`
:   PostgreSQL user password. Default: `postgres` for pgsq, `oracle` for oracle.

`doc`
:   If `true` — documentation will be generated. Set to `false` if you only want to draw a scheme of the database. Default: `true`

`scheme`
:   If `true` — the platuml code for database scheme will be generated. Default: `true`

`filters`
:   SQL-like operators for filtering the results. More info in the **Filters** section.

`doc_template`
:   Path to jinja-template for documentation. Path is relative to the project directory. If not supplied — default template would be used.

`scheme_template`
:   Path to jinja-template for scheme. Path is relative to the project directory. If not supplied — default template would be used.

`components`
:   List of components to be added to documentation. If not supplied — everything will be added. Use to exclude some parts of documentation.

## Usage

DBDoc currently supports two database engines: Oracle and PostgreSQL. To generate Oracle database documentation, add an `<oracle></oracle>` tag to a desired place of your chapter.


```html
# Introduction

This document contains the most awesome automatically generated documentation of our marvellous Oracle database.

<oracle></oracle>
```

To generate PostgreSQL database documentation, add a `<pgsql></pgsql>` tag to a desired place of your chapter.


```html
# Introduction

This document contains the most awesome automatically generated documentation of our marvellous Oracle database.

<pgsql></pgsql>
```

Each time the preprocessor encounters one of the mentioned tags, it inserts the whole generated documentation text instead of it. The connection parameters are taken from the config-file.

You can also specify some parameters (or all of them) in the tag options:

```html
# Introduction

Introduction text for database documentation.

<oracle scheme="true"
        doc="false"
        host="11.51.126.8"
        port="1521"
        dbname="mydb"
        user="scott"
        password="tiger">
</oracle>
```

Tag parameters have the highest priority.

This way you can have documentation for several different databases in one foliant project (even in one md-file if you like it so). It also allows you to put documentation and scheme for you database separately by switching on/off `doc` and `scheme` params in tags.

## Filters

You can add filters to exclude some tables from the documentation. dbdocs supports several SQL-like filtering operators and a determined list of filtering fields.

You can switch on filters either in foliant.yml file like this:

```yaml
preprocessors:
  - dbdoc:
    filters:
      eq:
        schema: public
      regex:
        table_name: 'main_.+'
```

or in tag options using the same yaml-syntax:

```html

<pgsql filters="
  eq:
    schema: public
  regex:
    table_name: 'main_.+'">
</pgsql>

```

List of currently supported operators:

operator | SQL equivalent | description | value
-------- | -------------- | ----------- | -----
`eq` | `=` | equals | literal
`not_eq` | `!=` | does not equal | literal
`in` | `IN` | contains | list
`not_in` | `NOT IN` | does not contain | list
`regex` | `~`, `REGEX_LIKE` | matches regular expression | literal
`not_regex` | `!~`, `NOT REGEX_LIKE` | does not match regular expression | literal

List of currently supported filtering fields:

field | description
----- | -----------
schema | filter by database schema
table_name | filter by database table names

The syntax for using filters in configuration files is following:

```yaml
filters:
  <operator>:
    <field>: value
```

If `value` should be list like for `in` operator, use YAML-lists instead:

```yaml
filters:
  in:
    schema:
      - public
      - corp
```

## About Templates

The structure of generated documentation is defined by jinja-templates. You can choose what elements will appear in the documentation, change their positions, add constant text, change layouts and more. Check the [Jinja documentation](http://jinja.pocoo.org/docs/2.10/templates/) for info on all cool things you can do with templates.

If you don't specify path to templates in the config-file and tag-options dbdoc will use default templates.

If you wish to create your own template, the default ones may be a good starting point.

* [Default **Oracle doc** template.](https://github.com/foliant-docs/foliantcontrib.dbdoc/blob/master/foliant/preprocessors/dbdoc/oracle/templates/doc.j2)
* [Default **Oracle scheme** template.](https://github.com/foliant-docs/foliantcontrib.dbdoc/blob/master/foliant/preprocessors/dbdoc/oracle/templates/scheme.j2)
* [Default **PostgreSQL doc** template.](https://github.com/foliant-docs/foliantcontrib.dbdoc/blob/master/foliant/preprocessors/dbdoc/pgsql/templates/doc.j2)
* [Default **PostgreSQL scheme** template.](https://github.com/foliant-docs/foliantcontrib.dbdoc/blob/master/foliant/preprocessors/dbdoc/pgsql
* /templates/doc.j2)
