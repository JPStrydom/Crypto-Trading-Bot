import os
import errno
import json


def validate_or_make_directory(directory_string):
    """
    Check if a directory exists. If it doesn't, then create it.

    :param directory_string: The relative directory string (ex: database/secrets.json)
    :type directory_string: str
    """
    if not os.path.exists(os.path.dirname(directory_string)):
        try:
            os.makedirs(os.path.dirname(directory_string))
            print("Successfully created `{}` file directory".format(directory_string))
        except OSError as exception:  # Guard against race condition
            if exception.errno != errno.EEXIST:
                raise


def get_json_from_file(directory_string, default_json_content=None):
    """
    Get the contents of a JSON file. If it doesn't exist,
    create and populate it with specified or default JSON content.

    :param directory_string: The relative directory string (ex: database/secrets.json)
    :type directory_string: str
    :param default_json_content: The content to populate a non-existing JSON file with
    :type default_json_content: dict, list
    """
    validate_or_make_directory(directory_string)
    try:
        with open(directory_string) as file:
            file_content = json.load(file)
            file.close()
            return file_content
    except (IOError, json.decoder.JSONDecodeError):
        with open(directory_string, "w") as file:
            if default_json_content is None:
                default_json_content = {}
            json.dump(default_json_content, file, indent=4)
            file.close()
            return default_json_content


def write_json_to_file(directory_string, json_content):
    """
    Get the contents of a JSON file. If it doesn't exist,
    create and populate it with specified or default JSON content.

    :param directory_string: The relative directory string (ex: database/secrets.json)
    :type directory_string: str
    :param json_content: The content to populate a non-existing JSON file with
    :type json_content: dict
    """
    with open(directory_string, "w") as file:
        json.dump(json_content, file, indent=4)
        file.close()
