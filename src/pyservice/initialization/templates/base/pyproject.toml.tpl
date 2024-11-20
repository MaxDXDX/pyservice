[build-system]
build-backend = "setuptools.build_meta"
requires = [ "setuptools",]

[project]
description = "{{ app.description }}"
name = "{{ app.app_name }}"
readme = "README.md"
requires-python = ">=3.11"
version = "0.0.1"
authors = [
    {name = "{{ app.author }}"},
]
dependencies = [
  # base level
  "pyservice @ git+https://pack:H4maFc_jxo6rnbaNmu8c@git.cebb.pro/ias-phoenix-native/submodules/pyservice.git@_package",

  # django level
  "django==5.1.3",
  "gunicorn==20.1.0",
  "psycopg2-binary==2.9.9",
  "psycopg==3.1.8",
  "django-cors-headers==4.4.0",
]
