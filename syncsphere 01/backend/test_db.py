import pymongo

client = pymongo.MongoClient('mongodb://127.0.0.1:27017')
db = client.syncsphere
for s in db.slack_tokens.find():
    print(f'SLACK: _id={s.get("_id")} org={s.get("organization_id")} user={s.get("user_id")}')
for g in db.google_tokens.find():
    print(f'GOOGLE: _id={g.get("_id")} org={g.get("organization_id")} user={g.get("user_id")}')
