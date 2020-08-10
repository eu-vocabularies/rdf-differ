"""
diffs.py
Date: 30/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from werkzeug.datastructures import FileStorage

from rdf_differ import config
from rdf_differ.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.skos_history_wrapper import SKOSHistoryRunner, SubprocessFailure
from utils.file_utils import temporarily_save_files


def get_diffs() -> tuple:
    """
        List the existent datasets with their descriptions.
    :return: list of existent datasets
    :rtype: list, int
    """
    fuseki_adapter = FusekiDiffAdapter(config.ENDPOINT)
    try:
        datasets, status = fuseki_adapter.list_datasets()
        return [{dataset: fuseki_adapter.diff_description(dataset)[0]} for dataset in datasets], status
    except FusekiException as exception:
        return str(exception), 500


def create_dataset(body: dict) -> tuple:
    """
        Create a dataset in the Fuseki store.
    :param body:
        {
          "dataset_id": "string"
        }
    :return: str, int
    """
    fuseki_adapter = FusekiDiffAdapter(config.ENDPOINT)

    try:
        response, _ = fuseki_adapter.create_dataset(dataset_name=body.get('dataset_id'))
        return response, 200
    except ValueError as exception:
        return str(exception), 400
    except FusekiException as exception:
        return str(exception), 409


def create_diff(dataset_id: str, body: dict, old_version_file_content: FileStorage,
                new_version_file_content: FileStorage) -> tuple:
    """
        Create a diff based on the versions send with old_Version_file_content and new_version_file_content.
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :param body:
        {
          "dataset_description": "string",
          "dataset_uri": "string",
          "new_version_id": "string",
          "old_version_id": "string",
        }
    :param old_version_file_content: The content of the old version file.
    :param new_version_file_content: The content of the new version file.
    :return:
    :rtype: str, int
    """
    try:
        with temporarily_save_files(old_version_file_content, new_version_file_content) as \
                (temp_dir, old_version_file, new_version_file):
            SKOSHistoryRunner(dataset=dataset_id,
                              basedir=temp_dir / 'basedir',
                              scheme_uri=body.get('dataset_uri'),
                              old_version_id=body.get('old_version_id'),
                              new_version_id=body.get('new_version_id'),
                              old_version_file=old_version_file,
                              new_version_file=new_version_file).run()

        return "Request to create a new dataset diff successfully accepted for processing.", 200
    except ValueError as exception:
        return str(exception), 500
    except SubprocessFailure:
        return 'Internal error while uploading the diffs.', 500


def get_diff(dataset_id: str) -> tuple:
    """
        Get the dataset description
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: dataset description
    :rtype: dict, int
    """
    try:
        return FusekiDiffAdapter(config.ENDPOINT).diff_description(dataset_id)
    except EndPointNotFound:
        return f'<{dataset_id}> does not exist.', 404
    # TODO: improve on the type of the error catching
    except Exception:
        return "Unexpected Error.", 500


def delete_diff(dataset_id: str) -> tuple:
    """
        Delete a dataset
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: info about deletion
    :rtype: str, int
    """
    return FusekiDiffAdapter(config.ENDPOINT).delete_dataset(dataset_id)
