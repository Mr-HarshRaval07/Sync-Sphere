import asyncio
from pymongo import MongoClient

def main():
    client = MongoClient('mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0')
    db = client['syncsphere']
    
    print("Migrating / Cleaning up old OAuth tokens without organization_id...")
    google_res = db['google_tokens'].delete_many({"organization_id": None})
    slack_res = db['slack_tokens'].delete_many({"organization_id": None})
    github_res = db['github_tokens'].delete_many({"organization_id": None})
    
    print(f"Deleted {google_res.deleted_count} orphaned Google tokens.")
    print(f"Deleted {slack_res.deleted_count} orphaned Slack tokens.")
    print(f"Deleted {github_res.deleted_count} orphaned GitHub tokens.")
    print("Done. Users will be correctly prompted to reconnect and save with organization_id.")
    
if __name__ == '__main__':
    main()
