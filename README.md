# AWS CloudFormation Macros

This repository hosts examples of AWS CloudFormation macros.

## Contents

* [Boto3](Boto3)

    The `Boto3` macro adds the ability to create CloudFormation resources that represent operations performed by [boto3](http://boto3.readthedocs.io/). Each `Boto3` resource represents one function call.

* [Count](Count)

    The `Count` macro provides a template-wide `Count` property for CloudFormation resources. It allows you to specify multiple resources of the same type without having to cut and paste.

* [ExecutionRoleBuilder](ExecutionRoleBuilder)

    The `Execution Role Builder` macro provides a more natural syntax for developers to express the permissions they want to attach to IAM execution roles for their applications, while simultaneously providing IAM administrators with a way to templatize those permissions. When used in conjunction with permission boundaries, this provides an effective solution for delegated role creation.

* [Explode](Explode)

    The `Explode` macro provides a template-wide `Explode` property for CloudFormation resources. Similar to the Count macro, it will create multiple copies of a template Resource, but looks up values to inject into each copy in a Mapping.

* [Public-and-Private-Subnet-per-AZ](Public-and-Private-Subnet-per-AZ)

    This is a Cloudformation Macro used to dynamically add a public and private subnet per Availability Zone when launching a template.  When the CreateStack template is launched and a change set is created, the Macro (named 'CreateSubnetsPerAZ') will dynamically add resources to the template for a public and private subnet per available AZ

* [PyPlate](PyPlate)

    Run arbitrary python code in your CloudFormation templates

* [S3Objects](S3Objects)

    The `S3Objects` macro adds a new resource type: `AWS::S3::Object` which you can use to populate an S3 bucket.

* [ShortHand](ShortHand)

    The `ShortHand` macro provides convenience syntax to allow you to create short CloudFormation templates that expand into larger documents upon deployment to a stack.

* [StackMetrics](StackMetrics)

    When the `StackMetrics` macro is used in a CloudFormation template, any CloudFormation stack deployed from that template will output custom CloudWatch metrics for the stack.

* [StringFunctions](StringFunctions)

    Provides string transformation utility functions.

## License

This library is licensed under the Apache 2.0 License. 
