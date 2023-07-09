import pymysql.cursors
import pymysql
import os
from dotenv import load_dotenv
from math import ceil
import lxml.html
import lxml.html.clean

load_dotenv()


def save_add_project_detail(**kwargs):
    connection = pymysql.connect(user=os.getenv("DATABASE_USERNAME"),
                                 password=os.getenv("DATABASE_PASSWORD"),
                                 host=os.getenv("HOST"),
                                 database=os.getenv("DATABASE"),
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
    connection = pymysql.connect(user=os.getenv("DATABASE_USERNAME"),
                                 password=os.getenv("DATABASE_PASSWORD"),
                                 host=os.getenv("HOST"),
                                 database=os.getenv("DATABASE"),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM projects"
            cursor.execute(sql)
            result = cursor.fetchall()

    # image_file_path = os.path.join('Images', result["project_img"])  # Update with your directory path
    # return send_file(image_file_path, mimetype="image/gif")
    return result


def retrieve_project(id):
    connection = pymysql.connect(user=os.getenv("DATABASE_USERNAME"),
                                 password=os.getenv("DATABASE_PASSWORD"),
                                 host=os.getenv("HOST"),
                                 database=os.getenv("DATABASE"),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )
    with connection:
        with connection.cursor() as cursor:
            sql = f"SELECT * FROM projects WHERE id={id}"
            cursor.execute(sql)
            result = cursor.fetchone()

    return result


def count_projects():
    connection = pymysql.connect(user=os.getenv("DATABASE_USERNAME"),
                                 password=os.getenv("DATABASE_PASSWORD"),
                                 host=os.getenv("HOST"),
                                 database=os.getenv("DATABASE"),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(id) FROM projects"
            cursor.execute(sql)
            result = cursor.fetchone()
            count = result['COUNT(id)']
    return count


def get_projects(page, per_page):
    connection = pymysql.connect(user=os.getenv("DATABASE_USERNAME"),
                                 password=os.getenv("DATABASE_PASSWORD"),
                                 host=os.getenv("HOST"),
                                 database=os.getenv("DATABASE"),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )

    with connection:
        with connection.cursor() as cursor:
            offset = (page - 1) * per_page
            sql = f"SELECT * FROM projects LIMIT {per_page} OFFSET {offset}"
            cursor.execute(sql)
            projects = cursor.fetchall()

    total_count = count_projects()

    total_pages = ceil(total_count / per_page)

    return projects, total_pages