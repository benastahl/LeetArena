import secrets
import sqlalchemy
import uuid
import bcrypt
import os

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import text

from datetime import datetime
from termcolor import colored
from models import User

if not os.getenv("PUBLIC_ACTIVATED"):
    assert load_dotenv(find_dotenv()), "Failed to load environment."

sql_host = os.getenv("SQL_HOST")
sql_username = os.getenv("SQL_USERNAME")
sql_password = os.getenv("SQL_PASSWORD")
sql_database = os.getenv("SQL_DATABASE")

google_app_password = os.getenv("GOOGLE_APP_PASSWORD")

# dialect+driver://username:password@host:port/database

tables = {
    "user": {
        "attributes": [
            "entry_id:TEXT",
            "email:TEXT",
            "username:TEXT",
            "hashed_password:TEXT",
            "auth_token:TEXT",
            "creation_date:INT",
            "admin:INT",
        ],
        "instance": User
    },
}


class LeetArena:
    def __init__(self):
        self.table_name = "TBD"
        self.table_attributes = None
        self.Instance = None
        self.connection_id = uuid.uuid4()

    def __enter__(self):
        self.log("Connecting to database...", "p")
        self.database = sqlalchemy.create_engine(
            f"mysql+pymysql://{sql_username}:{sql_password}@{sql_host}/{sql_database}")
        self.connection = self.database.connect()
        self.log(f"Successfully connected to database '{sql_database}' ({self.connection_id}).", "s")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.commit()
        self.connection.close()
        self.database.dispose()
        self.log(f"Connection closed and database engine disposed. ({self.connection_id})", "p")

    def set_table(self, table_name: str):
        self.table_name = table_name
        self.table_attributes = tables[table_name]['attributes']
        self.Instance = tables[table_name]['instance']

    def log(self, text: str, status: str) -> None:
        """
        Prints informative log message with details of process occurring.
        :param text: Message printed.
        :param status: Color of message. Signals status of process.
        :return:
        """
        color_schemes = {
            "s": "green",
            "f": "red",
            "p": "cyan",
            "d": "yellow"
        }
        print(
            colored(
                f"[{datetime.now().strftime('%m-%d-%Y %H:%M:%S')}] - "
                f"[ATHLEATS: {self.table_name.upper()}] - "
                f"{text}",
                color_schemes.get(status)
            )
        )

    @staticmethod
    def sql_conv(value):
        if type(value) == int:
            return f"{value}"
        else:
            return f"'{value}'"

    def create_table(self, table_name: str, reset=False) -> bool:
        self.set_table(table_name)
        """
        Creates a new table based on table_attributes. Should only be used once.
        :param table_name: 
        :param close_conn:
        :param reset: Deletes table in entirety before creating new one (if set to 'True').
        :return: True bool if successful.
        """
        if reset:
            self.log("Are you sure? This will delete all existing data in the table.", "d")
            input("Press enter to continue")
            self.log(f"Resetting table (dropping) '{table_name}'.", "d")
            self.connection.execute(text(f"DROP TABLE {table_name}"))
        attributes = ", ".join([f"{attr.split(':')[0]} {attr.split(':')[1]}" for attr in self.table_attributes])
        self.connection.execute(text(f'CREATE TABLE {table_name} ({attributes})'))
        self.log(f"Successfully created table '{table_name}'", "s")
        return True

    def create_entry(self, table_name: str, **kwargs):
        self.set_table(table_name)
        # Creates a row in our database table

        # Asserts that our table attributes order matches the kwargs order (sql order matters lol)
        assert [attr.split(":")[0] for attr in self.table_attributes] == [kwarg for kwarg in
                                                                          kwargs.keys()], "table_attributes does not match correspond with the kwargs in create_entry call."

        # Create SQL query strings
        attributes = ", ".join([self.sql_conv(kwarg) for kwarg in kwargs.values()])
        conditions = " AND ".join([f"{kwarg} = {self.sql_conv(kwargs[kwarg])}" for kwarg in kwargs])

        self.connection.execute(
            text(f"INSERT INTO {table_name} "
                 f"VALUES ({attributes})")
        )
        entries = self.connection.execute(text(f"SELECT * FROM {table_name} WHERE {conditions}")).fetchall()
        print(entries)

        assert entries, f"Failed to find an entry with kwargs given ({kwargs})."
        entry = entries[0]
        self.log(f"Successfully created entry '{kwargs.get('entry_id')}'.", "s")
        return self.Instance(*entry)

    def edit_entry(self, table_name: str, entry_id, **kwargs):
        self.set_table(table_name)
        conditions = ", ".join([f"{kwarg} = {self.sql_conv(kwargs[kwarg])}" for kwarg in kwargs])
        self.connection.execute(
            text(f"UPDATE {table_name} "
            f"SET {conditions} "
            f"WHERE entry_id = '{entry_id}'")
        )

        entries = self.connection.execute(text(f"SELECT * FROM {table_name} WHERE entry_id = '{entry_id}'")).fetchall()
        assert entries, f"Failed to find a entry with kwargs given ({kwargs})."
        entry = entries[0]
        return self.Instance(*entry)

    def delete_entry(self, table_name: str, entry_id):
        self.set_table(table_name)
        self.connection.execute(
            text(f"DELETE FROM {table_name} "
            f"WHERE entry_id = '{entry_id}'")
        )
        self.log(f"Deleted entry: {entry_id}.", "p")

    def get_entry(self, table_name: str, **filters):
        self.set_table(table_name)
        conditions = " AND ".join([f"{param} = {self.sql_conv(filters[param])}" for param in filters])
        entries = self.connection.execute(text(f"SELECT * FROM {table_name} WHERE {conditions}")).fetchall()
        if not entries:
            return False
        entry = entries[0]
        self.log(f"Successfully collected entry '{entry[0]}'", "s")
        print("ENTRY:", entry)

        return self.Instance(*entry)

    def get_all_entries(self, table_name: str, **filters):
        self.set_table(table_name)
        conditions = " AND ".join([f"{param} = {self.sql_conv(filters[param])}" for param in filters])
        query_string = \
            f"SELECT * " \
            f"FROM {table_name} "

        if filters:
            query_string += f"WHERE {conditions}"

        entries = self.connection.execute(text(query_string)).fetchall()
        if not entries:
            return []

        # assert entries, f"Failed to find a entry with kwargs given ({kwargs})."
        self.log(f"Successfully collected entries from table '{table_name}'", "s")

        return [self.Instance(*entry) for entry in entries]

    def login_user(self, email, password, new_auth=True):

        # Authenticates user email and password
        user = self.get_entry(table_name="user", email=email)
        if not user or not bcrypt.checkpw(bytes(password.encode("utf-8")), user.hashed_password.encode("utf-8")):
            return False
        if new_auth:
            # Creates new random auth token string
            auth_token = secrets.token_hex()
            # Sets new auth token to user database row
            authenticated_user = self.edit_entry(table_name="user", entry_id=user.entry_id, auth_token=auth_token)

            # Returns new auth token of authenticated user
            return authenticated_user.auth_token

        # Returns current auth token of user
        return user.auth_token
