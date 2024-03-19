#!/bin/sh

SUFFIX=20240320
PROJECT_ID=pj-test-$SUFFIX
ACCOUNT_ID=test-account-$SUFFIX
POOL_ID=test-pool-$SUFFIX
PROVIDER_ID=test-provider-$SUFFIX
AWS_ACCOUNT_ID=123456789000 # 任意のAWSアカウントID
AWS_ROLE=arn:aws:sts::$AWS_ACCOUNT_ID:assumed-role/hoge

# Projectを新規で作成する
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# サービスアカウントを追加
gcloud iam service-accounts create $ACCOUNT_ID --display-name=test_account

# Workload Identity APIを有効化する
gcloud services enable iamcredentials.googleapis.com

# Workload Identity Poolを作成
gcloud iam workload-identity-pools create $POOL_ID \
    --location="global" \
    --display-name=test_pool

# Workload Identity poolにプロバイダを作成
gcloud iam workload-identity-pools providers create-aws $PROVIDER_ID \
    --location="global" \
    --workload-identity-pool=$POOL_ID \
    --account-id=$AWS_ACCOUNT_ID \
    --attribute-mapping="google.subject=assertion.arn,attribute.aws_role=assertion.arn.contains('assumed-role') ? assertion.arn.extract('{account_arn}assumed-role/') + 'assumed-role/' + assertion.arn.extract('assumed-role/{role_name}/') : assertion.arn"

# サービス アカウントにアクセス権追加
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value core/project) --format=value\(projectNumber\))
SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts list --filter='display_name=test_account' --format='value(email)')
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
    --role=roles/iam.workloadIdentityUser \
    --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_ID/attribute.aws_role/$AWS_ROLE"

# 構成情報の取得
gcloud iam workload-identity-pools create-cred-config \
    projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_ID/providers/$PROVIDER_ID \
    --service-account=$SERVICE_ACCOUNT_EMAIL \
    --aws \
    --output-file=google_config.json

echo email:$SERVICE_ACCOUNT_EMAIL
echo project_number:$PROJECT_NUMBER

mv google_config.json ./runtime/app/google_config.json
