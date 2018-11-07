import argparse
import hashlib

from pycoshark.mongomodels import *

def is_authentication_enabled(db_user, db_password):
    if db_user is not None and db_user and db_password is not None and db_password:
        return True

    return False


def create_mongodb_uri_string(db_user, db_password, db_hostname, db_port, db_authentication_database, db_ssl_enabled):
    uri = 'mongodb://'

    if is_authentication_enabled(db_user, db_password):
        uri = '%s%s:%s@%s:%s' % (uri, db_user, db_password, db_hostname, db_port)
    else:
        uri = '%s%s:%s' % (uri, db_hostname, db_port)

    if (db_authentication_database is not None and db_authentication_database) or db_ssl_enabled:
        uri = '%s/?' % uri

        if db_authentication_database is not None and db_authentication_database:
            uri = '%sauthSource=%s&' % (uri, db_authentication_database)

        if db_ssl_enabled:
            uri = '%sssl=true&ssl_cert_reqs=CERT_NONE&' % uri

        uri = uri.rstrip('&')

    return uri


def get_code_entity_state_identifier(long_name, commit_id, file_id):
    """
    DEPRECATED: use CodeEntityState.calculate_identifier instead
    """
    return CodeEntityState.calculate_identifier(long_name, commit_id, file_id)

def get_code_group_state_identifier(long_name, commit_id):
    """
    DEPRECATED: use CodeGroupState.calculate_identifier instead
    """
    return CodeGroupState.calculate_identifier(long_name, commit_id)


def get_base_argparser(description, version):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--version', help='Shows the version', action='version', version=version)
    parser.add_argument('-U', '--db-user', help='Database user name', default=None)
    parser.add_argument('-P', '--db-password', help='Database user password', default=None)
    parser.add_argument('-DB', '--db-database', help='Database name', default='smartshark')
    parser.add_argument('-H', '--db-hostname', help='Name of the host, where the database server is running',
                        default='localhost')
    parser.add_argument('-p', '--db-port', help='Port, where the database server is listening', default=27017, type=int)
    parser.add_argument('-a', '--db-authentication', help='Name of the authentication database', default=None)
    parser.add_argument('--ssl', help='Enables SSL', default=False, action='store_true')

    return parser