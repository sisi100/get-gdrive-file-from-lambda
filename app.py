import pathlib

import aws_cdk as cdk
from aws_cdk import BundlingOptions, aws_iam, aws_lambda, aws_s3

GOOGLE_DRIVE_FOLDER_ID = "xxxxxxxxxxxxx_xxxxxxxxxxxxxxxxxxx"


app = cdk.App()
stack = cdk.Stack(app, "get-gdrive-file-from-lambda-stack")


bucket = aws_s3.Bucket(
    stack,
    "bucket",
    block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
    removal_policy=cdk.RemovalPolicy.DESTROY,
    auto_delete_objects=True,
)

layer = aws_lambda.LayerVersion(
    stack,
    "layer",
    code=aws_lambda.Code.from_asset(
        str(pathlib.Path(__file__).resolve().parent.joinpath("runtime/layer")),
        bundling=BundlingOptions(
            image=aws_lambda.Runtime.PYTHON_3_12.bundling_image,
            user="root",
            command=[
                "bash",
                "-c",
                "&&".join(
                    [
                        "cp -aur . /asset-output",
                        "cd /asset-output/python",
                        "pip install -r requirements.txt -t .",
                    ]
                ),
            ],
        ),
    ),
    compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_12],
)

# IAM role for Lambda
role = aws_iam.Role(
    stack,
    "role",
    role_name="hoge",  # CDKデフォルトのロール名だとGoogle側のAPIの文字数制限に引っかかるので物理名を強制。
    assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
    managed_policies=[aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")],
)
bucket.grant_write(role)

aws_lambda.Function(
    stack,
    "function",
    code=aws_lambda.Code.from_asset(
        str(pathlib.Path(__file__).resolve().parent.joinpath("runtime/app")),
    ),
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    handler="index.handler",
    role=role,
    layers=[layer],
    timeout=cdk.Duration.seconds(30),
    environment={
        "BUCKET_NAME": bucket.bucket_name,
        "FOLDER_ID": GOOGLE_DRIVE_FOLDER_ID,
    },
)


app.synth()
