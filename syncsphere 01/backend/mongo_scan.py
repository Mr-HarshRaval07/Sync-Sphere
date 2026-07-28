import json
from pymongo import MongoClient

def main():
    client = MongoClient('mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0')
    db = client['syncsphere']
    
    out = {}
    out['collections'] = db.list_collection_names()
    
    provider_coll = None
    model_coll = None
    for c in db.list_collection_names():
        if 'provider' in c.lower():
            provider_coll = c
        if 'model' in c.lower() and 'provider' not in c.lower():
            model_coll = c
            
    out['providers'] = []
    if provider_coll:
        for p in db[provider_coll].find():
            p['_id'] = str(p.get('_id'))
            out['providers'].append(p)
            
    out['models'] = []
    if model_coll:
        for m in db[model_coll].find():
            m['_id'] = str(m.get('_id'))
            out['models'].append(m)

    with open('mongo_scan_result.json', 'w') as f:
        json.dump(out, f, indent=2, default=str)

if __name__ == '__main__':
    main()
