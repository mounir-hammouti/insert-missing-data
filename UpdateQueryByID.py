from psycopg2 import sql
from tabulate import tabulate
from collections import defaultdict
import pandas as pd
from tqdm import tqdm

class UpdateQueryByID:
  
    def __init__(self, logger, conn, cursor, parameters_dict, dataframe):
        self.logger = logger
        self.conn = conn
        self.cursor = cursor
        self.parameters_dict = parameters_dict
        self.dataframe = dataframe

    def execute_query(self,query):
        try:
            self.cursor.execute(query)
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            self.conn.rollback()
        else:
            self.logger.info(f"Query executed successfully.")
            self.conn.commit()

    def create_join_clause(self,column_name):
        joins = self.parameters_dict.get("Joins").get(column_name)
        join_queries = []

        if joins: # check if dictionary is not empty
            for key, value in joins.items():
                tables_list = value.get("tables_to_join", []) # return empty list if no tables_to_join key
                if tables_list: # check if list is not empty
                    for table in tables_list:
                        join_type = table.get("join_type").strip()
                        table_name = table.get("name").strip()
                        primary_key = value.get("primary_key").strip()
                        foreign_key = joins.get(table_name).get("foreign_keys").get(key).strip()
                        join_query = sql.SQL(join_type.upper() + " JOIN {} on {} = {}").format(
                            sql.Identifier(table_name),
                            sql.Identifier(key, primary_key),
                            sql.Identifier(table_name, foreign_key)
                        )
                        join_queries.append(join_query)
        
        return sql.SQL("\n").join(join_queries)
    
    def create_where_clause(self,where_conditions, table_and_field_to_check,value_to_check):
        where_check = sql.SQL("{field_name}={value}").format(
            field_name=sql.Identifier(*table_and_field_to_check),
            value = sql.Literal(value_to_check)
        )

        where_conditions.append(where_check)

        return sql.SQL(" AND ").join(where_conditions)
    
    def create_update_query(self, table, field, value, select_query):
        update_query = sql.SQL("UPDATE {table} SET {field} = {value} WHERE id IN").format(
                table=sql.Identifier(table),
                field=sql.Identifier(field),
                value=sql.Literal(value)
        )
        
        update_query = sql.Composed([update_query, sql.SQL("("), select_query, sql.SQL(")")])
        
        self.logger.debug("Update Query:")
        self.logger.debug(update_query.as_string(self.cursor).replace('\n', ' '))

        return update_query
    
    def pretty_table_from_query_result(self, result):
        columns = [desc[0] for desc in self.cursor.description]
        dict_list = [dict(zip(columns, row)) for row in result]
        dd = defaultdict(list)
        for d in dict_list:
            for key, value in d.items():
                dd[key].append(value)

        return tabulate(dd, headers="keys")
    
    def execute(self):
        columns_to_update = self.parameters_dict.get("Columns_to_update")

        for index, row in tqdm(self.dataframe.iterrows(), total=self.dataframe.shape[0], desc="dataframe reading"):
            self.logger.debug("Reading line number {line} from excel file.".format(line=index))

            for key1, value1 in columns_to_update.items():
                self.logger.debug("Reading column {col}.".format(col=key1))
                table_to_update = value1.get("table_name")
                field_to_update = value1.get("field_name")
                value_to_update = row[key1]
                table_and_field_to_select = (table_to_update, "id")

                where_conditions = []

                identifying_columns = self.parameters_dict.get("Identifying_columns").get(key1)
                identifying_column_items = list(identifying_columns.items())
                no_value_to_update = False
                value_updated = False
                i = 0

                while i < len(identifying_column_items) and not value_updated and not no_value_to_update:
                    key2, value2 = identifying_column_items[i]
                    table_to_check = value2.get("table_name")
                    field_to_check = value2.get("field_name")
                    value_to_check = row[key2]
                    table_and_field_to_check = (table_to_check,field_to_check)

                    if isinstance(value_to_check, str):
                        value_to_check = value_to_check.strip().lower()

                    select_clause = sql.SQL("SELECT DISTINCT {fields}\nFROM {table}\n").format(
                            fields=sql.Identifier(*table_and_field_to_select),
                            table=sql.Identifier(table_to_update)
                    )
                    join_clause = self.create_join_clause(key1)
                    where_clause = self.create_where_clause(where_conditions,table_and_field_to_check,value_to_check)

                    select_query = sql.Composed([select_clause, join_clause, sql.SQL("\nWHERE "), where_clause])
                    self.logger.debug("Select Query:")
                    self.logger.debug(select_query.as_string(self.cursor).replace('\n', ' '))

                    self.execute_query(select_query)
                    result = self.cursor.fetchall()
                    result_table = self.pretty_table_from_query_result(result)
                    self.logger.debug("Query results:\n" + result_table)
                    
                    if not result:
                        self.logger.warn("No result has been returned by select query.")
                        no_value_to_update = True
                    elif len(result) == 1:
                        if value_to_update and pd.notna(value_to_update):
                            self.logger.info("One result has been returned. Making the update.")
                            update_query = self.create_update_query(table_to_update, field_to_update , value_to_update, select_query)
                            self.execute_query(update_query)
                            value_updated = True
                        else:
                            self.logger.info("No value to update in excel file.")
                            no_value_to_update = True
                    else:
                        self.logger.warn("Multiple results have been returned by select query. No Update.")
                    
                    i += 1

                if not value_updated: self.logger.warn("No value has been updated in database.")    
                self.logger.debug("-----------------------------------------------")