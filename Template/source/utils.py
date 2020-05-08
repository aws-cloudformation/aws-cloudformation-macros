import json, re
import troposphere as tp
from troposphere.template_generator import TemplateGenerator
from resources import S3, Git


class TemplateLoader(TemplateGenerator):
    __create_key = object()
    __sub_regex = r"(\${[^}]+})"

    @classmethod
    def loads(cls, json_string):
        return TemplateLoader(cls.__create_key,
                              cls._sub_to_join(json_string),
                              CustomMembers=[S3, Git])

    @classmethod
    def init(cls):
        return TemplateLoader.loads({
            'Description': 'This template is the result of the merge.',
            'Resources': {}
        })

    @classmethod
    def _sub_to_join(cls, template):
        template_clone = json.loads(json.dumps(template))
        cls._translate_value(template_clone)
        return json.loads(
            json.dumps(template_clone).replace('Fn::Sub', 'Fn::Join'))

    @classmethod
    def _translate_value(cls, template):
        if type(template) == dict:
            for key in template:
                if key == 'Fn::Sub':
                    try:
                        split_list = [
                            s for s in re.split(cls.__sub_regex, template[key])
                            if len(s) > 0
                        ]
                    except TypeError:
                        raise ('Error with', template[key], key)
                    for index, value in enumerate(split_list):
                        if re.match(cls.__sub_regex, value):
                            split_list[index] = tp.Ref(value[2:-1]).data
                    template[key] = ["", split_list]
                cls._translate_value(template[key])

    def __init__(self, create_key, cf_template=None, **kwargs):
        assert(create_key == TemplateLoader.__create_key), \
            "TemplateLoader objects must be created using TemplateLoader.loads or TemplateLoader.init"
        super(TemplateLoader, self).__init__(cf_template, **kwargs)
        self._to_replace = []

    def __iter__(self):
        fields = list(vars(self).keys())
        for props in fields:
            yield (props, getattr(self, props))

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __iadd__(self, other):
        for props in self:
            key, value = props
            if key.startswith('_') or key in ['version', 'transform']:
                continue

            if key == 'description':
                if value == '':
                    continue
                self[key] = "" if self[key] is None else self[key]
                other[key] = "" if other[key] is None else other[key]

                self[key] = "{} {}".format(self[key], other[key])
            else:
                self[key] = {**self[key], **other[key]}
        return self

    @staticmethod
    def __setattr(bucket, key, value):
        if type(key) == int:
            bucket[key] = value
        if type(key) == str:
            if hasattr(bucket, key):
                setattr(bucket, key, value)
            else:
                bucket[key] = value

    def to_json(self, keep_parameters=True):
        json_string = super().to_json()
        if keep_parameters:
            return json_string
        else:
            json_obj = json.loads(json_string)
            if 'Parameters' in json_obj:
                del json_obj['Parameters']
            return json.dumps(json_obj)

    def to_yaml(self, keep_parameters=True):
        json_string = self.to_json(keep_parameters)
        return flip(json_string)
