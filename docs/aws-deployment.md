# AWS deployment

The production system uses one EC2 server with a fixed Elastic IP, Amazon RDS for PostgreSQL in a private database network path, and AWS Systems Manager Parameter Store for encrypted server settings.

## What is automatic

After the initial setup, the EC2 server securely checks the public GitHub repository for updates to `main` every two minutes. It builds and restarts the service only when a new Git revision is available. This avoids storing AWS keys in GitHub while the project's Free plan restricts the AWS-managed CI/CD role path.

## One-time domain steps

1. Create an `A` record at Hostinger for the chosen subdomain, pointing to the Elastic IP supplied after the server is created.
2. Tell the deployment operator the exact hostname after the record is saved.
3. Add that hostname to Firebase Authentication's Authorized domains list.
4. Issue the HTTPS certificate on the EC2 server after DNS propagation.

## Production parameter fields

The encrypted Systems Manager parameter contains these fields only: `DATABASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_FALLBACK_MODELS`, `OPENROUTER_BASE_URL`, `FIREBASE_CREDENTIALS_JSON`, `APP_SITE_URL`, `CHATBOT_TIMEOUT_SECONDS`, and `CHATBOT_MAX_TOKENS`.

Do not place these values in GitHub, source files, the release archive, or EC2 user data.
