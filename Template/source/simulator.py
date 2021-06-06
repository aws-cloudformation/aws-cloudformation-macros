import re
import logging


logging.basicConfig(level=logging.INFO)

class Simulator():
    __params_regexp = r'\${AWS::[a-zA-Z0-9_]*}|\${[a-zA-Z0-9_]*}'
    __getatt_regexp = r'\${[a-zA-Z0-9_]*\.[a-zA-Z0-9_]*}'

    def __init__(self, template, params={}):
        import os

        self.data = template
        self.values = {
            'AWS::Region': os.environ.get('REGION', 'us-east-1'),
            'AWS::AccountId': os.environ.get('ACCOUNT', '1234567890'),
            'Template::DefaultBucket': os.environ.get('DEFAULT_BUCKET', 'macro-template-default-831650818513-us-east-1'),
            **{
                key: self.data.get('Parameters')[key]['Default']
                for key in self.data.get('Parameters', {}) if 'Default' in self.data.get(
                    'Parameters', {}).get(key, {})
            },
            **params
        }

    def simulate(self, excude_clean=[]):
        from copy import deepcopy

        self.template = deepcopy(self.data)

        self.template = self.expand_parameters(self.template)

        self.template = self.sub_to_join(self.template)

        self.template = self.evaluate_expression(self.template)

        self.template = self.handle_conditions(self.template)

        self.template = self.arrayfy_depends_on(self.template)

        self.template = self.cleanup(self.template, excude_clean)

        return self.template

    def sub_to_join(self, data):
        if type(data) == dict:
            if 'Fn::Sub' in data:
                sub_values = data['Fn::Sub']

                if type(sub_values) == str:
                    sub_string, sub_map = sub_values, {}
                if type(sub_values) == list:
                    sub_string, sub_map = sub_values

                join_values = re.split('('+self.__params_regexp+'|'+self.__getatt_regexp+')', sub_string)
                for index, element in enumerate(join_values):
                    if re.findall(self.__params_regexp, element):
                        reference_key = element[2:-1]
                        join_values[index] = sub_map.get(reference_key, 
                            {"Ref": reference_key})
                    if re.findall(self.__getatt_regexp, element):
                        reference_key = element[2:-1].split(".")
                        join_values[index] = {"Fn::GetAtt": reference_key}

                del data['Fn::Sub']

                data['Fn::Join'] = [ "" , self.sub_to_join([i for i in join_values if i]) ]

                return data
            else:
                return dict(filter(lambda x: not x is None, map(self.sub_to_join, data.items())))

        if type(data) == list:
            return list(filter(lambda x: not x is None, map(self.sub_to_join, data)))

        if type(data) == tuple:
            return (data[0], self.sub_to_join(data[1]))

        return data

    def expand_parameters(self, data):

        if type(data) == dict:
            value = self.values.get(data.get('Ref'))
            if value is None:
                return {key: self.expand_parameters(data[key]) for key in data}
            else:
                return value

        if type(data) == list:
            return [self.expand_parameters(d) for d in data]

        if type(data) == str:
            matches = re.finditer(self.__params_regexp, data, re.MULTILINE)
            for match in matches:
                param = match.group()
                value = self.values.get(param[2:-1], param)
                data = data.replace(param, str(value))
        return data

    def _split(self, delimiter, text):
        try:
            return text.split(delimiter)
        except Exception as e:
            logging.error('Fault assumption: _split {}'.format(e))
            logging.warning('Fault assumption: _split("{}",{})'.format(
                delimiter, text))
            return {"Fn::Split": [delimiter, text]}

    def _equals(self, a, b):
        try:
            return a == b
        except Exception as e:
            logging.error('Fault assumption: _equals {}'.format(e))
            logging.warning('Fault assumption: _equals({},{})'.format(a, b))
            return {"Fn::Equals": [a, b]}

    def _or(self, *args):
        try:
            return any(args)
        except Exception as e:
            logging.error('Fault assumption: _or {}'.format(e))
            logging.warning('Fault assumption: _or({})'.format(args))
            return {"Fn::Or": args}

    def _not(self, arg):
        try:
            return not arg
        except Exception as e:
            logging.error('Fault assumption: _not {}'.format(e))
            logging.warning('Fault assumption: _not({})'.format(arg))
            return {"Fn::Not": [arg]}

    def _and(self, *args):
        try:
            return all(args)
        except Exception as e:
            logging.error('Fault assumption: _and {}'.format(e))
            logging.warning('Fault assumption: _and({})'.format(args))
            return {"Fn::And": args}

    def _join(self, delimiter, words):
        try:
            return delimiter.join(words)
        except Exception as e:
            #logging.error('Fault assumption: _join {}'.format(e))
            #logging.warning('Fault assumption: _join("{}", {}).'.format(delimiter, words))
            return {"Fn::Join": [delimiter, words]}

    def _if(self, condition_name, value_if_true, value_if_false):
        try:
            return value_if_true if self._condition(
                condition_name) else value_if_false
        except Exception as e:
            logging.error('Fault assumption: _if {}'.format(e))
            logging.warning('Fault assumption: _if({}, {}, {})'.format(
                cond, opt_true, opt_false))
            return {"Fn::If": [condition_name, value_if_true, value_if_false]}

    def _find(self, map_name, top_level_key, second_level_key=None):
        try:
            if second_level_key:
                return self.template['Mappings'][map_name][top_level_key][
                    second_level_key]
            else:
                return self.template['Mappings'][map_name][top_level_key]
        except Exception as e:
            logging.error('Fault assumption: _find {}'.format(e))
            logging.warning('Fault assumption: _find({}, {}, {})'.format(
                map_name, top_level_key, second_level_key))
            return {
                "Fn::FindInMap":
                list(filter(None, [map_name, top_level_key, second_level_key]))
            }

    def _select(self, index, words):
        try:
            return words[int(index)]
        except Exception as e:
            logging.error('Fault assumption: _select {}'.format(e))
            logging.warning('Fault assumption: _select({}, {})'.format(
                index, words))
            return {"Fn::Select": [int(index), words]}

    def _sub(self, args):
        try:
            if type(args) == list:
                return self._join("", args)
            if re.findall(self.__params_regexp, args):
                return {"Fn::Sub": args}
            return args
        except Exception as e:
            logging.error('Fault assumption: _sub {}'.format(e))
            logging.warning('Fault assumption: _sub({})'.format(args))
            return {"Fn::Sub": args}

    def _condition(self, condition_name):
        try:
            cond_expr = self.template['Conditions'][condition_name]
            eval_expr = self.evaluate_expression(cond_expr)
            return eval_expr
        except Exception as e:
            logging.error('Fault assumption: _condition {}'.format(e))
            logging.warning(
                'Fault assumption: _condition({})'.format(condition_name))
            return condition_name

    def evaluate_expression(self, data):
        if type(data) == dict and "Fn::Split" in data:
            evaluated_params = self.evaluate_expression(data["Fn::Split"])
            return self._split(*evaluated_params)

        if type(data) == dict and "Fn::Equals" in data:
            evaluated_params = self.evaluate_expression(data["Fn::Equals"])
            return self._equals(*evaluated_params)

        if type(data) == dict and "Fn::Or" in data:
            evaluated_params = self.evaluate_expression(data["Fn::Or"])
            return self._or(*evaluated_params)

        if type(data) == dict and "Fn::Not" in data:
            evaluated_params = self.evaluate_expression(data["Fn::Not"])
            return self._not(evaluated_params)

        if type(data) == dict and "Fn::And" in data:
            evaluated_params = self.evaluate_expression(data["Fn::And"])
            return self._and(*evaluated_params)

        if type(data) == dict and "Fn::Join" in data:
            evaluated_params = self.evaluate_expression(data["Fn::Join"])
            return self._join(*evaluated_params)

        if type(data) == dict and "Fn::FindInMap" in data:
            evaluated_params = self.evaluate_expression(data["Fn::FindInMap"])
            return self._find(*evaluated_params)

        if type(data) == dict and "Fn::If" in data:
            evaluated_params = self.evaluate_expression(data["Fn::If"])
            return self._if(*evaluated_params)

        if type(data) == dict and "Fn::Select" in data:
            evaluated_params = self.evaluate_expression(data["Fn::Select"])
            return self._select(*evaluated_params)

        if type(data) == dict and "Fn::Sub" in data:
            evaluated_params = self.evaluate_expression(data["Fn::Sub"])
            return self._sub(evaluated_params)

        if type(data) == dict and "Condition" in data:
            if len(data.keys()) == 1:
                return self._condition(data["Condition"])
            else:
                data["Condition"] = self._condition(data["Condition"])

        if type(data) == list:
            return [self.evaluate_expression(d) for d in data]

        if type(data) == dict:
            return {key: self.evaluate_expression(data[key]) for key in data}

        return data

    def arrayfy_depends_on(self, data):
        if type(data) == dict:
            return dict(
                filter(lambda x: not x is None, map(self.arrayfy_depends_on, data.items())))
        if type(data) == list:
            return list(filter(lambda x: not x is None, map(self.arrayfy_depends_on, data)))
        if type(data) == tuple:
            key, value = data
            if key == 'DependsOn':
                if type(value) == list:
                    return (key, value)
                else:
                    return (key, [value])
            else:
                return (key, self.arrayfy_depends_on(value))
        return data

    def handle_conditions(self, data):
        if type(data) == dict:
            return dict(filter(lambda x: not x is None, map(self.handle_conditions,
                                         data.items())))
        if type(data) == list:
            return list(filter(lambda x: not x is None, map(self.handle_conditions, data)))
        if type(data) == tuple:
            key, value = data
            if type(value) == dict:
                if value.pop('Condition', True):
                    return (key, self.handle_conditions(value))
                else:
                    return None
        return data

    def cleanup(self, data, excude_clean):
        tags = ['Mappings', 'Conditions', 'Parameters', 'Transform']

        for tag in [t for t in tags if t not in excude_clean]:
            data.pop(tag, None)

        return data