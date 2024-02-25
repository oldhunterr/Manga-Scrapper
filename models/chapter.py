import sqlite3


class Chapter:
    def __init__(self, chapter_id, chapter_number, manga_id, chapter_url, downloaded):
        self.chapter_id = chapter_id
        self.chapter_number = chapter_number
        self.manga_id = manga_id
        self.chapter_url = chapter_url
        self.downloaded = downloaded
    
    @staticmethod
    def get_chapter_by_id(chapter_id):
        conn = sqlite3.connect('manga_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ChapterID, ChapterNumber, MangaID, ChapterURL, Downloaded FROM Chapters where ChapterID = ?', (chapter_id,))
        chapter_data = cursor.fetchone()
        conn.close()

        if chapter_data:
            chapter = Chapter(*chapter_data)
            return chapter
        else:
            print(f"No Chapter found in database for Chapter ID: {chapter_id}")
            return None
    
    def serialize(self):
        return {
            "chapter_id": self.chapter_id,
            "chapter_number": self.chapter_number,
            "manga_id": self.manga_id,
            "chapter_url": self.chapter_url,
            "downloaded": self.downloaded
        }