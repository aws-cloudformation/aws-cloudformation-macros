import sys, os, json

sys.path.insert(1, 'libs')
sys.path.insert(1, 'source/libs')
from troposphere.validators import boolean, integer
from troposphere import AWSObject
from troposphere import Tags, Ref
from cfn_flip import to_json
import logging
import boto3
import git

s3 = boto3.client('s3')
cm = boto3.client('codecommit')

BRANCH_DEFAULT = 'master'
TEMPLATE_NAME_DEFAULT = 'template.yaml'
ASSERT_MESSAGE = "{} Value is Invalid! Currently you can only !Ref a parameter or use a string."

try:
    basestring
except NameError:
    basestring = str


class Template(AWSObject):
    resource_type = 'Template'

    def get_value(self, key, template_params, default=None):
        value = self.properties.get(key)
        if isinstance(value, Ref):
            value = template_params[value.data['Ref']]
        return default if value in [None, ""] else value

    def get_attributes(self, main_template):
        return self.attributes


class Git(Template):
    resource_type = 'Template::Git'

    props = {
        'Mode': (basestring, True),
        'Provider': (basestring, True),
        'Repo': (basestring, True),
        'Path': (basestring, True),
        'Branch': (basestring, False),
        'Owner': (basestring, False),
        'OAuthToken': (basestring, False),
        'Parameters': (dict, False),
        'NotificationARNs': ([basestring], False),
        'Tags': ((Tags, list), False),
        'TimeoutInMinutes': (integer, False),
        'TemplateBucket': (basestring, False),
        'TemplateKey': (basestring, False)
    }


class S3(Template):
    resource_type = 'Template::S3'

    props = {
        'Mode': (basestring, True),
        'Bucket': (basestring, True),
        'Key': (basestring, True),
        'Parameters': (dict, False),
        'NotificationARNs': ([basestring], False),
        'Tags': ((Tags, list), False),
        'TimeoutInMinutes': (integer, False),
        'TemplateBucket': (basestring, False)
    }


def s3_import(request_id, resource_id, resource_obj, template_params,
              aws_region):
    logging.info('Import {} from S3.'.format(resource_id))

    bucket = resource_obj.get_value('Bucket', template_params)
    key = resource_obj.get_value('Key', template_params)

    assert type(bucket) == str, ASSERT_MESSAGE.format('Bucket')
    assert type(key) == str, ASSERT_MESSAGE.format('Key')

    file = '/tmp/' + request_id + '/' + key.replace('/', '_')

    with open(file, 'wb') as f:
        s3.download_fileobj(bucket, key, f)

    with open(file) as f:
        template = json.loads(to_json(f.read()))

    return template


def codecommit_import(request_id, resource_name, resource_obj, template_params,
                      aws_region):
    repo = resource_obj.get_value('Repo', template_params)
    branch = resource_obj.get_value('Branch',
                                    template_params,
                                    default=BRANCH_DEFAULT)
    path = resource_obj.get_value('Path',
                                  template_params,
                                  default=TEMPLATE_NAME_DEFAULT)

    assert type(repo) == str, ASSERT_MESSAGE.format('Repo')
    assert type(branch) == str, ASSERT_MESSAGE.format('Branch')
    assert type(path) == str, ASSERT_MESSAGE.format('Path')

    response = cm.get_file(repositoryName=repo,
                           commitSpecifier=branch,
                           filePath=path)

    template = json.loads(to_json(response['fileContent']))

    return template


def github_import(request_id, resource_name, resource_obj, template_params,
                  aws_region):
    repo = resource_obj.get_value('Repo', template_params)
    branch = resource_obj.get_value('Branch',
                                    template_params,
                                    default=BRANCH_DEFAULT)
    path = resource_obj.get_value('Path',
                                  template_params,
                                  default=TEMPLATE_NAME_DEFAULT)

    token = resource_obj.get_value('OAuthToken', template_params, default='')
    token = token if len(token) == 0 else '{}@'.format(token)

    owner = resource_obj.get_value('Owner', template_params)
    if owner is None:
        raise Exception(
            'Owner property must be provied when provider is GitHub.')

    assert type(repo) == str, ASSERT_MESSAGE.format('Repo')
    assert type(branch) == str, ASSERT_MESSAGE.format('Branch')
    assert type(path) == str, ASSERT_MESSAGE.format('Path')
    assert type(token) == str, ASSERT_MESSAGE.format('Token')
    assert type(owner) == str, ASSERT_MESSAGE.format('Owner')

    clone_dir = '/tmp/' + request_id + '/github'
    if not os.path.exists(clone_dir + '/' + repo):
        repo_url = 'https://{}github.com/{}/{}.git'.format(token, owner, repo)
        git.Git(clone_dir).clone(repo_url)

    file = clone_dir + '/' + repo + '/' + path
    with open(file) as f:
        template = json.loads(to_json(f.read()))

    return template


switcher = {
    's3': s3_import,
    'codecommit': codecommit_import,
    'github': github_import
}


def get_template(request_id, resource_id, resource_obj, template_params,
                 aws_region):
    if isinstance(resource_obj, Git):
        provider = resource_obj.properties["Provider"].lower()

    if isinstance(resource_obj, S3):
        provider = 's3'

    return switcher[provider](request_id, resource_id, resource_obj,
                              template_params, aws_region)
