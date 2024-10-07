import boto3
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
from main_app.models.models import ForumPost, ForumReply, ForumCluster, Attachment
from main_app.extensions import db


class ForumService:
    def __init__(self, s3_bucket_name):
        self.s3_client = boto3.client('s3')
        self.s3_bucket_name = s3_bucket_name

    @staticmethod
    def create_post(title, content, author_id, cluster_id=None):
        try:
            new_post = ForumPost(title=title, content=content, author_id=author_id, cluster_id=cluster_id)
            db.session.add(new_post)
            db.session.commit()
            return new_post
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating post: {str(e)}")

    @staticmethod
    def add_attachment_to_post(post_id, filename, s3_key, file_type, file_size):
        try:
            post = ForumPost.query.get(post_id)
            if not post:
                raise Exception("Post not found")
            
            new_attachment = Attachment(filename=filename, s3_key=s3_key, 
                                        file_type=file_type, file_size=file_size, 
                                        post_id=post_id)
            db.session.add(new_attachment)
            db.session.commit()
            return new_attachment
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error adding attachment: {str(e)}")

    @staticmethod
    def delete_post(post_id):
        try:
            post = ForumPost.query.get(post_id)
            if not post:
                raise Exception("Post not found")
            
            replies = ForumReply.query.filter_by(post_id = post_id).all()

            for reply in replies:
                db.session.delete(reply)

            db.session.delete(post)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting post: {str(e)}")

    @staticmethod
    def create_reply(content, author_id, post_id):
        try:
            new_reply = ForumReply(content=content, author_id=author_id, post_id=post_id)
            db.session.add(new_reply)
            db.session.commit()
            return new_reply
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating reply: {str(e)}")

    @staticmethod
    def delete_reply(reply_id):
        try:
            reply = ForumReply.query.get(reply_id)
            if not reply:
                raise Exception("Reply not found")
            
            db.session.delete(reply)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting reply: {str(e)}")

    @staticmethod
    def create_cluster(name, user_id, description=None):
        try:
            new_cluster = ForumCluster(name=name, description=description, author_id=user_id)
            db.session.add(new_cluster)
            db.session.commit()
            return new_cluster
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating cluster: {str(e)}")

    @staticmethod
    def delete_cluster(cluster_id):
        try:
            cluster = ForumCluster.query.get(cluster_id)
            if not cluster:
                raise Exception("Cluster not found")
            
            db.session.delete(cluster)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting cluster: {str(e)}")

    @staticmethod
    def get_all_posts():
        return  ForumPost.query.all()
    
    @staticmethod
    def get_post_by_id(id):
        return  ForumPost.query.filter_by(id=id).first()

    @staticmethod
    def get_reply_by_id(id):
        return  ForumReply.query.filter_by(id=id).first()

    @staticmethod
    def get_replies_by_post(post_id):
        return ForumReply.query.filter_by(post_id=post_id).all()

    @staticmethod
    def get_cluster_by_id(id):
        return  ForumCluster.query.filter_by(id=id).first()

    @staticmethod
    def get_all_clusters():
        return ForumCluster.query.all()
    
    @staticmethod
    def update_post(post_id, title=None, content=None):
        try:
            post = ForumPost.query.get(post_id)
            if not post:
                raise Exception("Post not found")
            
            if title is not None:
                post.title = title
            if content is not None:
                post.content = content
            
            db.session.commit()
            return post
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error updating post: {str(e)}")

    @staticmethod
    def update_reply(reply_id, content):
        try:
            reply = ForumReply.query.get(reply_id)
            if not reply:
                raise Exception("Reply not found")
            
            reply.content = content
            db.session.commit()
            return reply
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error updating reply: {str(e)}")

    @staticmethod
    def update_cluster(cluster_id, name=None, description=None):
        try:
            cluster = ForumCluster.query.get(cluster_id)
            if not cluster:
                raise Exception("Cluster not found")
            
            if name is not None:
                cluster.name = name
            if description is not None:
                cluster.description = description
            
            db.session.commit()
            return cluster
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error updating cluster: {str(e)}")

    @staticmethod
    def add_attachment_to_post(post_id, filename, file_content, file_type):
        try:
            logger.info(f"Starting add_attachment_to_post for post {post_id}")
            post = ForumPost.query.get(post_id)
            if not post:
                logger.warning(f"Post {post_id} not found")
                raise NotFound("Post not found")
            
            # יצירת מפתח ייחודי עבור S3
            s3_key = f"attachments/{post_id}/{filename}"

            # העלאת הקובץ ל-S3
            try:
                logger.info(f"Uploading file to S3: {s3_key}")
                s3_client.put_object(Bucket=s3_bucket_name, Key=s3_key, Body=file_content)
            except ClientError as e:
                logger.error(f"Error uploading file to S3: {str(e)}")
                raise Exception(f"Error uploading file to S3: {str(e)}")

            # יצירת רשומת Attachment בבסיס הנתונים
            file_size = len(file_content)
            new_attachment = Attachment(filename=filename, s3_key=s3_key, 
                                        file_type=file_type, file_size=file_size, 
                                        post_id=post_id)
            db.session.add(new_attachment)
            db.session.commit()
            logger.info(f"Successfully added attachment {new_attachment.id} to post {post_id}")
            return new_attachment
        except Exception as e:
            logger.error(f"Error in add_attachment_to_post: {str(e)}", exc_info=True)
            db.session.rollback()
            # אם הייתה שגיאה, ננסה למחוק את הקובץ מ-S3 אם הוא הועלה
            try:
                s3_client.delete_object(Bucket=s3_bucket_name, Key=s3_key)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up S3 object: {str(cleanup_error)}")
            raise
    
    @staticmethod
    def delete_attachment(self, attachment_id):
        try:
            attachment = Attachment.query.get(attachment_id)
            if not attachment:
                raise Exception("Attachment not found")
            
            # מחיקת הקובץ מ-S3
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=attachment.s3_key)
            except ClientError as e:
                raise Exception(f"Error deleting file from S3: {str(e)}")

            # מחיקת הרשומה מבסיס הנתונים
            db.session.delete(attachment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error deleting attachment: {str(e)}")
