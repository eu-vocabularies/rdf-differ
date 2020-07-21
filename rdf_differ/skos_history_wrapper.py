"""
skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from pathlib import Path
from shutil import copy
from urllib.parse import urljoin, quote

from rdflib.util import guess_format

from utils.file_utils import INPUT_MIME_TYPES, dir_exists, dir_is_empty

CONFIG_TEMPLATE = """# !/bin/bash

DATASET = {dataset}
SCHEMEURI = {scheme_uri}

VERSIONS = {versions}
BASEDIR = {basedir}
FILENAME = {filename}

PUT_URI = {put_uri}
UPDATE_URI = {update_uri}
QUERY_URI = {query_uri}

INPUT_MIME_TYPE = {input_type}"""


class SKOSHistoryRunner:
    def __init__(self, dataset: str, scheme_uri: str, basedir: str, filename: str, endpoint: str,
                 old_version_file: str, new_version_file: str, old_version_id: str = 'v1',
                 new_version_id: str = 'v2', config_template: str = CONFIG_TEMPLATE):
        """
        file_format:
        file_extension:

        :param dataset:
        :param scheme_uri:
        :param basedir:
        :param filename: explain that it doesn't contain the suffix.
        :param endpoint:
        :param old_version_file:
        :param new_version_file:
        :param old_version_id:
        :param new_version_id:
        :param config_template:
        """
        self.config_template = config_template
        self.dataset = quote(dataset)
        self.scheme_uri = scheme_uri

        self.old_version_file = old_version_file
        self.new_version_file = new_version_file
        self.old_version_id = old_version_id
        self.new_version_id = new_version_id

        self.basedir = basedir
        self.filename = filename
        self.endpoint = endpoint

        self._check_basedir()

        self.file_format = self._check_file_formats()
        self.file_extension = Path(self.old_version_file).suffix

    @property
    def put_uri(self) -> str:
        """
        Build the PUT URI
        :return: str
            PUT URI
        """
        return urljoin(self.endpoint, '/'.join([self.dataset, 'data']))

    @property
    def update_uri(self) -> str:
        """
        Build the update URI
        :return: str
            UPDATE URI
        """
        return urljoin(self.endpoint, self.dataset)

    @property
    def query_uri(self) -> str:
        """
        Build the query URI
        :return: str
            query URI
        """
        return urljoin(self.endpoint, '/'.join([self.dataset, 'query']))

    @staticmethod
    def get_file_format(file: str) -> str:
        file_format = guess_format(file, INPUT_MIME_TYPES)
        if file_format is None:
            raise Exception('Format of "{}" is not supported.'.format(file))

        return file_format

    def run(self):
        self.generate_structure()
        config_location = self.generate_config()
        # run in shell code

    def generate_structure(self):
        v1 = Path(self.basedir) / self.dataset / 'data' / self.old_version_id
        v2 = Path(self.basedir) / self.dataset / 'data' / self.new_version_id

        v1.mkdir(parents=True)
        v2.mkdir(parents=True)

        copy(self.old_version_file, v1 / self._get_full_filename())
        copy(self.new_version_file, v2 / self._get_full_filename())

    def generate_config(self) -> str:
        content = self.config_template.format(
            dataset=self.dataset,
            scheme_uri=self.scheme_uri,
            versions='({} {})'.format(self.old_version_id, self.new_version_id),
            basedir=self.basedir,
            filename=self._get_full_filename(),
            put_uri=self.put_uri,
            update_uri=self.update_uri,
            query_uri=self.query_uri,
            input_type=self.file_format
        )
        location = Path(self.basedir) / '{}.config'.format(self.dataset)
        with open(location, 'w') as file:
            file.write(content)

        return str(location)

    def _get_full_filename(self):
        return '{}{}'.format(self.filename, self.file_extension)

    def _check_file_formats(self):
        formats = []
        for file in [self.old_version_file, self.new_version_file]:
            formats.append(self.get_file_format(file))

        if len(set(formats)) > 1:
            raise Exception(f'File formats are different: {", ".join(format for format in formats)}')

        return formats.pop()

    def _check_basedir(self):
        if dir_exists(self.basedir) and not dir_is_empty(self.basedir):
            raise Exception('Root path is not empty.')
