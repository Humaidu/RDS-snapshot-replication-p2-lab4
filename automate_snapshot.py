import boto3
from datetime import datetime

timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H-%M')
snapshot_name = f'rds-auto-snapshot-{timestamp}'
copy_name = f'rds-auto-copy-{timestamp}'

source_region = 'eu-central-1'
destination_region = 'eu-west-1'

# Creating RDS client for both regions
rds_source = boto3.client('rds', region_name=source_region)
rds_dest = boto3.client('rds', region_name=destination_region)

def lambda_handler(event, context):
    # Step 1: Create the snapshot
    create_response = rds_source.create_db_snapshot(
        DBInstanceIdentifier='hash-rds-db',
        DBSnapshotIdentifier=snapshot_name
    )
    print("Snapshot creation started:", create_response)

    # Step 2: Wait for snapshot to be available
    print("Waiting for snapshot to become available...")
    waiter = rds_source.get_waiter('db_snapshot_available')
    waiter.wait(
        DBSnapshotIdentifier=snapshot_name,
        WaiterConfig={
            'Delay': 30,     # seconds between checks
            'MaxAttempts': 20  # total ~10 minutes
        }
    )
    print("Snapshot is now available.")

    # Step 3: Copy snapshot to destination region
    copy_response = rds_dest.copy_db_snapshot(
        SourceDBSnapshotIdentifier=f'arn:aws:rds:{source_region}:149536482038:snapshot:{snapshot_name}',
        TargetDBSnapshotIdentifier=copy_name,
        SourceRegion=source_region,
        KmsKeyId='alias/aws/rds'  # Default KMS key in destination
    )
    print("Snapshot copied:", copy_response)
