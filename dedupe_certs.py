"""Run ONCE before the new fetching_10000_main.py: lowercases domains, removes duplicates
(keeps the newest record per domain) and creates the unique index."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
col = MongoClient(os.getenv("MONGOURL"))["certdb"]["certificates"]

print("Before:", col.count_documents({}))
col.update_many({}, [{"$set": {"domain": {"$toLower": {"$trim": {"input": "$domain"}}}}}])

removed = 0
for g in col.aggregate([{"$group": {"_id": "$domain", "ids": {"$push": "$_id"}, "n": {"$sum": 1}}},
                        {"$match": {"n": {"$gt": 1}}}], allowDiskUse=True):
    ids = sorted(g["ids"])                      # ObjectIds grow with time -> last = newest
    removed += col.delete_many({"_id": {"$in": ids[:-1]}}).deleted_count

col.create_index("domain", unique=True)
print("Duplicates removed:", removed, "| After:", col.count_documents({}))
