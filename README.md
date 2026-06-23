# AWS Lambda S3 File Compression

## Using Amazon Lambda, S3, IAM, and EventBridge

---

## Project Overview

This project demonstrates how to build a **fully serverless file compression pipeline on AWS** using Lambda, S3, IAM, and EventBridge.

A Python Lambda function automatically downloads a file from S3, compresses it using ZIP DEFLATE, and uploads the compressed output back to the same S3 bucket — reducing a **50 MB file down to just 149 KB (99.7% compression)**.

The pipeline runs automatically every 15 minutes via an EventBridge scheduled rule — no servers, no manual intervention.

This project was completed as part of a **Cloud Learning Journey** to gain hands-on experience with:

- AWS Lambda serverless compute
- Amazon S3 object storage
- IAM roles and least-privilege security policies
- Amazon EventBridge scheduled rules
- Python boto3 SDK for AWS automation

---

## Technologies Used

| Technology | Purpose |
|---|---|
| AWS Lambda (Python 3.14) | Serverless compute — runs the compression logic |
| Amazon S3 | Object storage — stores source and compressed files |
| AWS IAM | Identity and access control — grants Lambda S3 permissions |
| Amazon EventBridge | Scheduler — triggers Lambda every 15 minutes |
| Python boto3 | AWS SDK used inside Lambda to interact with S3 |
| Python zipfile | Built-in library used for ZIP DEFLATE compression |

---

## Project Architecture

```
EventBridge Scheduled Rule (every 15 mins)
                ↓
        Lambda Function (FileCompressor)
          ↓               ↓
  Download from S3     Upload .zip to S3
  (sample_50MB.txt) → (sample_50MB.zip)
          ↓
    S3 Bucket (compression-file)
```

---

## Result

| File | Size | Notes |
|---|---|---|
| `sample_50MB.txt` | 50.0 MB | Original source file |
| `sample_50MB.zip` | 149.2 KB | Compressed output ✅ |

**99.7% size reduction** achieved using ZIP DEFLATE compression.

---

## Implementation Steps

---

### Step 1 — Create S3 Bucket

Navigate to **AWS Console → S3 → Create bucket**.

**Configuration used:**
- **Bucket name:** `compression-file`
- **Region:** US East (N. Virginia) `us-east-1`
- Block public access: enabled (default)

After creation, upload your source file:
- Click **Upload** inside the bucket
- Upload `sample_50MB.txt` (50 MB text file)

> Screenshot: S3 bucket `compression-file` created with `sample_50MB.txt` uploaded (50.0 MB)

![S3 Bucket](./Screenshots/s3-bucket.png)

---

### Step 2 — Create IAM Role for Lambda

Navigate to **AWS Console → IAM → Roles → Create role**.

**Step 2a — Select trusted entity:**
- Trusted entity type: **AWS Service**
- Use case: **Lambda**
- Click Next

**Step 2b — Add permissions:**
- Skip attaching managed policies for now (we'll create a custom inline policy)
- Click Next

**Step 2c — Name the role:**
- **Role name:** `LambdaS3CompressionRole`
- **Description:** `Allows Lambda functions to call AWS services on your behalf.`
- Click **Create role**

> Screenshot: IAM role `LambdaS3CompressionRole` creation — Name, review, and create screen

![IAM Role Creation](./Screenshots/iam-role-create.png)

---

### Step 3 — Attach Inline Policy to IAM Role

After creating the role, open `LambdaS3CompressionRole` → **Permissions tab** → **Add permissions → Create inline policy**.

**Use the JSON editor and paste:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:HeadObject"
      ],
      "Resource": "arn:aws:s3:::compression-file/*"
    }
  ]
}
```

- **Policy name:** `Compression`
- Click **Create policy**

> Why these 3 actions?
> - `s3:GetObject` — download the source file
> - `s3:PutObject` — upload the compressed zip
> - `s3:HeadObject` — boto3 checks file metadata before downloading (without this, you get a 403 error)

> Screenshot: IAM policy `Compression` attached to `LambdaS3CompressionRole`

![IAM Policy](./Screenshots/iam-policy.png)

---

### Step 4 — Create Lambda Function

Navigate to **AWS Console → Lambda → Functions → Create function**.

**Configuration used:**
- **Option:** Author from scratch
- **Function name:** `FileCompressor`
- **Runtime:** Python 3.x (latest)
- **Execution role:** Use an existing role → select `LambdaS3CompressionRole`
- Click **Create function**

> Screenshot: Create function screen with `FileCompressor` name entered

![Lambda Create](./Screenshots/lambda-create.png)

---

### Step 5 — Write and Deploy Lambda Code

In the Lambda function editor, replace the default code with:

```python
import boto3
import zipfile
import os
import tempfile

SOURCE_BUCKET = 'compression-file'
DEST_BUCKET = 'compression-file'
SOURCE_KEY = 'sample_50MB.txt'
DEST_KEY = 'sample_50MB.zip'

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    with tempfile.TemporaryDirectory() as tmp:
        download_path = os.path.join(tmp, 'input_file')
        zip_path = os.path.join(tmp, 'output_file.zip')
        
        # Download source file from S3
        s3.download_file(SOURCE_BUCKET, SOURCE_KEY, download_path)
        
        # Compress using ZIP DEFLATE
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(download_path, SOURCE_KEY)
        
        # Upload compressed file back to S3
        s3.upload_file(zip_path, DEST_BUCKET, DEST_KEY)
    
    return {
        'statusCode': 200,
        'body': 'File compressed and uploaded successfully!'
    }
```

Click **Deploy** (or Ctrl+Shift+U).

**Important:** Also increase the Lambda timeout:
- Go to **Configuration → General configuration → Edit**
- Set **Timeout** to `5 min 0 sec` (default 3s is too short for large files)
- Set **Memory** to `1024 MB` for faster processing

> Screenshot: Lambda code deployed successfully

![Lambda Code](./Screenshots/lambda-code.png)

---

### Step 6 — Test the Lambda Function

Create a test event:
- Click **Test** → **Create new test event**
- **Event name:** `lamdaS3functions`
- **Payload:**

```json
{
  "key": "sample_50MB.txt"
}
```

Click **Test** and check the output panel at the bottom.

**Expected successful response:**
```json
{
  "statusCode": 200,
  "body": "File compressed and uploaded successfully!"
}
```

> Screenshot: Lambda test showing `Status: Succeeded`

![Lambda Test Success](./Screenshots/lambda-test-success.png)

---

### Step 7 — Verify Output in S3

Navigate back to **S3 → compression-file bucket**.

You should now see two files:

| Name | Type | Size |
|---|---|---|
| `sample_50MB.txt` | txt | 50.0 MB |
| `sample_50MB.zip` | zip | 149.2 KB ✅ |

> Screenshot: S3 bucket showing both source and compressed files

![S3 Output](./Screenshots/s3-output.png)

---

### Step 8 — Create EventBridge Scheduled Rule

Navigate to **AWS Console → Amazon EventBridge → Rules → Create rule**.

**Configuration used:**
- **Rule name:** `S3UploadTriggerRule`
- **Event bus:** default
- **Rule type:** Schedule
- **Schedule pattern:** Fixed rate — `15 minutes`

**Target:**
- Target type: **AWS service**
- Select target: **Lambda function**
- Function: `FileCompressor`

Click **Create rule**.

> Screenshot: EventBridge rule `S3UploadTriggerRule` enabled with 15-minute fixed rate

![EventBridge Rule](./Screenshots/eventbridge-rule.png)

---

## ✅ Project Output

- ✅ S3 bucket `compression-file` created in `us-east-1`
- ✅ IAM role `LambdaS3CompressionRole` created with least-privilege inline policy
- ✅ Lambda function `FileCompressor` deployed with Python 3.x runtime
- ✅ 50 MB `.txt` file compressed to 149.2 KB `.zip` (99.7% reduction)
- ✅ EventBridge rule triggering Lambda automatically every 15 minutes
- ✅ Entire pipeline is serverless — no EC2, no servers to manage

---

## Common Error & Fix

### 403 Forbidden — HeadObject

```
ClientError: An error occurred (403) when calling the HeadObject operation: Forbidden
```

**Cause:** Lambda's execution role is missing S3 permissions.

**Fix:** Ensure the IAM role attached to the Lambda function has the `Compression` inline policy with `s3:GetObject`, `s3:PutObject`, and `s3:HeadObject` actions on `arn:aws:s3:::compression-file/*`. Also verify the correct role is selected under **Lambda → Configuration → Permissions**.

---

## 🎯 Learning Outcomes

Through this project I learned:

- How to build a serverless automation pipeline on AWS
- How IAM least-privilege policies work and why `s3:HeadObject` matters
- How Python's `zipfile` module achieves compression inside Lambda
- How `tempfile.TemporaryDirectory()` safely manages ephemeral Lambda storage
- How EventBridge scheduled rules trigger Lambda functions automatically
- The difference between hardcoded keys vs dynamic event-driven file keys
- How to debug Lambda 403 errors by tracing IAM permission gaps

---

## Screenshots

| Screenshot | Description |
|---|---|
| `s3-bucket.png` | S3 bucket created with source file uploaded |
| `iam-role-create.png` | IAM role `LambdaS3CompressionRole` creation screen |
| `iam-policy.png` | `Compression` inline policy attached to role |
| `lambda-create.png` | Lambda function creation screen |
| `lambda-code.png` | Lambda code deployed in editor |
| `lambda-test-success.png` | Test execution showing Status: Succeeded |
| `s3-output.png` | S3 bucket showing compressed output file |
| `eventbridge-rule.png` | EventBridge scheduled rule details |

---

## Repository Structure

```
AWS-Lambda-S3-File-Compression/
│
├── lambda/
│   └── lambda_function.py       # Lambda compression code
│
├── iam/
│   └── compression-policy.json  # IAM inline policy JSON
│
├── Screenshots/
│   ├── s3-bucket.png
│   ├── iam-role-create.png
│   ├── iam-policy.png
│   ├── lambda-create.png
│   ├── lambda-code.png
│   ├── lambda-test-success.png
│   ├── s3-output.png
│   └── eventbridge-rule.png
│
└── README.md
```

---

## Author

**Aryanraje Dhokale**

Cloud and DevOps Learner | AWS | Lambda | Serverless | Python