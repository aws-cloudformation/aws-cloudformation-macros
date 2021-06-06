# Template Macro

The `Template` macro adds the ability to create CloudFormation resources from existing Cloudformation Templates. You can reference templates that are saved both in Git Repository and S3 Bucket. A typical use case for this macro might be to reuse Cloudformation configurations that let you manage a group of related resources as if they were a single resource.

You can recursive import Templates, Template::S3 and Template::Git are allowed in imported Cloudformation Templates.

This Macro uses [Troposphere](https://github.com/cloudtools/troposphere).

# How to install and use the Macro in your AWS account

## Deploying

1. You will need an S3 bucket to store the CloudFormation artifacts:
    * If you don't have one already, create one with `aws s3 mb s3://<bucket name>`

2. Install all python requirements

    ```shell
    pip install -r source/requirements.txt -t source/libs
    ```

3. Package the CloudFormation template. The provided template uses [the AWS Serverless Application Model](https://aws.amazon.com/about-aws/whats-new/2016/11/introducing-the-aws-serverless-application-model/) so must be transformed before you can deploy it.

    ```shell
    aws cloudformation package \
        --template-file template.yaml \
        --s3-bucket <your bucket name here> \
        --output-template-file template.output
    ```

4. Deploy the packaged CloudFormation template to a CloudFormation stack:

    ```shell
    aws cloudformation deploy \
        --stack-name template-macro \
        --template-file template.output \
        --capabilities CAPABILITY_IAM
    ```

5. To test out the macro's capabilities, try launching the provided example template:

    ```shell
    aws cloudformation package \
    	--template-file example.yaml 
    	--s3-bucket <your bucket name here> \
    	--output-template-file example.output

    aws cloudformation deploy \
    	--template-file ./example.output \
    	--stack-name TemplateExample \
    	--region <select your region> \
    	--capabilities CAPABILITY_AUTO_EXPAND
    ```


# Custom Resources

This Macro uses two Custom Resources.

- Template::Git
- Template::S3

## Template::Git

The Template::Git imports Cloudformation Template from Git Repository.

### Syntax

To declare this entity in your AWS CloudFormation template use the following syntax:

#### JSON
```
{
  "Type" : "Template::Git",
  "Properties" : {
  	  "Mode": String,
  	  "Provider": String,
  	  "Repo": String,
	  "Project" : String,
  	  "Branch": String,
  	  "Owner": String,
  	  "OAuthToken": String,
  	  "Path": String,
      "Parameters" : {Key : Value, ...},
      "NotificationARNs" : [ String, ... ],
      "Tags" : [ Tag, ... ],
      "TimeoutInMinutes" : Integer,
      "TemplateBucket" : String,
      "TemplateKey" : String,
    }
}
```

#### YAML
```
Type: Template::Git
Properties: 
  Mode: String
  Provider: String
  Repo: String
  Project: String
  Branch: String
  Owner: String
  OAuthToken: String
  Path: String
  Parameters:
  	Key : Value
  NotificationARNs:
    - NotificationARN
  Tags: 
    - Tag 
  TimeoutInMinutes: Integer
  TemplateBucket: String
  TemplateKey: String
`````

### Properties

`Mode`

Specifies whether to import the template inline or as [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) resource.

If Nested mode is used Macro automatically uploads Template into S3 Bucket when TemplateBucket, TemplateKey or Path parameters are provided as String or by using the intrinsic function [Ref](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html). 

If Inline mode is used you can reference resource in imported Template using the intrinsic functions [Ref](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html) and [Fn::GetAtt](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html) with the _Template::_ prefix. 

For example, you can obtain the Arn of a resource inside imported template using GetAtt, you can reference resource inside imported template using Ref:

- ```Fn::GetAtt: [ Template::TemplateName::LogicalName, attributeName ]```

- ```Ref: Template::TemplateName::LogicalName```

Nested mode suppors all attributes you can use with AWS::CloudFormation::Stack while Inline mode supports DeletionPolicy, DependsOn, UpdatePolicy [Resource Attributes](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-product-attribute-reference.html) and [Conditions](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/conditions-section-structure.html).

You can define dependency to Template resource using _Template::_ prefix.

- ```DependsOn: Template::TemplateName```

_Required_: Yes

_Type_: String

_Allowed Values_:  Inline | Nested


`Provider`

Specifies from where to import template. There are two valid values for the Provider field: Codecommit, GitHub. If the Provider field is Codecommit you must ensure that your lambda macro has the permission to clone the repository, please check the lambda role. If the Provider field is GitHub you need also to specify the Owner field and OAuthToken if you are referencing private repository. 

_Required_: Yes

_Type_: String

_Allowed Values_:  Codecommit | GitHub | Gitlab

`Repo`

The name of the repository.

_Required_: Yes

_Type_: String

`Project`

The name of the project for your GitLab codebase.

Conditional. Required if Provider is Gitlab

_Required_: Conditional

_Type_: String

`Branch`

The branch repository.

_Required_: No

_Type_: String

_Default_: master


`Owner`

The name of the GitHub user.

Conditional. Required if Provider is GitHub

_Required_: Conditional

_Type_: String


`OAuthToken`

It is the GitHub authentication token that allows Macro to perform operations on your GitHub repository. 

Conditional. Required if Provider is GitHub | Gitlab

_Required_: Conditional

_Type_: String

`Path`

Specifies the path of the template inside the repository.

_Required_: Yes

_Type_: String

_Example_: path/to/file/template.yaml

`Parameters`

The set value pairs that represent the parameters passed to Macro when the template is imported. Each parameter has a name corresponding to a parameter defined in the embedded template and a value representing the value that you want to set for the parameter.

_Required_: No

_Type_: Map of String

`NotificationARNs`

The Simple Notification Service (SNS) topic ARNs to publish stack related events. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) for more informations.

_Required_: No

_Type_: List of String

`Tags`

Key-value pairs to associate with nested stack. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) for more informations.

_Required_: No

_Type_: List of [Tag](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-resource-tags.html)

`TimeoutInMinutes`

The length of time, in minutes, that CloudFormation waits for the nested stack to reach the CREATE_COMPLETE state. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) for more informations.

_Required_: No

_Type_: Integer

_Minimum_: 1


`TemplateBucket`

The name of the S3 Bucket where template from git is uploaded. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) TemplateURL section for more informations. The default bucket is created within macro transformation. 


_Required_: No

_Type_: String

_Default_: macro-template-default-<AccountId>-<Region>


`TemplateKey`

The path where template from git is saved in the S3 Bucket . Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) TemplateURL section for more informations.

> :warning: **This override the object if already exist**: Be very careful here!

_Required_: No

_Type_: String

_Default_: same value as Path field


## Template::S3

The Template::S3 imports Cloudformation Template from S3 Bucket. This is an improvemend over [AWS::Include Transform](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/create-reusable-transform-function-snippets-and-add-to-your-template-with-aws-include-transform.html), while AWS::Include let you import configuration snippet from S3 with Template::S3 you can import the whole Cloudforamtion Template.


### Syntax

To declare this entity in your AWS CloudFormation template use the following syntax:

#### JSON
```
{
  "Type" : "Template::S3",
  "Properties" : {
  	  "Mode": String,
  	  "Bucket": String,
  	  "Key": String,
      "Parameters" : {Key : Value, ...},
      "NotificationARNs" : [ String, ... ],
      "Tags" : [ Tag, ... ],
      "TimeoutInMinutes" : Integer,
      "TemplateBucket" : String,
      "TemplateKey" : String,
    }
}
```

#### YAML
```
Type: Template::S3
Properties: 
  Mode: String
  Bucket: String
  Key: String
  Parameters:
  	Key : Value
  NotificationARNs:
    - NotificationARN
  Tags: 
    - Tag 
  TimeoutInMinutes: Integer
  TemplateBucket: String
  TemplateKey: String
`````

### Properties


`Mode`

Specifies whether to import the template inline or as [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) resource.

If Nested mode is used Macro automatically uploads Template into S3 Bucket when TemplateBucket, TemplateKey or Path parameters are provided as String or by using the intrinsic function [Ref](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html). 

If Inline mode is used you can reference resource in imported Template using the intrinsic functions [Ref](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html) and [Fn::GetAtt](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html) with the _Template::_ prefix. 

For example, you can obtain the Arn of a resource inside imported template using GetAtt, you can reference resource inside imported template using Ref:

- ```Fn::GetAtt: [ Template::TemplateName::LogicalName, attributeName ]```

- ```Ref: Template::TemplateName::LogicalName```

Nested mode suppors all attributes you can use with AWS::CloudFormation::Stack while Inline mode supports DeletionPolicy, DependsOn, UpdatePolicy [Resource Attributes](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-product-attribute-reference.html) and [Conditions](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/conditions-section-structure.html).

You can define dependency to Template resource using _Template::_ prefix. 

- ```DependsOn: Template::TemplateName```

_Required_: Yes

_Type_: String

_Allowed Values_:  Inline | Nested


`Bucket`

The name of the S3 Bucket from where the template is dowloaded.

_Required_: Yes

_Type_: String


`Key`

The path from where the template is dowloaded.

_Required_: Yes

_Type_: String

`Parameters`

The set value pairs that represent the parameters passed to Macro when the template is imported. Each parameter has a name corresponding to a parameter defined in the embedded template and a value representing the value that you want to set for the parameter.

_Required_: No

_Type_: Map of String

`NotificationARNs`

The Simple Notification Service (SNS) topic ARNs to publish stack related events. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) for more informations.

_Required_: No

_Type_: List of String

`Tags`

Key-value pairs to associate with nested stack. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) for more informations.

_Required_: No

_Type_: List of [Tag](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-resource-tags.html)

`TimeoutInMinutes`

The length of time, in minutes, that CloudFormation waits for the nested stack to reach the CREATE_COMPLETE state. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) for more informations.

_Required_: No

_Type_: Integer

_Minimum_: 1


`TemplateBucket`

The name of the S3 Bucket where template from git is uploaded. Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) TemplateURL section for more informations. The default bucket is created within macro transformation. 


_Required_: No

_Type_: String

_Default_: macro-template-default-<AccountId>-<Region>


`TemplateKey`

The path where template from git is saved in the S3 Bucket . Refer to [AWS::CloudFormation::Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html) TemplateURL section for more informations.

> :warning: **This override the object if already exist**: Be very careful here!

_Required_: No

_Type_: String

_Default_: Key field

### Examples

#### Import Template Inline From Codecommit

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": {
      "Template": {
         "Type": "Template::Git",
         "Properties": {
            "Mode": "Inline",
            "Provider": "Codecommit",
            "Repo": { 
	       	  "Ref" : "RepositoryName" 
	        },
            "Branch": { 
	       	  "Ref" : "BranchName" 
	        },
            "Path": { 
	       	  "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "codecommit-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  Environment:
    Type: String
    Default: dev

Resources:
  Template:
    Type: "Template::Git"
    Properties:
      Mode: Inline
      Provider: Codecommit
      Repo: !Ref RepositoryName
      Branch: !Ref BranchName
      Path: !Ref TemplateKey
      Parameters:
        Name: "codecommit-example"
        Environment: !Ref Environment
```

#### Import Template Inline From Github

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "GitHubUser": {
         "Type": "String",
         "Default": "user"
      },
      "GitHubToken": {
         "Type": "String",
         "Default": "OAuthToken"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": {
      "Template": {
         "Type": "Template::Git",
         "Properties": {
            "Mode": "Inline",
            "Provider": "Github",
            "Repo": { 
	       	   "Ref" : "RepositoryName" 
	        },
            "Branch": { 
	       	   "Ref" : "BranchName" 
	        },
            "Owner": { 
	       	   "Ref" : "GitHubUser" 
	        },
            "OAuthToken": { 
	       	   "Ref" : "GitHubToken" 
	        },
            "Path": { 
	       	   "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "github-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  GitHubUser:
    Type: String
    Default: user
  GitHubToken:
    Type: String
    Default: OAuthToken
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  Environment:
    Type: String
    Default: dev

Resources:
  Template:
    Type: "Template::Git"
    Properties:
      Mode: Inline
      Provider: Github
      Repo: !Ref RepositoryName
      Branch: !Ref BranchName
      Owner: !Ref GitHubUser
      OAuthToken: !Ref GitHubToken
      Path: !Ref TemplateKey
      Parameters:
        Name: "github-example"
        Environment: !Ref Environment
```

#### Import Template Nested

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "GitHubUser": {
         "Type": "String",
         "Default": "user"
      },
      "GitHubToken": {
         "Type": "String",
         "Default": "OAuthToken"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "TemplateBucket": {
         "Type": "String",
         "Default": "example-bucket"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": null,
   "Notification": {
      "Type": "AWS::SNS::Topic",
      "Properties": {
         "TopicName": "topic-name"
      }
   },
   "Template": {
      "Type": "Template::Git",
      "Properties": {
         "Mode": "Nested",
         "Provider": "Github",
         "Repo": { 
	       "Ref" : "RepositoryName" 
	     },
         "Branch": { 
	       	"Ref" : "BranchName" 
	     },
         "Owner": { 
	       	"Ref" : "GitHubUser" 
	     },
         "OAuthToken": { 
	       	"Ref" : "GitHubToken" 
	     },
         "Path": { 
	       	"Ref" : "TemplateKey" 
	     },
         "Parameters": {
            "Name": "github-example",
            "Environment": { 
	       	    "Ref" : "Environment" 
	        }
         },
         "NotificationARNs": [
            { 
            	"Fn::GetAtt" : [ "Notification", "Arn" ] 
            }
         ],
         "Tags": [
            {
               "Key": "Environment",
               "Value": { 
	       	      "Ref" : "Environment" 
	            }
            }
         ],
         "TimeoutInMinutes": 1,
         "TemplateBucket": { 
	       	"Ref" : "TemplateBucket" 
	     },
         "TemplateKey": { 
	       	"Ref" : "TemplateKey" 
	     }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  GitHubUser:
    Type: String
    Default: user
  GitHubToken:
    Type: String
    Default: OAuthToken
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  BucketName:
    Type: String
    Default: example-bucket
  Environment:
    Type: String
    Default: dev

Resources:

Notification:
  Type: "AWS::SNS::Topic"
  Properties: 
    TopicName: 'topic-name'

Template:
  Type: "Template::Git"
  Properties:
    Mode: Nested
    Provider: Github
    Repo: !Ref RepositoryName
    Branch: !Ref BranchName
    Owner: !Ref GitHubUser
    OAuthToken: !Ref GitHubToken
    Path: !Ref TemplateKey
    Parameters:
      Name: "github-example"
      Environment: !Ref Environment
    NotificationARNs:
      - !GetAtt Notification.Arn
    Tags: 
      - Key: Environment
        Value: !Ref Environment
    TimeoutInMinutes: 1
    TemplateBucket: !Ref BucketName
    TemplateKey: !Ref TemplateKey
```

#### Import Multiple Template

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "GitHubUser": {
         "Type": "String",
         "Default": "user"
      },
      "GitHubToken": {
         "Type": "String",
         "Default": "OAuthToken"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "BucketName": {
         "Type": "String",
         "Default": "example-bucket"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": {
      "TemplateGit": {
         "Type": "Template::Git",
         "Properties": {
            "Mode": "Inline",
            "Provider": "Github",
            "Repo": { 
	       	  "Ref" : "RepositoryName" 
	        },
            "Branch": { 
	       	   "Ref" : "BranchName" 
	        },
            "Owner": { 
	       	   "Ref" : "GitHubUser" 
	        },
            "OAuthToken": { 
	       	   "Ref" : "GitHubToken" 
	        },
            "Path": { 
	       	   "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "github-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      },
      "TemplateS3": {
         "Type": "Template::S3",
         "Properties": {
            "Mode": "Inline",
            "Provider": "S3",
            "Bucket": { 
	       	  "Ref" : "BucketName" 
	        },
            "Key": { 
	       	  "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "s3-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  GitHubUser:
    Type: String
    Default: user
  GitHubToken:
    Type: String
    Default: OAuthToken
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  BucketName:
    Type: String
    Default: example-bucket
  Environment:
    Type: String
    Default: dev

Resources:
  TemplateGit:
    Type: "Template::Git"
    Properties:
      Mode: Inline
      Provider: Github
      Repo: !Ref RepositoryName
      Branch: !Ref BranchName
      Owner: !Ref GitHubUser
      OAuthToken: !Ref GitHubToken
      Path: !Ref TemplateKey
      Parameters:
        Name: "github-example"
        Environment: !Ref Environment


  TemplateS3:
    Type: "Template::S3"
    Properties:
      Mode: Inline
      Provider: S3
      Bucket: !Ref BucketName
      Key: !Ref TemplateKey
      Parameters:
        Name: 's3-example'
        Environment: !Ref Environment
```

# Work in Progress

- auto tag resource in the imported template using tag property

- let user to provide git credentials as aws secret

- use metadata

- select commit tag

