import boto3
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from main_app.models.models import Event, EventImage
from main_app.extensions import db



class EventService:
    def __init__(self, s3_bucket_name):
        self.s3_client = boto3.client('s3')
        self.s3_bucket_name = s3_bucket_name

    def create_event(self, title, description=None):
        try:
            new_event = Event(title=title, description=description)
            db.session.add(new_event)
            db.session.commit()
            return new_event
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating event: {str(e)}")

    def get_event(self, event_id):
        try:
            return Event.query.get(event_id)
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching event: {str(e)}")

    def update_event(self, event_id, title=None, description=None):
        try:
            event = Event.query.get(event_id)
            if not event:
                raise Exception("Event not found")
            
            if title:
                event.title = title
            if description is not None:
                event.description = description
            
            db.session.commit()
            return event
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error updating event: {str(e)}")

    def delete_event(self, event_id):
        try:
            event = Event.query.get(event_id)
            if not event:
                raise Exception("Event not found")
            
            # מחיקת כל התמונות הקשורות לאירוע מ-S3
            for image in event.images:
                self.delete_image_from_s3(image.s3_key)
            
            db.session.delete(event)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting event: {str(e)}")

    def add_image_to_event(self, event_id, file_content, file_name):
        try:
            event = Event.query.get(event_id)
            if not event:
                raise Exception("Event not found")
            
            # יצירת מפתח ייחודי עבור S3
            s3_key = f"events/{event_id}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"

            # העלאת הקובץ ל-S3
            try:
                self.s3_client.put_object(Bucket=self.s3_bucket_name, Key=s3_key, Body=file_content)
            except ClientError as e:
                raise Exception(f"Error uploading file to S3: {str(e)}")

            # יצירת רשומת EventImage בבסיס הנתונים
            file_size = len(file_content)
            new_image = EventImage(s3_key=s3_key, file_name=file_name, file_size=file_size, event_id=event_id)
            db.session.add(new_image)
            db.session.commit()
            return new_image
        except Exception as e:
            db.session.rollback()
            # אם הייתה שגיאה, ננסה למחוק את הקובץ מ-S3 אם הוא הועלה
            self.delete_image_from_s3(s3_key)
            raise Exception(f"Error adding image to event: {str(e)}")

    def delete_image(self, image_id):
        try:
            image = EventImage.query.get(image_id)
            if not image:
                raise Exception("Image not found")
            
            # מחיקת הקובץ מ-S3
            self.delete_image_from_s3(image.s3_key)

            # מחיקת הרשומה מבסיס הנתונים
            db.session.delete(image)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting image: {str(e)}")

    def delete_image_from_s3(self, s3_key):
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=s3_key)
        except ClientError as e:
            raise Exception(f"Error deleting file from S3: {str(e)}")

    def get_event_images(self, event_id):
        try:
            event = Event.query.get(event_id)
            if not event:
                raise Exception("Event not found")
            return event.images
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching event images: {str(e)}")

    def get_all_events(self):
        try:
            return Event.query.all()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching all events: {str(e)}")
        