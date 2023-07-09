import pymysql.cursors
import pymysql
import os
from dotenv import load_dotenv
from flask import send_file
import cryptography

load_dotenv()


def save_add_project_detail(**kwargs):
    connection = pymysql.connect(user=os.getenv("user"),
                                 password=os.getenv("password"),
                                 host=os.getenv('host'),
                                 database=os.getenv("database"),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )
    print(kwargs)
    with connection:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "INSERT INTO projects (project_name, project_overview, project_code_overview, project_img) " \
                  "VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (
                kwargs["details"]["project_name"],
                kwargs["details"]["project_overview"],
                kwargs["details"]["project_code_overview"],
                kwargs["details"]["project_img"])
                           )
        connection.commit()


def project_list():
    connection = pymysql.connect(user=os.getenv("user"),
                                 password=os.getenv("password"),
                                 host=os.getenv('host'),
                                 database=os.getenv("database"),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM projects"
            cursor.execute(sql)
            result = cursor.fetchone()

    # image_file_path = os.path.join('Images', result["project_img"])  # Update with your directory path
    # return send_file(image_file_path, mimetype="image/gif")
    return result
