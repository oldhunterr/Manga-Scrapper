import os
import sqlite3

import requests
class Manga:
    def __init__(self, manga_id, title, description, source_id, manga_url, image_path, image_url):
        self.manga_id = manga_id
        self.title = title
        self.description = description
        self.source_id = source_id
        self.manga_url = manga_url
        self.image_path = image_path
        self.image_url = image_url
        self.chapters = []

    def add_chapter(self, chapter):
        self.chapters.append(chapter)

    def remove_chapter(self, chapter_number):
        self.chapters = [chapter for chapter in self.chapters if chapter.chapter_number != chapter_number]
    
    def manga_link_exists(manga_link):
        conn = sqlite3.connect('manga_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM Manga WHERE MangaURL = ?', (manga_link,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    @staticmethod
    def get_manga_from_database(manga_link):
        conn = sqlite3.connect('manga_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Manga WHERE MangaURL = ?', (manga_link,))
        manga_data = cursor.fetchone()
        conn.close()

        if manga_data:
            manga = Manga(*manga_data)
            return manga
        else:
            print(f"No manga found in database for URL: {manga_link}")
            return None
    
    @staticmethod
    def get_manga_from_database_by_id(manga_id):
        conn = sqlite3.connect('manga_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Manga WHERE MangaID = ?', (manga_id,))
        manga_data = cursor.fetchone()
        conn.close()

        if manga_data:
            manga = Manga(*manga_data)
            return manga
        else:
            print(f"No manga found in database for manga id: {manga_id}")
            return None
    
    def save(self):
        conn = sqlite3.connect('manga_database.db')
        cursor = conn.cursor()
        sql = 'INSERT INTO Manga (Title, Description, SourceID, MangaURL, ImagePath, ImageURL) VALUES (?, ?, ?, ?, ?, ?)'
        values = (self.title or '', self.description or '', self.source_id or 0, self.manga_url or '', self.image_path or '', self.image_url or '')
        cursor.execute(sql, values)
        manga_id = cursor.lastrowid
        conn.commit()

        # Fetch the newly inserted row from the database
        cursor.execute('SELECT * FROM Manga WHERE MangaID = ?', (manga_id,))
        manga_data = cursor.fetchone()
        conn.close()

        # Create a new Manga object with the fetched data and return it
        return Manga(*manga_data)

    def update(self):
        if not self.manga_id:
            print("Manga ID is required for update.")
            return
        conn = sqlite3.connect('manga_database.db')
        cursor = conn.cursor()
        sql = 'UPDATE Manga SET Title = ?, Description = ?, SourceID = ?, MangaURL = ?, ImagePath = ?, ImageURL = ? WHERE MangaID = ?'
        values = (self.title or '', self.description or '', self.source_id or 0, self.manga_url or '', self.image_path or '', self.image_url or '', self.manga_id)
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        print("Manga updated successfully.")
    
    def save_image(manga):
        image_response = requests.get(manga.image_url)
        if image_response.status_code == 200:
            # Create directories if they don't exist
            directory = f'images/sources/{manga.source_id}/manga_{manga.manga_id}'
            os.makedirs(directory, exist_ok=True)
            
            image_extension = os.path.splitext(manga.image_url)[1]
            image_name = f"poster{image_extension}" 
            
            # Save the image to the specified directory
            image_path = os.path.join(directory, image_name)
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            
            # Update manga object with image path
            manga.image_path = image_path
            manga.update()
            
    @staticmethod
    def fetch_all_manga():
        conn = sqlite3.connect('manga_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT MangaID, Title, Description, SourceID, MangaURL, ImagePath, ImageURL FROM Manga')
        manga_data = cursor.fetchall()
        conn.close()
        manga_list = []
        for manga_row in manga_data:
            manga = Manga(*manga_row)
            manga_list.append(manga)
        return manga_list
    
    def __str__(self):
        return f"Manga(manga_id={self.manga_id}, title='{self.title}', description='{self.description}', source_id={self.source_id}, manga_url='{self.manga_url}', image_path='{self.image_path}', image_url='{self.image_url}')"
    