import os
from dotenv import load_dotenv
from mylogger import getmylogger
from Database import Database
from UpdateQueryByID import UpdateQueryByID
import inquirer
from inquirer.themes import GreenPassion
import json
import pandas as pd

load_dotenv()
logger = getmylogger(__name__)

db_connection_dict = {
    'dbname': str(os.getenv('DB_NAME')),
    'user': str(os.getenv('DB_USER')),
    'password': str(os.getenv('DB_PASSWORD')),
    'host': str(os.getenv('DB_HOST')),
    'port': str(os.getenv('DB_PORT')),
    'options': """-c search_path="{schema}" """.format(schema=str(os.getenv('DB_SCHEMA')))
}

db_connection = Database(db_connection_dict)

def read_config_file_and_excel_file():
    data_folder = os.path.join('.', 'data_to_update')
    data_files = os.listdir(data_folder)
    config_folder = os.path.join('.', 'config_files')
    config_files = os.listdir(config_folder)

    configFile_and_excelFile_questions = [
        inquirer.List('data_file',
                        message="Choose the dataframe file in data_to_update folder",
                        choices=data_files,
                        ),
        inquirer.List('config_file',
                        message="Choose the json file in config_files folder",
                        choices=config_files,
                        )
    ]

    answers = inquirer.prompt(configFile_and_excelFile_questions, theme=GreenPassion())

    data_file = os.path.join(data_folder, answers['data_file'])
    config_file = os.path.join(config_folder, answers['config_file'])

    logger.info(f"Reading {data_file} file.")
    dataframe = pd.read_excel(data_file)

    logger.info(f"Reading {config_file} config file.")
    with open(config_file) as json_file:
        query_parameters = json.load(json_file)

    return query_parameters, dataframe

def main():
    query_parameters, dataframe = read_config_file_and_excel_file()
    Update_Database =UpdateQueryByID(logger, db_connection.conn, db_connection.conn.cursor(), query_parameters, dataframe)
    Update_Database.execute()
 
if __name__ == "__main__":
    main()