import pymongo
import config
import datetime
import logging
from pymongo import MongoClient

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class User:

    client = MongoClient(config.MONGO_DB_TOKEN)
    db = client.big_team


    def __init__(self, message):
        print("INIT: ", message.from_user.first_name)
        self.group_id = message.chat.id
        self.user_id = message.from_user.id
        self.group_name = message.chat.title
        self.user_name = message.from_user.first_name + " " + message.from_user.last_name
        self.user_content = message.text
        self.message_object = message # passes the full message object itself for greater flexibility 

        self.insert_request_template = { 
            # $setOnINsert and $set need to be both in the same argument
            # $setOnInsert so ID is never changed unless its an insert operation the rest are updated
            "$setOnInsert":{"_id":self.user_id}, 
            "$set":{
                    "group_id":self.group_id,
                    "group_name":self.group_name,
                    "user_name":self.user_name,
                    "user_content":self.user_content,
                    "last_modified":datetime.datetime.utcnow()
            }
        }

    # To add blank enteries to DB for users who just entered the group
    def new_member(self):
        # Full name of new user and his ID extracted from message object. Set as vairables for readability 
        full_name = self.message_object.new_chat_members[0]["first_name"] + ' ' + self.message_object.new_chat_members[0]["last_name"]
        new_user_id = self.message_object.new_chat_members[0]["id"]

        new_member_template = {    
                    "_id":new_user_id, # _id of new member      
                    "group_id":self.group_id,
                    "group_name":self.group_name,
                    "user_name":full_name,
                    "user_content": "0",
                    "last_modified":datetime.datetime.utcnow()
        }
        self.db["icase_bot"].update({"_id":new_user_id}, new_member_template, upsert=True)
        self.db["nba_bot"].update({"_id":new_user_id}, new_member_template, upsert=True)

    # To remove data from DB of group members who just left
    def remove_member(self):
        self.db["icase_bot"].delete_one({"_id":self.message_object.left_chat_member["id"]})
        self.db["nba_bot"].delete_one({"_id":self.message_object.left_chat_member["id"]})
        pass

    # Function to check if the input is iCase or NBA. Inserts / updates entry to the correct collection on MongoDB
    def submit(self, type): # Note to self, let return be 
        
        logger.info("Currently submitting a case of type: " + type)

        if(type == "icase_bot"):
            collection = self.db["icase_bot"]
            collection.update({"_id":self.user_id}, self.insert_request_template, upsert=True)
            return

        elif(type == "nba_bot"):
            collection = self.db["nba_bot"]
            collection.update({"_id":self.user_id}, self.insert_request_template, upsert=True)
            return
        else:
            print("Something went wrong with inserting your data. Please check class User.")
            return