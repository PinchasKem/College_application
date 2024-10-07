from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
from main_app.models.models import Lesson, CategoryLessons
from main_app.extensions import db


class LessonService:
    def __init__(self, s3_bucket_name):
        self.s3_client = boto3.client('s3')
        self.s3_bucket_name = s3_bucket_name

    def create_lesson(self, title, description, is_audio, file_content, file_name, category_id):
        try:
            # יצירת מפתח ייחודי עבור S3
            s3_key = f"lessons/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"

            # העלאת הקובץ ל-S3
            try:
                self.s3_client.put_object(Bucket=self.s3_bucket_name, Key=s3_key, Body=file_content)
            except ClientError as e:
                raise Exception(f"Error uploading file to S3: {str(e)}")

            # יצירת רשומת Lesson בבסיס הנתונים
            file_size = len(file_content)
            new_lesson = Lesson(title=title, description=description, is_audio=is_audio,
                                s3_key=s3_key, file_size=file_size, category_id=category_id)
            db.session.add(new_lesson)
            db.session.commit()
            return new_lesson
        except Exception as e:
            db.session.rollback()
            # אם הייתה שגיאה, ננסה למחוק את הקובץ מ-S3 אם הוא הועלה
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=s3_key)
            except:
                pass  # התעלם משגיאות בניקוי
            raise Exception(f"Error creating lesson: {str(e)}")

    def update_lesson(self, lesson_id, title=None, description=None, is_audio=None, file_content=None, file_name=None, category_id=None):
        try:
            lesson = Lesson.query.get(lesson_id)
            if not lesson:
                raise Exception("Lesson not found")

            if title:
                lesson.title = title
            if description:
                lesson.description = description
            if is_audio is not None:
                lesson.is_audio = is_audio
            if category_id:
                lesson.category_id = category_id

            if file_content and file_name:
                # מחיקת הקובץ הישן מ-S3
                try:
                    self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=lesson.s3_key)
                except ClientError as e:
                    raise Exception(f"Error deleting old file from S3: {str(e)}")

                # העלאת הקובץ החדש ל-S3
                new_s3_key = f"lessons/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
                try:
                    self.s3_client.put_object(Bucket=self.s3_bucket_name, Key=new_s3_key, Body=file_content)
                except ClientError as e:
                    raise Exception(f"Error uploading new file to S3: {str(e)}")

                lesson.s3_key = new_s3_key
                lesson.file_size = len(file_content)

            db.session.commit()
            return lesson
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error updating lesson: {str(e)}")

    def delete_lesson(self, lesson_id):
        try:
            lesson = Lesson.query.get(lesson_id)
            if not lesson:
                raise Exception("Lesson not found")

            # מחיקת הקובץ מ-S3
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=lesson.s3_key)
            except ClientError as e:
                raise Exception(f"Error deleting file from S3: {str(e)}")

            # מחיקת הרשומה מבסיס הנתונים
            db.session.delete(lesson)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error deleting lesson: {str(e)}")

    @staticmethod
    def create_category(name):
        try:
            new_category = CategoryLessons(name=name)
            db.session.add(new_category)
            db.session.commit()
            return new_category
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating category: {str(e)}")
    
    @staticmethod
    def delete_category(category_id):
        try:
            category = CategoryLessons.query.filter_by(category_id=category_id).first()
            db.session.delete(category)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting category: {str(e)}")
        
    @staticmethod
    def get_all_categories():
        try:
            categories = CategoryLessons.query.all()
            return categories
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error geting categories: {str(e)}")

    @staticmethod
    def get_lessons_by_category(category_id):
        try:
            return Lesson.query.filter_by(category_id=category_id).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching lessons by category: {str(e)}")
        