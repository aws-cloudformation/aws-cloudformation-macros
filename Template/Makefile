BUCKET=audioposts-site
REGION=us-east-1
REPO=template-macro

update:
	aws s3 cp sns-topics.yaml s3://$(BUCKET)/test/sns-topics.yaml

macros:
	pip install -r source/requirements.txt -t source/libs
	aws cloudformation package --template-file template.yaml --s3-bucket $(BUCKET) --output-template-file template.output 
	aws cloudformation deploy --template-file ./template.output --stack-name TemplateMacro --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --region $(REGION) || echo "Continue"
	rm -f ./template.output

example:
	aws cloudformation package --template-file example.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateExamplev1 --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND || echo "Continue"
	rm -f ./example.output