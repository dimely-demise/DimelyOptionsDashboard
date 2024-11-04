from sqlalchemy import create_engine, text
import pandas as pd
import traceback

class Database:
    def __init__(self, host: str, user: str, password: str, database: str):
        try:
            # Initialize SQLAlchemy engine with pymysql as the driver
            self.engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}")
            self.mostRecentUpdate = None
            print("Database connection established successfully.")
        except Exception as e:
            print("An error occurred while connecting to the database:")
            print(e)
            traceback.print_exc()

    def get_options_watchlist(self) -> pd.DataFrame:
        try:
            # Use read_sql to directly load data into a DataFrame
            query = "SELECT * FROM OptionsWatchlist where expiry >= NOW()"
            df = pd.read_sql(query, self.engine)
            df['latestUpdate'] = pd.to_datetime(df['latestUpdate'], errors='coerce')
            df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce')

            self.mostRecentUpdate = df["latestUpdate"].max()
            print("Data retrieved successfully.")
            return df
        except Exception as e:
            print("An error occurred while fetching data:")
            print(e)
            traceback.print_exc()
            return pd.DataFrame()  # Return empty DataFrame on error
        
    def store_updates(self, df: pd.DataFrame):
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    for index, row in df[df["latestUpdate"] >= self.mostRecentUpdate].iterrows():
                        update_values = {
                            "bid": row.get('bid'),
                            "ask": row.get('ask'),
                            "undPrice": row.get('undPrice'),
                            "delta": row.get('delta'),
                            "impliedVolatility": row.get('IV'),
                            "day": row.get('latestUpdate')
                        }
                        update_values = {k: (v if pd.notna(v) else None) for k, v in update_values.items()}
                        if update_values:
                            set_clause = ", ".join([f"{col} = :{col}" for col in update_values.keys()])  # Use named parameters
                            sql = f"UPDATE optiondata SET {set_clause} WHERE contractId = :contractId"
                            
                            # Include the contract ID in the update values
                            update_values['contractId'] = row['id']
                            
                            # Use text() to make the SQL string executable
                            conn.execute(text(sql), update_values)  # Pass a dictionary instead of a list
                    print("Data updated successfully.")
                    self.mostRecentUpdate = df["latestUpdate"].max()
        except Exception as e:
            print("An error occurred while updating data:")
            print(e)
            traceback.print_exc()




    def close(self):
        # SQLAlchemy engine doesn't need explicit close, but we can dispose of the connection
        self.engine.dispose()
        print("Database connection closed.")
