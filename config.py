import os
import json

class Config:
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
    CHATBOX_EMAIL = os.environ.get('CHATBOX_EMAIL')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    DATABASE_USERNAME = os.environ.get('DATABASE_USERNAME')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
    HOST = os.environ.get('HOST')
    DATABASE = os.environ.get('DATABASE')
    SECRET_KEY = os.environ.get('SECRET_KEY')
