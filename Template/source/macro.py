import sys, os, io, traceback

sys.path.insert(1, 'libs')
sys.path.insert(1, 'source/libs')
from cfn_flip import flip, to_json
from troposphere import cloudformation, Join, Ref

import json
import boto3
import json
import logging

from utils import *
from resources import *

DEFAULT_BUCKET = os.environ.get('DEFAULT_BUCKET')
logging.basicConfig(level=logging.INFO)


def s3_export(request_id, bucket_name, object_key, troposphere_template,
              template_params):
    if isinstance(bucket_name, Ref):
        bucket_name = template_params[bucket_name.data['Ref']]

    if isinstance(object_key, Ref):
        object_key = template_params[object_key.data['Ref']]

    if bucket_name is None:
        bucket_name = DEFAULT_BUCKET
        object_key = '{}/{}'.format(request_id, object_key)

    logging.info('Upload {} in {}'.format(object_key, bucket_name))
    template = troposphere_template.to_json()
    s3.upload_fileobj(io.BytesIO(template.encode()), bucket_name, object_key)

    return Join('',
                ['https://', bucket_name, '.s3.amazonaws.com/', object_key])


def get_stack_template(request_id, resource_obj, resource_id, template_params,
                       import_template):
    bucket_name = resource_obj.properties.get('TemplateBucket', None)
    object_key = resource_obj.properties.get('TemplateKey',\
        resource_obj.properties.get('Path',\
            resource_obj.properties.get('Key', None)))

    nested_stack = cloudformation.Stack(title='NS' + resource_id)

    for attr in nested_stack.attributes:
        if hasattr(resource_obj, attr):
            setattr(nested_stack, attr, getattr(resource_obj, attr))

    for prop in nested_stack.propnames:
        if prop in resource_obj.properties:
            setattr(nested_stack, prop, resource_obj.properties.get(prop))
    nested_stack.TemplateURL = s3_export(request_id, bucket_name, object_key,
                                         import_template, template_params)

    return nested_stack


def get_attributes(resource_obj, main_template, resource_id):
    rules = []
    for attr in ['Condition']:
        if hasattr(resource_obj, attr) and hasattr(main_template,
                                                   'conditions'):
            key = getattr(resource_obj, attr)
            rules += [{
                'key': key,
                'value': getattr(main_template, 'conditions').get(key)
            }]
            break

    return rules[-1] if len(rules) > 0 else None


def handle_template(request_id, main_template, template_params, aws_region):
    main_template = TemplateLoader.loads(main_template)

    merge_template = TemplateLoader.init()
    merge_template.parameters = main_template.parameters
    merge_template.conditions = main_template.conditions

    for resource_id, resource_obj in main_template.resources.items():
        if not isinstance(resource_obj, Template):
            merge_template.add_resource(resource_obj)
        else:
            mode = resource_obj.properties.get('Mode', 'Inline')
            import_template = TemplateLoader.loads(
                get_template(request_id, resource_id, resource_obj,
                             template_params, aws_region))
            if mode.lower() == 'inline':
                logging.warning(
                    '[{}] Inline mode is not supported.'.format(resource_id))

            stack_template = get_stack_template(request_id, resource_obj,
                                                resource_id, template_params,
                                                import_template)
            merge_template.add_resource(stack_template)

    if any([
            isinstance(res, S3) or isinstance(res, Git)
            for res in merge_template.resources.values()
    ]):
        logging.info('Recursive Call.')
        return handle_template(request_id,
                               json.loads(merge_template.to_json()),
                               template_params, aws_region)
    return json.loads(merge_template.to_json())


def handler(event, context):
    logging.debug(json.dumps(event))

    macro_response = {
        'fragment': event['fragment'],
        'status': 'success',
        'requestId': event['requestId']
    }

    path = '/tmp/' + event['requestId']

    try:
        os.mkdir(path)
        os.mkdir(path + '/github')
    except OSError:
        logging.warning('Creation of the directory %s failed' % path)
    else:
        logging.info('Successfully created the directory %s ' % path)

    try:
        macro_response['fragment'] = handle_template(
            event['requestId'], event['fragment'],
            event['templateParameterValues'], event['region'])
        logging.debug(json.dumps(macro_response['fragment']))
    except Exception as e:
        traceback.print_exc()
        macro_response['status'] = 'failure'
        macro_response['errorMessage'] = str(e)

    return macro_response


if __name__ == '__main__':
    with open('./source/event.json') as json_file:
        event = json.load(json_file)
    handler(event, None)
