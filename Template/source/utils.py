from troposphere import AWSObject, AWSHelperFn, AWSProperty
from troposphere import Tags, Ref, Join, GetAtt, Export, Template, Join
from troposphere.template_generator import TemplateGenerator
from troposphere.validators import boolean, integer
from troposphere import cloudformation
import os

BRANCH_DEFAULT = 'master'

TEMPLATE_NAME_DEFAULT = 'template.yaml'

ASSERT_MESSAGE = """Template format error: {} value in {} is invalid. 
The value must not depend on any resources or imported values. 
Check if Parameter exists."""

DEFAULT_BUCKET = os.environ.get(
    'DEFAULT_BUCKET', 'macro-template-default-831650818513-us-east-1')

MACRO_NAME = 'Template'

MACRO_SEPARATOR = '::'

MACRO_PREFIX = MACRO_NAME + MACRO_SEPARATOR

setattr(TemplateGenerator, 'add_description', TemplateGenerator.set_description)
setattr(TemplateGenerator, 'add_version', TemplateGenerator.set_version)

def is_macro(x):
	return False
setattr(AWSObject, 'is_macro', is_macro)

def extract(x):
	return list(x.data.values()).pop()
setattr(AWSHelperFn, 'extract', extract)

class TemplateLoaderCollection():

	def __init__(self):
		self.templates = {}

	def __getitem__(self, key):
		return self.templates[key]

	def __setitem__(self, key, value):
		self.templates[key] = value

	def __iter__(self):
		for key in self.templates:
			yield (key, *self.templates[key])

	def update(self, data):
		self.templates.update(data)

	def get(self, key, default=None):
		return self.templates.get(key, default)

	def items(self):
		return self.templates.items()

	def contains(self, key):
		return key in self.templates

	def to_dict(self):
		return self.templates