# RDS Snapshot Replication Across AWS Regions

## Objective

This lab demonstrates how to:
- Create an Amazon RDS Snapshot
- Copy the snapshot to another AWS region
- Restore the snapshot to create a replica database

---

## Prerequisites

Before starting, ensure you have:
- An **AWS Account** with permissions for RDS, IAM, and S3
- An **existing RDS instance** (MySQL, PostgreSQL, or MariaDB)
- **AWS CLI** installed and configured (optional but recommended)

---

## Step-by-Step Guide

### Step 1: Create a Manual Snapshot

1. Log in to the **AWS Management Console**
2. Navigate to **Amazon RDS**
3. Select your **RDS instance**
4. Go to **Actions → Take Snapshot**
5. Enter a snapshot name, e.g., `rds-prod-snapshot`
6. Click **Create Snapshot**
7. Wait until the snapshot status is **"Available"**

---

### Step 2: Copy the Snapshot to Another AWS Region

#### Using AWS Console

1. Go to **RDS → Snapshots**
2. Select the snapshot you created
3. Click **Actions → Copy Snapshot**
4. Configure the copy:
   - **Destination Region**: Choose target region (e.g., `eu-west-1`)
   - **Snapshot Name**: Enter a name (or keep default)
   - **Encryption**: Enable if required
5. Click **Copy Snapshot**
6. Wait until the snapshot is **"Available"** in the destination region

#### Using AWS CLI

```bash
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier arn:aws:rds:us-east-1:123456789012:snapshot:rds-prod-snapshot \
  --target-db-snapshot-identifier rds-prod-snapshot-copy \
  --source-region eu-central-1 \
  --destination-region eu-west-1

```
Replace ARN, snapshot name, and regions accordingly.

---

### Step 3: Restore Snapshot in Target Region

#### Using AWS Console

1. Switch to the target AWS region
2. Navigate to **RDS → Snapshots**
3. Select the copied snapshot
4. Click **Actions → Restore Snapshot**
5. Configure:
    - **DB Instance Identifier:** rds-replica-instance
    - **Instance Class:** Choose instance type
    - **VPC & Security Groups:** Choose appropriate network settings
6. Click **Restore DB Instance**
7. Wait until the status is `Available`

#### Using AWS CLI

```
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier rds-replica-instance \
  --db-snapshot-identifier rds-prod-snapshot-copy \
  --region us-west-1

```

---

### Step 4: Verify the Replica Database

1. In the **RDS Console**, go to Databases
2. Find `rds-replica-instance`
3. Note the **Endpoint** and **Port**
4. Connect using appropriate CLI:
    - MySQL
    ```
     mysql -h <endpoint> -u admin -p

    ```

    - PostgreSQL
    ```
    psql -h <endpoint> -U admin -d mydb

    ```

##### Using Docker with MYSQL for the Verification

```
docker run -it --rm mysql:8 mysql -h <endpoint> -u admin -p

```
If it's accessible, you'll be prompted for your password and dropped into the MySQL CLI.

**Note:**
- RDS db should be Publicly Accessible
- Allow port 3306 in rds security group

---

### Step 5 : Automate Snapshots and Replication

#### Enable Automated Snapshots

1. Go to **RDS → Databases → Select your instance**
2. Click **Modify**
3. Under the **Backup** section, configure:
   - **Backup Retention Period**: e.g., 7 days
   - **Backup Window**: e.g., choose off-peak hours
4. Click **Save Changes**

---

#### Automate Snapshot Copying with Lambda

##### Setup Instructions

1. Go to **AWS Lambda → Create Function**
2. Choose Author from scratch
3. Use Python 3.9 or latest version
4. Assign an `IAM role` with permissions to access RDS (and optionally S3)
5. Paste the code from [Automate Snapshot Script](automate_snapshot.py) into the function editor
6. Create a CloudWatch Event Rule to trigger the Lambda function daily

---

### Step 6: Automate Daily RDS Snapshot Copy with EventBridge(CloudWatch Rule)

To automate the creation and cross-region copy of your RDS snapshots, configure an Amazon EventBridge (CloudWatch Events) rule to trigger the Lambda function on a daily schedule.

#### Steps to Create the EventBridge Rule

1. Open the **AWS Management Console** and navigate to **Amazon EventBridge**.
2. Click **"Create rule"**.
3. Configure the rule settings:
   - **Name**: `DailyRDSSnapshotCopyRule`
   - **Description**: Trigger Lambda function to create and copy RDS snapshot daily.
   - **Rule type**: Schedule
   - **Schedule pattern**:  
     ```
     cron(0 11 * * ? *)
     ```
     This cron expression triggers the rule at **11:00 AM UTC every day**.

4. Under **Target**:
   - **Target type**: AWS service
   - **Service**: Lambda function
   - **Function**: Select your Lambda function (e.g., `automateRDSSnapshot`)
5. **Permissions**: Allow EventBridge to invoke your Lambda function if prompted.

6. Click **"Create"**.

#### Notes

- The cron expression `cron(0 11 * * ? *)` means:
  - Minute: `0`
  - Hour: `11` (UTC)
  - Day of month: every day
  - Month: every month
  - Day of week: any day
  - Year: any year
- You can adjust the time according to your preferred backup window or timezone.

### Result

This setup ensures your Lambda function runs daily to:
- Create an encrypted RDS snapshot
- Wait until it becomes available
- Copy it to the destination AWS region with the appropriate KMS key

---

## Cleanup

**Delete the Replica Instance**

```
aws rds delete-db-instance \
  --db-instance-identifier rds-replica-instance-name \
  --skip-final-snapshot

```

**Delete the Snapshot Copy**

```
aws rds delete-db-snapshot \
  --db-snapshot-identifier rds-snapshot-copy-name

```

