import argparse

from mongoengine import connection, Document

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


def reset_connection_cache():
    connection._connections = {}
    connection._connection_settings ={}
    connection._dbs = {}
    for document_class in Document.__subclasses__():
        document_class._collection = None


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


_WONT_FIX_TYPES = {'not a bug', "won't do", "won't fix", 'duplicate', 'cannot reproduce', 'not a problem',
                   'works for me', 'invalid'}
_RESOLVED_TYPES = {'delivered', 'resolved', 'fixed', 'workaround', 'done', 'implemented', 'auto closed'}
_CLOSED_STATUS = {'resolved', 'closed'}


def jira_is_resolved_and_fixed(issue):
    """
    checks if an JIRA issue was addressed (at least once)
    :param issue: the issue
    :return: true if there was a time when the issue was closed and the status was resolved as fixed (or similar),
    false otherwise
    """
    if issue.resolution and issue.resolution.lower() in _WONT_FIX_TYPES:
        return False
    current_status = None
    current_resolution = None
    for e in Event.objects(issue_id=issue.id).order_by('created_at'):
        if e.status is not None and e.status.lower()=='status' and e.new_value is not None:
            current_status = e.new_value.lower()
        if e.status is not None and e.status.lower() == 'resolution' and e.new_value is not None:
            current_resolution = e.new_value.lower()
        if current_status in _CLOSED_STATUS and current_resolution in _RESOLVED_TYPES:
            return True
    return False