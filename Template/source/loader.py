import boto3
import os
import json

from resources import *
from utils import *

class TemplateLoader(TemplateGenerator):
    __create_key = object()

    @classmethod
    def loads(cls, json_string):
        return TemplateLoader(cls.__create_key,
                              json_string,
                              CustomMembers=[S3, Git])

    @classmethod
    def init(cls, parameters):
        template = TemplateLoader.loads({
            'Description': 'This template is the result of the merge.',
            'Resources': {}
        })
        template.parameters = parameters
        template.set_version()
        return template

    def __init__(self, create_key, cf_template=None, **kwargs):
        assert(create_key == TemplateLoader.__create_key), \
            "TemplateLoader objects must be created using TemplateLoader.loads or TemplateLoader.init"
        super(TemplateLoader, self).__init__(cf_template, **kwargs)

    def __iter__(self):
        fields = list(vars(self).keys())
        for props in fields:
            yield (props, getattr(self, props))

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __iadd__(self, other):
        for key, value in self:
            if key.startswith('_') or key in ['version', 'transform']:
                continue

            if key == 'description':
                self[key] = "{} {}".format(
                    self[key] if self[key] else "", 
                    other[key] if other[key] else ""
                )
            else:
                self[key] = {**self[key], **other[key]}

        return self

    def is_template_contains_custom_resources(self):
        return any([
                res.is_macro()
                for res in self.resources.values()
        ])

    def _evaluate_custom_get(self, args):
        if type(args) == list:
            if Macro.macro_prefix in args[0]:
                args[0] = args[0].replace(Macro.macro_prefix, "")
                return [''.join(args[:-1]).replace(":", ""), args[-1]]

        if type(args) == str:
            return args.replace(Macro.macro_prefix, "").replace(":", "")

        return args

    def _evaluate_custom_ref(self, args):
        if type(args) == list:
            if Macro.macro_prefix in args[0]:
                args[0] = args[0].replace(Macro.macro_prefix, "")
                return ''.join(args).replace(":", "")
        if type(args) == str:
            if args.startswith(Macro.macro_prefix):
                return args.replace(Macro.macro_prefix, "").replace(":", "")

        return args

    def _evaluate_custom_expression(self, data):
        if type(data) == dict and "Fn::GetAtt" in data:
            evaluated_params = self._evaluate_custom_expression(data["Fn::GetAtt"])
            data["Fn::GetAtt"] = self._evaluate_custom_get(evaluated_params)
            return data

        if type(data) == dict and "Ref" in data:
            evaluated_params = self._evaluate_custom_expression(data["Ref"])
            data["Ref"] = self._evaluate_custom_ref(evaluated_params)
            return data

        if type(data) == list:
            return [self._evaluate_custom_expression(d) for d in data]

        if type(data) == dict:
            return {
                key: self._evaluate_custom_expression(data[key])
                for key in data
            }

        return data

    def evaluate_custom_expression(self):
        return self.loads(
            self._evaluate_custom_expression(
                self.to_dict()
            )
        )

    def _get_template_logical_ids(self):
        logical_ids = []
        for prop, value in self:
            if type(value) == dict:
                logical_ids += list(value.keys())
        return logical_ids

    def _translate_custom_reference(self, data):
        if data.startswith(Macro.macro_prefix):
            values = data.split(Macro.macro_separator)
            if values[1] != self.prefix and values[1] in self.logical_ids:
                values.insert(1, self.prefix)
                data = Macro.macro_separator.join(values)

        if data in self.logical_ids:
            data = self.prefix + data

        return data

    def _translate_template(self, data):
        if data in Macro.resources:
            return data

        if type(data) == dict:
            return dict(map(self._translate_template, data.items()))

        if type(data) == list:
            return list(map(self._translate_template, data))

        if type(data) == tuple:
            key, value = data
            if key == 'Ref':
                if value in self.logical_ids:
                    value = self.prefix + value

            if key == "Fn::GetAtt":
                if value[0] in self.logical_ids:
                    value[0] = self.prefix + value[0]

            if key == "Export" and 'Name' in value:
                value["Name"] = {
                    "Fn::Join": ["-", [self.prefix, value["Name"]]]
                }

            return (key, self._translate_template(value))

        if type(data) == str:
            data = self._translate_custom_reference(data)

        return data

    def _translate_logical_ids(self, prefix):
        for prop, value in self:
            if type(value) == dict:
                self[prop] = {(prefix + lid):value[lid]for lid in value.keys()}

    def translate(self, prefix):
        self.prefix = prefix
        self.logical_ids = self._get_template_logical_ids()
        self._translate_logical_ids(prefix)

        json_string = self._translate_template(self.to_dict())
        return self.loads(json_string)

    def _set_deletion_policy(self, macro_resource):
        if hasattr(macro_resource, 'DeletionPolicy'):
            value = getattr(macro_resource, 'DeletionPolicy')
            for title in self.resources:
                setattr(self.resources[title], 'DeletionPolicy', value)

    def _set_update_replace_policy(self, macro_resource):
        if hasattr(macro_resource, 'UpdateReplacePolicy'):
            value = getattr(macro_resource, 'UpdateReplacePolicy')
            for title in self.resources:
                setattr(self.resources[title], 'UpdateReplacePolicy', value)

    def _set_depends_on(self, macro_resource):
        if hasattr(macro_resource, 'DependsOn'):
            for title in self.resources:
                value = list(getattr(macro_resource, 'DependsOn'))
                if hasattr(self.resources[title], 'DependsOn'):
                    value += getattr(self.resources[title], 'DependsOn')
                setattr(self.resources[title], 'DependsOn', value)

    def _translate_depends_on(self, template_collection):
        for title in self.resources:
            current_resource = self.resources[title]

            if hasattr(current_resource, 'DependsOn'):
                depends_on = getattr(current_resource, 'DependsOn')

                depends_on_macro = [
                    d for d in depends_on 
                    if Macro.macro_prefix in d
                ]

                depends_on_aws = [
                    d for d in depends_on 
                    if Macro.macro_prefix not in d
                ]

                for depends_on_value in depends_on_macro:
                    logical_id = Macro.to_logical_id(depends_on_value)

                    if template_collection.contains(logical_id):
                        macro_resource, external_template = template_collection.get(logical_id)
                        for external_title in external_template.resources:
                            external_resource = external_template.resources[external_title]
                            if external_resource.is_macro():
                                depends_on_aws += [Macro.macro_prefix + external_title]
                            else:
                                depends_on_aws += [external_title]
                    else:
                        local_resource = self.resources.get(logical_id)
                        if not local_resource:
                            print(logical_id)
                        if local_resource.is_macro():
                            depends_on_aws += [depends_on_value]
                        else:
                            depends_on_aws.append(logical_id)


                depends_on_aws = list(set(depends_on_aws))
                setattr(self.resources[title], 'DependsOn', depends_on_aws)

    def add_templates(self, template_collection):

        for logical_id, macro_resource, external_template in template_collection:

            external_template._set_deletion_policy(macro_resource)

            external_template._set_update_replace_policy(macro_resource)

            external_template._set_depends_on(macro_resource)

            self += external_template

        self._translate_depends_on(template_collection)



