from database import DatabaseManager

def main():
    print("Inizializzazione database...")
    db_manager = DatabaseManager()
    db_manager.create_tables()
    print(f"Database creato in: {db_manager.db_path}")

if __name__ == "__main__":
    main()
