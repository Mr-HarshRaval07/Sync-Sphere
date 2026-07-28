import json
from pymongo import MongoClient

def main():
    client = MongoClient('mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0')
    db = client['syncsphere']
    
    out = {}
    
    # Check google_tokens
    out['google_tokens'] = []
    for t in db['google_tokens'].find():
        out['google_tokens'].append({
            '_id': str(t.get('_id')),
            'user_id': t.get('user_id'),
            'organization_id': t.get('organization_id'),
            'google_email': t.get('google_email'),
            'created_at': t.get('created_at'),
        })

    # Check slack_tokens
    out['slack_tokens'] = []
    for t in db['slack_tokens'].find():
        out['slack_tokens'].append({
            '_id': str(t.get('_id')),
            'team_name': t.get('team_name'),
            'organization_id': t.get('organization_id'),
            'created_at': t.get('created_at'),
        })

    # Check github_tokens
    out['github_tokens'] = []
    for t in db['github_tokens'].find():
        out['github_tokens'].append({
            '_id': str(t.get('_id')),
            'github_username': t.get('github_username'),
            'organization_id': t.get('organization_id'),
            'created_at': t.get('created_at'),
        })
        
    print(json.dumps(out, indent=2, default=str))

if __name__ == '__main__':
    main()
