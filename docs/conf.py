#!/usr/bin/env python3
from importlib import metadata

from packaging.version import parse

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "sphinx_autodoc_typehints",
    "sphinx_tabs.tabs",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "asphalt-web"
author = "Alex Grönholm"
copyright = "2022, " + author

v = parse(metadata.version(project))
version = v.base_version
release = v.public

language = "en"

exclude_patterns = ["_build"]
pygments_style = "sphinx"
highlight_language = "python3"
todo_include_todos = False
autodoc_inherit_docstrings = False
autodoc_default_options = {"show-inheritance": True}

html_theme = "sphinx_rtd_theme"
htmlhelp_basename = project.replace("-", "") + "doc"

branch_or_release = release if ".post" not in release else "master"
extlinks = {
    "github": (
        f"https://github.com/asphalt-framework/{project}/tree/{branch_or_release}/%s",
        None,
    )
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "asphalt": ("https://asphalt.readthedocs.io/en/latest/", None),
    "litestar": ("https://docs.litestar.dev/latest/", None),
}
