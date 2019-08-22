import argparse
import re

import networkx as nx

from mongoengine import connection, Document
from dateutil.relativedelta import relativedelta
from Levenshtein import distance

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
    # first we check if the issue itself contains information about its state
    if issue.resolution and issue.resolution.lower() in _WONT_FIX_TYPES:
        return False
    if issue.resolution and issue.resolution.lower() in _RESOLVED_TYPES and issue.status and issue.status.lower() in _CLOSED_STATUS:
        return True

    # then we check all events related to the issue
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


TEST_FILES = re.compile(r'(^|\/)(test|tests|test_long_running|testing|legacy-tests|testdata|test-framework|derbyTesting|unitTests|java\/stubs|test-lib|src\/it|src-lib-test|src-test|tests-src|test-cactus|test-data|test-deprecated|src_unitTests|test-tools)\/', re.IGNORECASE)
DOCUMENTATION_FILES = re.compile(r'(^|\/)(doc|docs|example|examples|sample|samples|demo|tutorial|helloworld|userguide|showcase|SafeDemo)\/', re.IGNORECASE)
OTHER_EXCLUSIONS = re.compile(r'(^|\/)(_site|auxiliary-builds|gen-java|external)\/', re.IGNORECASE)


def java_filename_filter(filename, production_only=True):
    """
    cheks if a file is a java file
    :param filename: name of the file
    :param production_only: if True, the function excludes tests and documentation, eg. test and example folders
    :return: True if the file is java, false otherwise
    """
    ret = filename.endswith('.java') and \
           not filename.endswith('package-info.java')
    if production_only:
        ret = ret and \
              not re.search(TEST_FILES, filename) and \
              not re.search(DOCUMENTATION_FILES, filename) and \
              not re.search(OTHER_EXCLUSIONS, filename)
    return ret


# qualifiers are expected at the end of the tag and they may have a number attached
# it is very important for the b to be at the end otherwise beta would already be matched!
_GIT_TAG_QUALIFIERS = r"[^a-z]((rc)|(alpha)|(beta)|(b)|(m)|(r)|(broken)|(DEV_STYLE)|(COPY)|(mysql_auth)|(hbase0\.98)|(release-test-00001)|(t1)|(t2)|(t3)|(branch))([^a-z]|$)"


# separators are expected to divide 2 or more numbers
_TAG_VERSION_SEPARATORS = ['.', '_', '-']


# manual corrections of known broken tags that cannot be heuristically identified
_MANUAL_CORRECTIONS = {'COMMONS_JEXL_2_0': 'b9dc71c16461ce497e7ba4b2439983c4d756f0af'}


def git_tag_filter(project_name, discard_patch=False, correct_broken_tags=True, date_tolerance=3, max_steps=2):
    """
    Filters all tags of a project to only include those that are likely versions of releases. The version of the
    release is determined using pattern matching with the possible version separators ., _, and -. The version is
    returned in a SemVer style, i.e., always with three numbers for major, minor, and patch.
    :param project_name: name of the project
    :param discard_patch: only keep major releases, i.e., discard patch releases
    :param correct_broken_tags Corrects the date of broken tags by looking at the parent commits. A tag is considered
    broken if there are multiple tags at the exact same time.
    :param date_tolerance time difference that is considered as "same" while looking for a parent in minutes
    :param max_steps depth of prior parent commits that are considered when looking for parents
    :return: List of dicts with the filtered tags. The dict contains the entries 'version' with the SemVer version of
    we determined for the tag, 'original' with the name of the tag, 'revision' with the revision hash of the commit that
    is tagged, 'corrected_revision' if a broken tag was found, and 'qualifiers' if there are any.
    """
    initial_versions = []
    project_id = Project.objects(name=project_name).get().id
    vcs_system_id = VCSSystem.objects(project_id=project_id).get().id
    if correct_broken_tags:
        tag_dates = {}
        tag_commits = set()
        for tag in Tag.objects(vcs_system_id=vcs_system_id):
            tag_commits.add(Commit.objects(id=tag.commit_id).only('committer_date').get())
        for tag_commit in tag_commits:
            if tag_commit.committer_date in tag_dates:
                tag_dates[tag_commit.committer_date] += 1
            else:
                tag_dates[tag_commit.committer_date] = 1

    for tag in Tag.objects(vcs_system_id=vcs_system_id):
        if tag.name.startswith("J_"):
            continue
        corrected_commit = None
        if correct_broken_tags:
            if tag.name in _MANUAL_CORRECTIONS:
                corrected_commit = Commit.objects(revision_hash=_MANUAL_CORRECTIONS[tag.name]).only(
                    'revision_hash').get()
            else:
                tag_commit = Commit.objects(id=tag.commit_id).only('committer_date', 'parents').get()
                if tag_dates[tag_commit.committer_date] > 1:
                    tolerated_date = tag_commit.committer_date - relativedelta(minutes=date_tolerance)
                    # simple breadth first search for correct commit
                    steps = 0
                    parents = {}
                    parents[0] = set(tag_commit.parents)
                    while corrected_commit is None and steps < max_steps:
                        if steps in parents:
                            for parent in parents[steps]:
                                parent_commit = Commit.objects(revision_hash=parent).only('committer_date', 'parents',
                                                                                          'revision_hash').get()
                                if parent_commit.committer_date < tolerated_date:
                                    corrected_commit = parent_commit
                                else:
                                    if steps + 1 not in parents:
                                        parents[steps + 1] = set(parent_commit.parents)
                                    else:
                                        for p in parent_commit.parents:
                                            parents[steps + 1].add(p)
                        steps += 1
                    if corrected_commit is None:
                        continue

        filtered_name = re.sub(project_name.lower(), '', tag.name.lower())

        if re.search(_GIT_TAG_QUALIFIERS, filtered_name, re.MULTILINE | re.IGNORECASE):
            continue

        # we only want numbers and separators
        version = re.sub('[a-z]', '', filtered_name)
        # the best separator is the one separating the most numbers
        best = -1
        best_sep = None
        for sep in _TAG_VERSION_SEPARATORS:
            current = 0
            for v in version.split(sep):
                v = ''.join(c for c in v if c.isdigit())
                if v.isnumeric():
                    current += 1
            if current > best:
                best = current
                best_sep = sep
        version = version.split(best_sep)
        final_version = []
        for v in version:
            v = ''.join(c for c in v if c.isdigit())
            if v.isnumeric():
                final_version.append(int(v))

        # if we have a version we append it to our list
        if final_version:
            # force SemVer by potentially adding minor and patch version if only major is present
            if len(final_version) == 1:
                final_version.append(0)
            if len(final_version) == 2:
                final_version.append(0)
            commit = Commit.objects(id=tag.commit_id).only('revision_hash').get()
            fversion = {'version': final_version, 'original': tag.name, 'revision': commit.revision_hash}
            if corrected_commit is not None:
                fversion['corrected_revision'] = corrected_commit.revision_hash
            initial_versions.append(fversion)

    # sort versions using version numbers based on the SemVer scheme
    sorted_versions = sorted(initial_versions, key=lambda x: (x['version'][0], x['version'][1], x['version'][2]))

    # finally make sorted versions unique and discard patch releases
    ret = []
    for version in sorted_versions:
        # we discard patch releases
        if discard_patch:
            if len(version['version']) > 2:
                del version['version'][2:]
        # we discard duplicates; the sorting ensures that we only keep the oldest release in case we ignore patches
        if version['version'] not in [v2['version'] for v2 in ret]:
            ret.append(version)

    return ret


def get_affected_versions(issue, project_name='', jira_key=''):
    """
    Determines a list of the affected versions as a list of SemVer versions. Only considers releases.
    :param issue: issue for which the affected versions are determined
    :param project_name: name of the project; can be provided to increase sensitivity of the approach
    :param jira_key: Jira key of the project; can be provided to increase sensitivity of the approach
    :return: list of lists of version numbers
    """
    versions = []
    if issue.affects_versions:
        for av in issue.affects_versions:
            av = av.lower()
            if av.startswith('v'):
                av = av[1:]
            av = av.replace(project_name,'')
            av = av.replace(jira_key, '')
            av = av.replace('.x', '')
            av = av.replace('release', '')
            av = av.strip()
            if all(v.isnumeric() for v in av.split('.')):
                versions.append(av.split('.'))
    return versions


def get_commit_graph(vcs_system_id, silent=True):
    """Load NetworkX digraph structure from commits of this VCS.
    :param vcs_system_id id of the vcs system for which the graph is created
    :param silent determines whether there is an output to stdout in case of a missing parent commit
    """
    g = nx.DiGraph()
    # first we add all nodes to the graph
    for c in Commit.objects(vcs_system_id=vcs_system_id).only('id', 'revision_hash').timeout(False):
        g.add_node(c.revision_hash)

    # after that we draw all edges
    for c in Commit.objects(vcs_system_id=vcs_system_id).only('id', 'parents', 'revision_hash').timeout(False):
        for p in c.parents:
            try:
                p1 = Commit.objects(vcs_system_id=vcs_system_id,revision_hash=p).only('id', 'revision_hash').get()
                g.add_edge(p1.revision_hash, c.revision_hash)
            except Commit.DoesNotExist:
                if not silent:
                    print("parent of a commit is missing (commit id: {} - revision_hash: {})".format(c.id, p))
    return g


def heuristic_renames(vcs_system_id, revision_hash):
    """Return most probable rename from all FileActions, rest count as DEL/NEW.
    There may be multiple renames of the same file in the same commit, e.g., A->B, A->C.
    This is due to pygit2 and the Git heuristic for rename detection.
    This function uses another heuristic to detect renames by employing a string distance metric on the file name.
    This captures things like commons-math renames org.apache.math -> org.apache.math3.
    :param vcs_system_id vcs system of the commit
    :param revision_hash revision has of the commit for which the renames are determined
    :return Tuple of renames and added files. The renames are a list of tuples, where the first element in the tuple is
    the old name and the second element is the new name. The added files are a list.
    """
    renames = {}
    commit = Commit.objects(vcs_system_id=vcs_system_id, revision_hash=revision_hash).only('id').get()
    for fa in FileAction.objects(commit_id=commit.id, mode='R'):
        new_file = File.objects.get(id=fa.file_id)
        old_file = File.objects.get(id=fa.old_file_id)

        if old_file.path not in renames.keys():
            renames[old_file.path] = []
        renames[old_file.path].append(new_file.path)

    true_renames = []
    added_files = []
    for old_file, new_files in renames.items():

        # only one file, easy
        if len(new_files) == 1:
            true_renames.append((old_file, new_files[0]))
            continue

        # multiple files, find the best matching
        min_dist = float('inf')
        probable_file = None
        for new_file in new_files:
            d = distance(old_file, new_file)
            if d < min_dist:
                min_dist = d
                probable_file = new_file
        true_renames.append((old_file, probable_file))

        for new_file in new_files:
            if new_file == probable_file:
                continue
            added_files.append(new_file)
    return true_renames, added_files
