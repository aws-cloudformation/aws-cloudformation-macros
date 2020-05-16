# PyPlate

Run arbitrary Python code in your CloudFormation templates.

## Basic Usage

Place Python code as a literal block anywhere in your template. The literal block will be replaced with the contents of
the `output` variable defined in your code. There are several variables available to your code:

- `params`: dict containing the contents of the templateParameterValues
- `template`: dict containing the entire template
- `account_id`: AWS account ID
- `region`: AWS region

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: tests String macro functions
Parameters:
  Tags:
    Default: "Env=Prod,Application=MyApp,BU=ModernisationTeam"
    Type: "CommaDelimitedList"
Resources:
  S3Bucket:
    Type: "AWS::S3::Bucket"
    Properties:
      Tags: |
        #!PyPlate
        output = []
        for tag in params['Tags']:
           key, value = tag.split('=')
           output.append({"Key": key, "Value": value})
Transform: [PyPlate]
```

## Author

[Jay McConnell](https://github.com/jaymccon)  
Partner Solutions Architect  
Amazon Web Services
