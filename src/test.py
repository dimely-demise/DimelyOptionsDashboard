from infrastructure.Database import Database

db = Database('127.0.0.1', 'root', 'dev', 'tws')  
df = db.get_options_watchlist()
print(df)