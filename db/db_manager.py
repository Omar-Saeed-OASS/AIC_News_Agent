import os
import uuid
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore
from dotenv import load_dotenv
from firebase_admin.firestore import client

load_dotenv()

class DatabaseManager:

    def __init__(self, raw_json_cert=None):
        try:
            # Fetch raw_json_cert
            if raw_json_cert is None:
                raw_json_cert = os.environ.get("FIREBASE_CREDENTIALS_JSON")

            # Prevent double initialization crashes
            if not firebase_admin._apps:
                if raw_json_cert:
                    # Cloud Run / Secret Manager path (or local .env JSON string)
                    cert_dict = json.loads(raw_json_cert)
                    self.cred = credentials.Certificate(cert_dict)
                    self.app = firebase_admin.initialize_app(self.cred)
                else:
                    # Fallback to Application Default Credentials if env var isn't set
                    self.app = firebase_admin.initialize_app()

            self.db = firestore.client()
        except Exception as e:
            print(f"Error: {e}")

    def get_db(self):
        """return the firestore client"""
        return self.db

    def set_document(self, collection, data, doc_id=None):
        """Creates or overwrites a document inside a collection"""

        if doc_id:
            self.db.collection(collection).document(doc_id).set(data)
        else:
            auto_id = uuid.uuid4().hex[:5]
            self.db.collection(collection).document(auto_id).set(data)


    def get_document(self, collection, doc_id):
        """Retrieves a specific document from a collection"""

        doc = self.db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None
