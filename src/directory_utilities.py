import os
import errno
import json


def validate_or_make_directory(directory_string):
    if not os.path.exists(os.path.dirname(directory_string)):
        try:
            os.makedirs(os.path.dirname(directory_string))
            print('Successfully created `{}` file directory'.format(directory_string))
        except OSError as exception:  # Guard against race condition
            if exception.errno != errno.EEXIST:
                raise


def get_json_from_file(directory_string, default_json_content):
    validate_or_make_directory(directory_string)
    try:
        with open(directory_string) as file:
            file_content = json.load(file)
            file.close()
            return file_content
    except (IOError, json.decoder.JSONDecodeError):
        with open(directory_string, 'w') as file:
            json.dump(default_json_content, file, indent=4)
            file.close()
            return default_json_content


def write_json_to_file(directory_string, json_content):
    with open(directory_string, 'w') as file:
        json.dump(json_content, file, indent=4)
        file.close()