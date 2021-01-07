import sqlite3


class DatabaseManager:
    ''' Database Manager '''

    def __init__(self, db_name):
        self.db_name = db_name  # database name
        self.conn = None        # connection

    def check_database(self):
        ''' Check if the database exists or not '''

        try:
            self.conn = sqlite3.connect(self.db_name, uri=True)
            return True

        except sqlite3.OperationalError as err:
            return False

    def close_connection(self):
        ''' Close connection to database '''

        if self.conn is not None:
            self.conn.close()
