import psycopg2

class Database:

    def __init__(self,param_dict):
        self.conn = self.connect_bd(param_dict)

    def connect_bd(self, param_dict):
        conn = None
        try:
            conn = psycopg2.connect(**param_dict)
            conn.set_client_encoding('UTF8')
            print("Connection successful")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            conn = None

        return conn