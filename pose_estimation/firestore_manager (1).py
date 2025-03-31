import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import cv2
import base64
import datetime
import os  # Added for file path operations

class FirestoreManager:
    def __init__(self, credential_path="firebase-credentials.json"):
        """Initialize Firebase with the specified credentials.
        
        Args:
            credential_path: Path to the Firebase credentials JSON file
        """
        self.initialized = False
        try:
            cred = credentials.Certificate(credential_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.initialized = True
            print("Firestore initialized successfully")
        except Exception as e:
            print(f"Firestore initialization error: {e}")
            
            
            
    def send_to_firebase(self, bad_form_images, session_stats=None, user_id="testing"):
        if not self.initialized:
            print("Firestore not initialized")
            return {"success": False, "error": "Firestore not initialized"}
    
        results = {
            "success": True,
            "images_uploaded": 0,
            "failed_uploads": 0,
            "image_doc_ids": [],
            "session_id": None
        }
    
        # Create a session ID
        session_id = str(uuid.uuid4())
        
        # Upload session stats first
        if session_stats:
            try:
                # Create session document
                session_data = {
                    'username': user_id,
                    'session_id': session_id,
                    'timestamp': datetime.datetime.now(),
                    'stats': session_stats,
                    'bad_form_count': len(bad_form_images),
                    'completed': True
                }
                
                # Add to sessions collection
                session_ref = self.db.collection('sessions').document(session_id)
                session_ref.set(session_data)
                
                results["session_id"] = session_id
                print(f"Uploaded session with ID: {session_id}")
            
            except Exception as e:
                print(f"Error uploading session: {e}")
                results["session_error"] = str(e)
                results["success"] = False
                return results  # If we can't create the session, no point continuing
        
        # Process and upload each image
        for image_path in bad_form_images:
            try:
                # Extract information from filename
                filename = os.path.basename(image_path)
                parts = filename.split('_')
                
                # Parse information from filename (attempt_NUM_ISSUE_TYPE_TIMESTAMP.jpg)
                attempt_num = parts[1] if len(parts) > 1 else "unknown"
                issue_type = parts[2] if len(parts) > 2 else "unknown"
                
                # Read the image
                img = cv2.imread(image_path)
                if img is None:
                    print(f"Failed to read image: {image_path}")
                    results["failed_uploads"] += 1
                    continue
                
                # Resize image to reduce size before encoding
                max_width = 320  # Limit width to control file size
                height, width = img.shape[:2]
                if width > max_width:
                    scale = max_width / width
                    img = cv2.resize(img, None, fx=scale, fy=scale)
                
                # Convert image to jpg buffer
                _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
                
                # Convert to base64 string
                img_str = base64.b64encode(buffer).decode('utf-8')
                
                # Create document data for wrong form image
                wrong_form_data = {
                    'username': user_id,
                    'session_id': session_id,
                    'timestamp': datetime.datetime.now(),
                    'form_issue': issue_type,
                    'attempt_number': attempt_num,
                    'image_path': image_path,
                    'image': img_str
                }
                
                # Add to wrong_forms collection
                doc_ref = self.db.collection('wrong_forms').document()
                doc_ref.set(wrong_form_data)
                
                results["images_uploaded"] += 1
                results["image_doc_ids"].append(doc_ref.id)
                print(f"Uploaded bad form image: {image_path}")
                
            except Exception as e:
                print(f"Error uploading image {image_path}: {e}")
                results["failed_uploads"] += 1
        
        print(f"Firebase upload complete: {results['images_uploaded']} images uploaded, {results['failed_uploads']} failed")
        return results

