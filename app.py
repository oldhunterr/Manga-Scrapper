import os
import re
import time
from bs4 import BeautifulSoup
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import sqlite3

import requests
from models.source import Source
from models.manga import Manga
from models.chapter import Chapter
from models.image import Image
from models.element_types import ElementType
from models.source_setting import SourceSetting
from models.database import db, init_db

app = Flask(__name__)
app.secret_key = 'GreyHairedHunter'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Enable SQLAlchemy logging

database_uri = app.config['SQLALCHEMY_DATABASE_URI']
print(database_uri)
# Initialize the database
init_db(app)

admin = Admin(app)

# Add views for Source and SourceSetting models
admin.add_view(ModelView(Source, db.session))
admin.add_view(ModelView(SourceSetting, db.session))
admin.add_view(ModelView(ElementType, db.session))

def scrape_manga_details(manga: Manga):
    response = requests.get(manga.manga_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    image_div = soup.find('div', class_='summary_image')
    if image_div:
        image_url = image_div.find('img')['src']
        manga.image_url = image_url
    
    title_div = soup.find('div', class_='post-title')
    if title_div:
        title = title_div.find('h1').text.strip()
        manga.title = title
    
    description_div = soup.find('div', class_='description-summary')
    if description_div:
        description = description_div.text.strip()
        manga.description = description
    manga = manga.save()
    manga.save_image()
    return manga

def scrape_manga_chapters(manga: Manga):
    response = requests.get(manga.manga_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the div containing the list of chapters
        chapters_div = soup.find('div', class_='listing-chapters_wrap')

        if chapters_div:
            # Find all list items within the chapters div
            chapters_list = chapters_div.find_all('li', class_='wp-manga-chapter')

            for chapter_item in chapters_list:
                # Extract chapter URL and number
                chapter_url = chapter_item.find('a')['href']
                chapter_text = chapter_item.find('a').text.strip()

                # Use regular expressions to extract only the numeric part of the text
                chapter_number_match = re.search(r'\d+(\.\d+)?', chapter_text)
                if chapter_number_match:
                    chapter_number = chapter_number_match.group()
                else:
                    # If no numeric part found, skip this chapter
                    continue
                
                conn = sqlite3.connect('manga_database.db')
                cursor = conn.cursor()
                # Check if chapter already exists in the database for the manga
                cursor.execute('SELECT ChapterID FROM Chapters WHERE MangaID = ? AND ChapterNumber = ?', (manga.manga_id, chapter_number))
                existing_chapter = cursor.fetchone()
                if existing_chapter:
                    # Chapter already exists, skip insertion
                    chapter_id = existing_chapter[0]
                    print("SKIPPING CHAPTER EXIST", chapter_number, manga.title)
                else:
                    # Insert chapter into the database
                    print("INSERTING ", chapter_number)
                    cursor.execute('INSERT INTO Chapters (ChapterNumber, MangaID, ChapterURL) VALUES (?, ?, ?)', (chapter_number, manga.manga_id, chapter_url))

                    # Retrieve the auto-generated chapter ID
                    chapter_id = cursor.lastrowid

                    # Commit changes to the database
                    conn.commit()

                # Create Chapter object and add it to the manga object
                chapter = Chapter(chapter_id=chapter_id, chapter_number=chapter_number, manga_id=manga.manga_id, chapter_url=chapter_url,downloaded=0)
                manga.add_chapter(chapter)
    return manga


def handle_post_search(request):
    source = request.form.get('source')
    manga_link = request.form.get('manga_link')
    manga = Manga(None,None,None,None,None,None,None)
    if(Manga.manga_link_exists(manga_link)):
        print("EXIST")
        manga = Manga.get_manga_from_database(manga_link)
    else:
        print("Doesn't Exist")
        manga.manga_url = manga_link
        manga.source_id = source
        manga = scrape_manga_details(manga)
    # manga = scrape_manga_chapters(manga)
    # Here you can handle the form submission, e.g., search for manga
    return f'Searching for manga from source: {source}, with link: {manga_link}'

from flask import request




@app.route('/bulk_download_chapters', methods=['POST'])
def bulk_download_chapters():
    data = request.json
    manga_id = data.get('manga_id')
    selected_chapters = data.get('selected_chapters', [])
    source_id = data.get('source_id')
    
    print("Bulk Downloading Chapter - START")
    for chapter_id in selected_chapters:
        print("Downloading Chapter : ",chapter_id)
        chapter = Chapter.get_chapter_by_id(chapter_id)
        if(chapter):
            chapter = download_chapter_from_bulk(chapter,source_id,manga_id)
            time_remaining = 60
            if(chapter.downloaded == 1):
                print("Chapter Downloaded: ",chapter.chapter_number)
            # for i in range(5, 0, -1):
            #     print(f"Time left: {i} seconds")
            #     time.sleep(1)
            #     time_remaining -= 1
            # # Wait for 1 minute between chapters
            # time.sleep(55)

    # Redirect to manga details page or any other page as needed
    print("Bulk Downloading Chapter - END")
    return jsonify({"message": "Bulk download completed successfully"}), 200

def download_chapter_from_bulk(chapter: Chapter, source_id: int, manga_id: int):
    chapter_url = chapter.chapter_url
    chapter_number = chapter.chapter_number
    chapter_id = chapter.chapter_id

    conn = sqlite3.connect('manga_database.db')
    cursor = conn.cursor()
    # Create directories if they don't exist
    directory = f'images/sources/{source_id}/manga_{manga_id}/chapters/{chapter_number}'
    os.makedirs(directory, exist_ok=True)

    # Fetch images from the chapter URL using BeautifulSoup
    response = requests.get(chapter_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        images = soup.find_all('img', class_='wp-manga-chapter-img')
        # Download and save images to the specified directory
        for index, img in enumerate(images):
            image_url = img['src']
            image_extension = image_url.split('.')[-1]
            image_path = os.path.join(directory, f'{index+1}.{image_extension}')
            with open(image_path, 'wb') as f:
                image_data = requests.get(image_url).content
                f.write(image_data)

                # Add record to the Images table in the database
                cursor.execute('INSERT INTO Images (ChapterID, ImageURL, ImagePath, ImageOrder) VALUES (?, ?, ?, ?)',
               (chapter_id, image_url, image_path, index+1))

        
        # Mark chapter as downloaded in the database
        cursor.execute('UPDATE Chapters SET Downloaded = 1 WHERE ChapterID = ?', (chapter_id,))
        conn.commit()
        chapter.downloaded = 1
        return chapter

@app.route('/download_chapter', methods=['POST'])
def download_chapter():
    manga_id = request.form['manga_id']
    chapter_url = request.form['chapter_url']
    source_id = request.form['source_id']
    chapter_number = request.form['chapter_number']
    chapter_id = request.form['chapter_id']

    conn = sqlite3.connect('manga_database.db')
    cursor = conn.cursor()
    # Create directories if they don't exist
    directory = f'images/sources/{source_id}/manga_{manga_id}/chapters/{chapter_number}'
    os.makedirs(directory, exist_ok=True)

    # Fetch images from the chapter URL using BeautifulSoup
    response = requests.get(chapter_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        images = soup.find_all('img', class_='wp-manga-chapter-img')
        # Download and save images to the specified directory
        for index, img in enumerate(images):
            image_url = img['src']
            image_extension = image_url.split('.')[-1]
            image_path = os.path.join(directory, f'{index+1}.{image_extension}')
            with open(image_path, 'wb') as f:
                image_data = requests.get(image_url).content
                f.write(image_data)

                # Add record to the Images table in the database
                cursor.execute('INSERT INTO Images (ChapterID, ImageURL, ImagePath, ImageOrder) VALUES (?, ?, ?, ?)',
               (chapter_id, image_url, image_path, index+1))

        
        # Mark chapter as downloaded in the database
        cursor.execute('UPDATE Chapters SET Downloaded = 1 WHERE ChapterID = ?', (chapter_id,))
        conn.commit()

        # Redirect to manga details page or any other page as needed
        return redirect(url_for('manga_details', manga_id=manga_id))
    
def get_manga_details(manga_id):
    conn = sqlite3.connect('manga_database.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT m.MangaID, m.Title, m.Description, m.ImageURL, m.ImagePath, m.SourceID, c.ChapterID, c.ChapterNumber, c.ChapterURL, c.Downloaded
    FROM Manga m
    LEFT JOIN Chapters c ON m.MangaID = c.MangaID
    WHERE m.MangaID = ?
''', (manga_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    manga_info = rows[0]
    manga_id, title, description, image_url, image_path , source_id = manga_info[:6]
    
    chapters = []
    for row in rows:
        if row[6] is not None:  # Check if chapter data is available
            chapter_id, chapter_number, chapter_url, downloaded = row[6:]
            chapter = Chapter(chapter_id, chapter_number, manga_id, chapter_url,downloaded)
            chapters.append(chapter)

    manga = Manga(manga_id, title, description,source_id,None,image_path,image_url)
    manga.chapters = chapters
    return manga

@app.route('/manga/<int:manga_id>')
def manga_details(manga_id):
    # Fetch manga details from the database based on manga_id
    manga_details = get_manga_details(manga_id)
    if manga_details:
        return render_template('manga_details.html', manga=manga_details)
    else:
        # If manga is not found, redirect to the homepage or display an error message
        return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        handle_post_search(request)
    # Fetch sources from the database
    sources = Source.get_sources()
    # Fetch all manga from the database
    manga_data = Manga.fetch_all_manga()
    return render_template('index.html', sources=sources, manga_data=manga_data)

@app.route('/fetch_chapters', methods=['POST'])
def fetch_chapters():
    # Get the manga ID from the request data
    manga_id = request.json.get('manga_id')
    print(manga_id)
    # Fetch the manga object from the database using the manga ID
    manga = Manga.get_manga_from_database_by_id(manga_id)  # You should implement this method in your Manga class

    if manga:
        # Call the function to fetch chapters again
        manga = scrape_manga_chapters(manga)

        # Convert manga object to JSON and return as response
        manga_dict = {
            'manga_id': manga.manga_id,
            'title': manga.title,
            'description': manga.description,
            'image_url': manga.image_url,
            'chapters': [chapter.serialize() for chapter in manga.chapters]  # Serialize each chapter
        }

        # Return the manga dictionary as a JSON response
        return jsonify(manga_dict)

    return jsonify({'error': 'Manga not found'}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)