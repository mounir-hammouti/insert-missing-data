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
        self.where_condition = sql.SQL("")
        self.select_query = sql.SQL("")
        self.update_query = sql.SQL("")

    def execute_query(self,query):
        try:
            self.cursor.execute(query)
        except Exception as e:
            self.logger.error(e)
            self.conn.rollback()
        else:
            self.conn.commit()

    def create_join_clause(self,column_name):
    
        joins = self.parameters_dict.get("Joins").get(column_name)
        join_clause = sql.SQL("")

        if joins: # check if dictionary is not empty
            for key, value in joins.items():
                if "tables_to_join" in value: # check if there are tables to join
                    tables_list = value.get("tables_to_join")
                    if tables_list: # check if list is not empty
                        for table in tables_list:
                            join_type = table.get("join_type").strip()
                            table_name = table.get("name").strip()
                            primary_key = value.get("primary_key").strip()
                            foreign_key = joins.get(table_name).get("foreign_keys").get(key).strip()
                            join_query =  sql.SQL(join_type + " join {} on {} = {}\n").format(sql.Identifier(table_name),
                                                                        sql.Identifier(key, primary_key),
                                                                        sql.Identifier(table_name, foreign_key) )
                            join_clause = sql.Composed([join_clause, join_query])

        return join_clause
    
    def create_where_condition(self,where_condition, table_and_field_to_check,value_to_check):

        if not where_condition.as_string(self.cursor): # if the where condition is empty (first iteration of for loop)
            where_check = sql.SQL("WHERE {field_name}={value}").format(field_name=sql.Identifier(*table_and_field_to_check),
                                                                    value = sql.Literal(value_to_check))
            where_condition = sql.Composed([where_condition, where_check])
        else:
            where_check = sql.SQL(" AND {field_name}={value}").format(field_name=sql.Identifier(*table_and_field_to_check),
                                                                        value = sql.Literal(value_to_check))
            where_condition = sql.Composed([where_condition, where_check])

        return where_condition
    
    def create_update_query(self, table, field, value):
        update_query = sql.SQL("UPDATE {table} SET {field} = {value} WHERE id in").format(
                                                    table=sql.Identifier(table),
                                                    field=sql.Identifier(field),
                                                    value=sql.Literal(value)
                                                    )
        
        update_query = sql.Composed([update_query, sql.SQL("("), self.select_query, sql.SQL(")")])
        
        self.logger.info(update_query.as_string(self.cursor).replace('\n', ' '))

        return update_query
    
    def pretty_table_from_query_result(self, result):
        columns = [desc[0] for desc in self.cursor.description]
        dict_list = []
        for row in result:
            dict_list.append(dict(zip(columns, row)))
        dd = defaultdict(list)
        for d in dict_list:
            for key, value in d.items():
                dd[key].append(value)
        return tabulate(dd, headers="keys")
    
    def execute(self):
        columns_to_update = self.parameters_dict.get("Columns_to_update")

        for row in tqdm(self.dataframe.itertuples(), total=self.dataframe.shape[0], desc="dataframe reading"):
            for key1, value1 in columns_to_update.items():
                
                table_to_update = value1.get("table_name")
                field_to_update = value1.get("field_name")
                value_to_update = getattr(row, key1)
                table_and_field_to_select = (table_to_update,"id")

                join_clause = self.create_join_clause(key1)
                identifying_columns = self.parameters_dict.get("Identifying_columns").get(key1)

                values_to_check = []
                count = 0
                
                where_condition = sql.SQL("")

                for key2, value2 in identifying_columns.items():

                    table_to_check = value2.get("table_name")
                    field_to_check = value2.get("field_name")
                    table_and_field_to_check = (table_to_check,field_to_check)

                    value_to_check = getattr(row, key2)
                    if isinstance(value_to_check, str):
                        value_to_check = value_to_check.strip().lower()
                    values_to_check.append(value_to_check)

                    self.where_condition = self.create_where_condition(where_condition,table_and_field_to_check,value_to_check)

                    select_fields = sql.SQL("SELECT DISTINCT {fields}\nFROM {table}\n").format(
                                                    fields=sql.Identifier(*table_and_field_to_select),
                                                    table=sql.Identifier(table_to_update))
                    
                    self.select_query = sql.Composed([select_fields, join_clause, self.where_condition])

                    self.execute_query(self.select_query)
                    result = self.cursor.fetchall()
                    result_table = self.pretty_table_from_query_result(result)
                    
                    count += 1
                    if count == 1:
                        self.logger.debug("-----------------------------------------------")

                    self.logger.debug("Select Query:")
                    self.logger.debug(self.select_query.as_string(self.cursor).replace('\n', ' '))
                    self.logger.debug("Query results:\n" + result_table)
                    
                    if not result:
                        self.logger.info("No result has been returned by select query.")
                    elif len(result) == 1:
                        if value_to_update and pd.notna(value_to_update):
                            self.logger.info("One result has been returned. Making the update.")
                            self.logger.debug("Update Query:")
                            self.update_query = self.create_update_query(table_to_update, field_to_update , value_to_update)
                            self.execute_query(self.update_query)
                            break
                        else:
                            self.logger.info("No value to update for {} {}.".format(', '.join(values_to_check) , 
                                                                                    'value' if len(values_to_check) <= 1 else 'values'))
                    else:
                        self.logger.info("Multiple results have been returned by select query. No Update.")