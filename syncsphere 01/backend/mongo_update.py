from pymongo import MongoClient

def main():
    client = MongoClient('mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0')
    db = client['syncsphere']
    
    user = db['users'].find_one()
    org_id = user['org_id']
    user_id = str(user['_id'])
    
    print(f"Migrating with org_id: {org_id} and user_id: {user_id}")
    
    db['google_tokens'].update_many({"organization_id": None}, {"$set": {"organization_id": org_id, "user_id": user_id}})
    db['slack_tokens'].update_many({"organization_id": None}, {"$set": {"organization_id": org_id, "user_id": user_id}})
    db['github_tokens'].update_many({"organization_id": None}, {"$set": {"organization_id": org_id, "user_id": user_id}})
    
    print("Migration complete!")

if __name__ == '__main__':
    main()
