# This stack is based on the following blog post:
# https://aws.amazon.com/blogs/developer/cdk-pipelines-continuous-delivery-for-aws-cdk-applications/
from aws_cdk import (
    core,
    aws_lambda
)

from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep, ManualApprovalStep
from aws_cdk.aws_codepipeline_actions import LambdaInvokeAction
from aws_cdk.aws_codepipeline import StagePlacement

from makerspace import MakerspaceStage

from accounts_config import accounts
from dns import Domains

class TestStage(core.Stage):
    def __init__(self, scope: core.Construct, stage: str, *,
                 env: core.Environment) -> None:
        super().__init__(scope, stage, env=env)

        self.api_gateway = "https://r90fend561.execute-api.us-east-1.amazonaws.com/prod/"

class Pipeline(core.Stack):
    def __init__(self, app: core.App, id: str, *,
                 env: core.Environment) -> None:
        super().__init__(app, id, env=env)

        # Define our pipeline
        #
        # Our pipeline will automatically create the following stages:
        # Source          – This stage is probably familiar. It fetches the source of your CDK app from your forked
        #                   GitHub repo and triggers the pipeline every time you push new commits to it.
        # Build           – This stage compiles your code (if necessary) and performs a cdk synth. The output of that
        #                   step is a cloud assembly, which is used to perform all actions in the rest of the pipeline.
        # UpdatePipeline  – This stage modifies the pipeline if necessary. For example, if you update your code to add
        #                   a new deployment stage to the pipeline or add a new asset to your application, the pipeline
        #                   is automatically updated to reflect the changes you made.
        # PublishAssets   – This stage prepares and publishes all file assets you are using in your app to Amazon Simple
        #                   Storage Service (Amazon S3) and all Docker images to Amazon Elastic Container Registry
        #                   (Amazon ECR) in every account and Region from which it’s consumed, so that they can be used
        #                   during the subsequent deployments.
        deploy_cdk_shell_step = ShellStep("Synth",
            # use a connection created using the AWS console to authenticate to GitHub
            input=CodePipelineSource.connection("DillonRanwala/unified-makerspace", "pipeline_dev",
                connection_arn="arn:aws:codestar-connections:us-east-1:149497240198:connection/24ef657f-09b9-40ed-bdbf-7f57ea583228"
            ),
            commands=[    
                # install dependancies for frontend
                'cd site/visitor-console',
                'npm install',

                # build for dev
                f'VITE_API_ENDPOINT="https://r90fend561.execute-api.us-east-1.amazonaws.com/prod" npm run build',
                'mkdir -p ../../cdk/visit/console/Dev',
                'cp -r dist/* ../../cdk/visit/console/Dev',

                # build for prod
                # f'VITE_API_ENDPOINT="https://{Domains("Prod").api}" npm run build',
                # 'mkdir -p ../../cdk/visit/console/Prod',
                # 'cp -r dist/* ../../cdk/visit/console/Prod',
                
                'cd ../..',

                # synth the app
                "cd cdk",
                "npm install -g aws-cdk && pip install -r requirements.txt",
                "cdk synth"
            ],
            primary_output_directory="cdk/cdk.out",
        )
        
        pipeline = CodePipeline(self, "Pipeline",
            synth=deploy_cdk_shell_step,
            cross_account_keys=True  # necessary to allow the prod account to access our artifact bucket
        )
     
        # create the stack for dev
        deploy = MakerspaceStage(self, 'Dev', env=accounts['Dev-dranwal'])
        deploy_stage = pipeline.add_stage(deploy)

        deploy_stage.add_post(
            ShellStep(
                "TestCloudfrontEndpoint",
                commands=[
                    "curl https://d1byeqit66b8mv.cloudfront.net/",

                ],
            )
        )

        lambda_action = LambdaInvokeAction(
            action_name="Test_API_Lambda",
            lambda_= aws_lambda.Function(self,
            'TestAPILambda',
            function_name=core.PhysicalName.GENERATE_IF_NEEDED,
            code=aws_lambda.Code.from_asset('visit/lambda_code/test_api'),
            environment={},
            handler='test_api.handler',
            runtime=aws_lambda.Runtime.PYTHON_3_9)
        )

        test_stage = pipeline.add_stage(
            stage_name='RunTestStage',
            placement=StagePlacement(
                just_after=pipeline.pipeline.stage(
                    'Dev'
                )
            ),
            actions=[
                lambda_action
            ]
        )
        #testing = TestStage(self, 'Test', env=accounts['Dev-dranwal'])
        #testing_stage = pipeline.add_stage(testing, actions=[lambda_action])
        
        # ShellStep(
        #         "TestAPIGatewayEndpoint",
        #         env_from_cfn_outputs={
        #             "ENDPOINT_URL": deploy.service.api_gateway.api.url
        #         },
        #         commands=[
        #             "curl -Ssf $ENDPOINT_URL/visit",
        #             "curl -Ssf $ENDPOINT_URL/register",
        #         ],
        #     )
        # )

      
        
        # # create the stack for beta
        # self.beta_stage = MakerspaceStage(self, 'Beta', env=accounts['Beta'])
        # pipeline.add_stage(self.beta_stage)

        # # create the stack for prod
        # self.prod_stage = MakerspaceStage(self, 'Prod', env=accounts['Prod'])
        # pipeline.add_stage(self.prod_stage, 
        #     pre=[ManualApprovalStep("PromoteBetaToProd")]
        # )

