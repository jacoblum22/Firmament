# AWS Setup Guide for StudyMate-v2

This guide will help you set up an AWS account and configure S3 storage for StudyMate-v2.

## Prerequisites
- You'll need an email address and credit/debit card for AWS account creation
- AWS Free Tier provides 5GB of S3 storage for 12 months (perfect for MVP)

## Step 1: Create AWS Account

1. **Go to AWS Sign Up**: Visit [aws.amazon.com](https://aws.amazon.com)
2. **Click "Create an AWS Account"**
3. **Fill in account details**:
   - Email address
   - Account name (e.g., "StudyMate-v2")
   - Choose "Personal" account type
4. **Verify your email** and continue
5. **Add payment information** (required even for free tier)
6. **Verify your phone number**
7. **Choose Support Plan**: Select "Basic support - Free"

## Step 2: Create IAM User (Security Best Practice)

1. **Sign in to AWS Console**: [console.aws.amazon.com](https://console.aws.amazon.com)
2. **Go to IAM Service**: Search for "IAM" in the services search
3. **Create a new user**:
   - Click "Users" → "Create user"
   - Username: `studymate-s3-user`
   - Select "Programmatic access"
4. **Set permissions**:
   - Choose "Attach policies directly"  
   - Click **"Create policy"** instead of using the overly broad AmazonS3FullAccess
   - Switch to **JSON** tab and paste this least-privilege policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject", 
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::studymate-prod-storage",
                "arn:aws:s3:::studymate-prod-storage/*"
            ]
        }
    ]
}
```

   - **Important**: Replace `studymate-prod-storage` with your actual bucket name
   - Click **"Review policy"** → Name it `StudyMate-S3-Policy` → **"Create policy"**
   - Go back to user creation and attach your new `StudyMate-S3-Policy`
5. **Create user** and **SAVE the credentials**:
   - Access Key ID
   - Secret Access Key
   - ⚠️ **Important**: Save these securely - you won't see the secret again!

## Step 3: Create S3 Bucket

1. **Go to S3 Service**: Search for "S3" in the AWS Console
2. **Create bucket**:
   - Bucket name: `studymate-prod-storage` (must be globally unique)
   - If name is taken, try: `studymate-[your-initials]-storage`
   - Region: `us-east-1` (same as configured in the app)
3. **Configure settings**:
   - **Block Public Access**: Keep all checkboxes CHECKED (security)
   - **Bucket Versioning**: Disable (saves money)
   - **Default encryption**: Enable with SSE-S3
4. **Create bucket**

## Step 4: Configure CORS (for web uploads)

1. **Select your bucket** in S3 console
2. **Go to "Permissions" tab**
3. **Scroll to "Cross-origin resource sharing (CORS)"**
4. **Click "Edit"** and paste this configuration:

```json
[
    {
        "AllowedHeaders": [
            "Content-Type",
            "Authorization"
        ],
        "AllowedMethods": [
            "GET",
            "POST",
            "PUT"
        ],
        "AllowedOrigins": [
            "https://your-production-domain.com",
            "http://localhost:5173",
            "http://localhost:3000"
        ],
        "ExposeHeaders": [],
        "MaxAgeSeconds": 3000
    }
]
```

5. **Replace** `https://your-production-domain.com` with your actual domain
6. **Save changes**

## Step 5: Update Environment Variables

Update your `.env.production` file with the AWS credentials:

```bash
# AWS S3 Configuration
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name-here
```

## Step 6: Test the Configuration

Run the test script to verify everything is working:

```bash
cd backend
python test_s3_connection.py
```

## Security Best Practices

1. **Use least-privilege IAM policies**: The custom policy above only grants access to your specific bucket, not all S3 buckets in your account
2. **Never commit AWS credentials** to version control
3. **Use IAM users** instead of root account for applications
4. **Rotate credentials** regularly (at least every 90 days)
5. **Monitor usage** in AWS Console to avoid unexpected charges
6. **Restrict CORS** to only the headers and methods your application needs

## Free Tier Limits

- **5GB of S3 storage** for 12 months
- **20,000 GET requests** per month
- **2,000 PUT requests** per month

For a typical MVP, this should be sufficient for several months.

## Troubleshooting

### Common Issues:
1. **Bucket name already exists**: Choose a different name
2. **Access denied**: Check IAM permissions
3. **CORS errors**: Verify CORS configuration includes your domain

### Getting Help:
- AWS Documentation: [docs.aws.amazon.com](https://docs.aws.amazon.com)
- AWS Support (free tier): Available through AWS Console

## Cost Monitoring

1. **Set up billing alerts**:
   - Go to AWS Console → Billing & Cost Management
   - Create a budget alert for $5-10 to monitor usage

2. **Monitor S3 usage**:
   - Go to S3 Console → Metrics & Analytics
   - Check storage usage and request counts

Remember: With proper cleanup policies (which StudyMate includes), your costs should remain minimal!
