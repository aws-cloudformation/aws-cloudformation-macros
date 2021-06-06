# Map Parameter

CloudFormation Macro that enables the use of Maps/JSON objects as Input Parameters.

## Basic Usage

Use the Transform to retrieve the value from a key-value input parameter of type JSON/Dict/Map as shown below. The value in a nested map can be retrieved by using a hierarchical traversal format like "K1.K2.K3" (K3 being the innermost Key)

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: Test template for Map macro
Parameters:
  MapParameter:
    Description: Enter the Map/JSON
    Default: '{"K1": {"K2":{"K2":{"K2":"Nested"}}, "K3": {"K4": "V4"}}}'
    Type: String
Resources:
  S3Bucket:
    Type: 'AWS::S3::Bucket'
    Properties:
      Tags:
        - Key: Outer
          Value:
            'Fn::Transform':
              - Name: Map
                Parameters:
                  MapParameter: !Ref MapParameter
                  Key: K1.K2.K2.K2
        - Key: Inner
          Value:
            'Fn::Transform':
              - Name: Map
                Parameters:
                  MapParameter: !Ref MapParameter
                  Key: K1.K3.K4

```


## Author

[Akshit Khanna](https://github.com/akshitkh)  
