import sys

sys.path.insert(1, 'libs')
sys.path.insert(1, 'source/libs')

import os
import json
import logging
import traceback
import urllib.parse

from resources import *
from loader import *
from simulator import *
from utils import *

logging.basicConfig(level=logging.INFO)

def handle_template(main_template):
    merge_template = TemplateLoader.init(main_template.parameters)

    template_collection = TemplateLoaderCollection()

    for resource_id, resource_obj in main_template.resources.items():
        if not resource_obj.is_macro():
            merge_template.add_resource(resource_obj)

            logging.info('Add AWS Resource {}'.format(resource_id))

        else:
            mode = resource_obj.properties.get('Mode', 'Inline')

            if mode.lower() == 'nested':
                merge_template.add_resource(
                    resource_obj.get_stack_template()
                )

                logging.info('Add Template Resource {}, Mode={}'.format(resource_id, mode))

            if mode.lower() == 'inline':
                import_template = TemplateLoader.loads(
                    resource_obj.get_template()
                )

                import_template = import_template.translate(prefix=resource_id)

                template_collection.update({
                    resource_id : (resource_obj, import_template)
                })

                logging.info('Add Template Resource {}, Mode={}'.format(resource_id, mode))

    merge_template.add_templates(template_collection)

    if merge_template.is_template_contains_custom_resources():
        logging.info('Recursive Call.')
        return handle_template(merge_template)

    return merge_template


def create_local_path(requestId):
    path = '/tmp/' + requestId
    try:
        os.mkdir(path)
        os.mkdir(path + '/github')
    except OSError:
        logging.warning('Creation of the directory %s failed' % path)
    else:
        logging.info('Successfully created the directory %s ' % path)
    return requestId


def handler(event, context):
    logging.debug("Input:", json.dumps(event))

    request_id = create_local_path(event['requestId'])
    parameters = event['templateParameterValues']

    cfn = Simulator(event['fragment'], parameters)
    template = cfn.simulate(excude_clean=['Parameters'])
    template = TemplateLoader.loads(template)

    macro_response = {
        'status': 'success',
        'requestId': request_id
    }

    Macro.aws_cfn_request_id = request_id
    Macro.template_params = parameters
    Macro.aws_region = event['region']

    try:
        template = handle_template(template)

        template = template.evaluate_custom_expression()

        macro_response['fragment'] = template.to_dict()

        logging.debug("Output:", json.dumps(event))
    except Exception as e:
        traceback.print_exc()
        macro_response['status'] = 'failure'
        macro_response['errorMessage'] = str(e)

    return macro_response
