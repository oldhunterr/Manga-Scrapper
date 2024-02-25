import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('manga_database.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sources (
        SourceID INTEGER PRIMARY KEY,
        SourceName TEXT NOT NULL,
        SourceURL TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Manga (
        MangaID INTEGER PRIMARY KEY,
        Title TEXT NOT NULL,
        Description TEXT,
        SourceID INTEGER NOT NULL,
        MangaURL TEXT NOT NULL,
        FOREIGN KEY (SourceID) REFERENCES Sources(SourceID)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Chapters (
        ChapterID INTEGER PRIMARY KEY,
        ChapterNumber INTEGER NOT NULL,
        MangaID INTEGER NOT NULL,
        ChapterURL TEXT NOT NULL,
        FOREIGN KEY (MangaID) REFERENCES Manga(MangaID)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Images (
        ImageID INTEGER PRIMARY KEY,
        ChapterID INTEGER NOT NULL,
        ImageURL TEXT NOT NULL,
        ImagePath TEXT,
        FOREIGN KEY (ChapterID) REFERENCES Chapters(ChapterID)
    )
''')

# Commit changes and close connection
conn.commit()
conn.close()
