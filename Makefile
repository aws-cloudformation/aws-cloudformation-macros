MACROS = Boto3 Count ExecutionRoleBuilder Explode PublicAndPrivateSubnetPerAZ PyPlate S3Objects ShortHand StackMetrics StringFunctions

.PHONY: $(MACROS)

all: $(MACROS)

delete:
	for i in $(MACROS); do \
		cd $$i; \
		sam delete --no-prompts --region $(REGION); \
		cd ..; \
	done

all_embedded:
	sam deploy

delete_embedded:
	sam delete --no-prompts --region $(REGION)

$(MACROS):
	cd $@ && sam deploy
