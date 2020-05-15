import sys, os, json, io

sys.path.insert(1, 'libs')
sys.path.insert(1, 'source/libs')

import logging
import boto3
import git
import gitlab

from cfn_flip import to_json
from simulator import *
from utils import *

s3 = boto3.client('s3')
cm = boto3.client('codecommit')

try:
    basestring
except NameError:
    basestring = str

class Macro(AWSObject): 
    global aws_cfn_request_id
    global template_params
    global aws_region

    macro_name = MACRO_NAME
    macro_separator = MACRO_SEPARATOR
    macro_prefix = MACRO_PREFIX

    resources = []
    json_template = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.resources.append(cls.resource_type)

    def get_value(self, key, default=None):
        value = self.properties.get(key)
        if type(value) == Ref:
            value = self.template_params[value.extract()]
        return default if value in [None, ""] else value

    def get_template(self):
        template = self.download()

        cfn = Simulator(template, {
            **self.template_params,
            **self.get_value('Parameters', default={})
        })

        return cfn.simulate()

    def _s3_export(self):
        assert self.aws_cfn_request_id, 'Request Id is None.'

        bucket_name = self.get_value('TemplateBucket', DEFAULT_BUCKET)
        object_key = self.get_value('TemplatePrefix')

        if not object_key:
            object_key = self.get_value('Path', self.get_value('Key'))
            object_key = '/'.join(object_key.split("/")[:-1])

        object_key = '{}/{}-{}.template'.format(
            object_key, self.title, 
            self.aws_cfn_request_id
        )

        logging.info('Upload {} in {}'.format(object_key, bucket_name))

        import_template = json.dumps(self.get_template())
        s3.upload_fileobj(io.BytesIO(import_template.encode()), bucket_name, object_key)

        return Join(
            '', ['https://', bucket_name, '.s3.amazonaws.com/', object_key])

    def get_stack_template(self):
        nested_stack = cloudformation.Stack(title=self.title)
        for attr in nested_stack.attributes:
            if hasattr(self, attr):
                setattr(nested_stack, attr, getattr(self, attr))
        for prop in nested_stack.propnames:
            if prop in self.properties:
                if prop == 'Parameters': # Parameters are already resolved by Simulator
                    continue
                setattr(nested_stack, prop, self.get_value(prop))
        nested_stack.TemplateURL = self._s3_export()

        return nested_stack

    def get_aws_cfn_request_id(self):
        return self.aws_cfn_request_id

    def get_template_params(self):
        return self.template_params

    def get_aws_region(self):
        return self.aws_region

    def is_macro(self):
        return True

    @staticmethod
    def to_logical_id(value):
        return value.replace(Macro.macro_prefix, "").replace(Macro.macro_separator, "")


class Git(Macro):
    resource_type = Macro.macro_prefix + 'Git'

    props = {
        'Mode': (basestring, True),
        'Provider': (basestring, True),
        'Repo': (basestring, False),
        'Project': (basestring, False), 
        'Path': (basestring, True),
        'Branch': (basestring, False),
        'Owner': (basestring, False),
        'OAuthToken': (basestring, False),
        'Parameters': (dict, False),
        'NotificationARNs': ([basestring], False),
        'Tags': ((Tags, list), False),
        'TimeoutInMinutes': (integer, False),
        'TemplateBucket': (basestring, False),
        'TemplatePrefix': (basestring, False)
    }

    def _codecommit_import(self):
        logging.info('Import {} from Codecommit.'.format(self.title))

        repo = self.get_value('Repo')
        branch = self.get_value('Branch', default=BRANCH_DEFAULT)
        path = self.get_value('Path', default=TEMPLATE_NAME_DEFAULT)

        assert type(repo) == str, ASSERT_MESSAGE.format('Repo', self.title)
        assert type(branch) == str, ASSERT_MESSAGE.format('Branch', self.title)
        assert type(path) == str, ASSERT_MESSAGE.format('Path', self.title)

        response = cm.get_file(repositoryName=repo,
                               commitSpecifier=branch,
                               filePath=path)

        template = json.loads(to_json(response['fileContent']))

        return template

    def _github_import(self):
        logging.info('Import {} from Github.'.format(self.title))

        repo = self.get_value('Repo')
        branch = self.get_value('Branch', default=BRANCH_DEFAULT)
        path = self.get_value('Path', default=TEMPLATE_NAME_DEFAULT)

        token = self.get_value('OAuthToken', default='')
        token = token if len(token) == 0 else '{}@'.format(token)

        owner = self.get_value('Owner')
        if owner is None:
            raise Exception(
                'Owner property must be provied when provider is GitHub.')

        assert type(repo) == str, ASSERT_MESSAGE.format('Repo', self.title)
        assert type(branch) == str, ASSERT_MESSAGE.format('Branch', self.title)
        assert type(path) == str, ASSERT_MESSAGE.format('Path', self.title)
        assert type(token) == str, ASSERT_MESSAGE.format('Token', self.title)
        assert type(owner) == str, ASSERT_MESSAGE.format('Owner', self.title)
        assert self.aws_cfn_request_id, 'Request Id is None.'

        clone_dir = '/tmp/' + self.aws_cfn_request_id + '/github'
        logging.info('Clone in {}.'.format(clone_dir))

        if not os.path.exists(clone_dir + '/' + repo):
            repo_url = 'https://{}github.com/{}/{}.git'.format(
                token, owner, repo)
            git.Git(clone_dir).clone(repo_url)

        file = clone_dir + '/' + repo + '/' + path
        with open(file) as f:
            template = json.loads(to_json(f.read()))

        return template

    def _gitlab_import(self):
        logging.info('Import {} from Gitlab.'.format(self.title))

        project = self.get_value('Project')
        branch = self.get_value('Branch', default=BRANCH_DEFAULT)
        path = self.get_value('Path', default=TEMPLATE_NAME_DEFAULT)
        token = self.get_value('OAuthToken', default='')

        gl = gitlab.Gitlab('https://gitlab.com', private_token=token, api_version=4)
        gl.auth()

        project = gl.projects.get(project)
        template = project.files.raw(file_path=path, ref=branch)

        return json.loads(to_json(template))


    def download(self):
        provider = self.get_value('Provider')

        if provider.lower() == 'github':
            return self._github_import()

        if provider.lower() == 'codecommit':
            return self._codecommit_import()

        if provider.lower() == 'gitlab':
            return self._gitlab_import()

class S3(Macro):
    resource_type = Macro.macro_prefix + 'S3'

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

    def _s3_import(self):
        logging.info('Import {} from S3.'.format(self.title))

        bucket = self.get_value('Bucket')
        key = self.get_value('Key')

        assert type(bucket) == str, ASSERT_MESSAGE.format('Bucket', self.title)
        assert type(key) == str, ASSERT_MESSAGE.format('Key', self.title)
        assert self.aws_cfn_request_id, 'Request Id is None.'

        file = '/tmp/' + self.aws_cfn_request_id + '/' + key.replace('/', '_')
        logging.info('Save file in {}, from s3://{}/{}.'.format(file, bucket, key))

        with open(file, 'wb') as f:
            s3.download_fileobj(bucket, key, f)

        with open(file) as f:
            template = json.loads(to_json(f.read()))

        return template

    def download(self):
        return self._s3_import()


