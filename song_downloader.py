import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import re
from mutagen.easyid3 import EasyID3
import sys
from concurrent.futures import ThreadPoolExecutor

chromedriver_autoinstaller.install()

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def scrape_info(driver, first_result):
    try:
        album = first_result.find_element(By.CLASS_NAME, 'album').text
    except:
        album = "Unknown Album"
    return album

def search_and_download(artist, song):
    driver = webdriver.Chrome()
    query = f"{artist} - {song}"
    driver.get("https://w15.mp3-juices.nu/")
    
    search_box = driver.find_element(By.NAME, 'query')
    search_box.send_keys(query)
    search_box.submit()
    time.sleep(1)
    search_box.submit()
    time.sleep(2)

    try:
        first_result = driver.find_element(By.CLASS_NAME, 'result')
        mp3_download_button = first_result.find_element(By.LINK_TEXT, 'MP3 Download')
        mp3_download_button.click()
        
        download_button = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Download"))
        )
        download_link = download_button.get_attribute('href')
        
        album = scrape_info(driver, first_result)
        
        response = requests.get(download_link)
        filename = safe_filename(f"{song}.mp3")
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Download complete: {filename}")

        audio = EasyID3(filename)
        audio['title'] = song
        audio['album'] = album
        audio['artist'] = artist
        audio.save()
        print(f"Metadata added: {filename}")
    except Exception as e:
        print(f"No results found or an error occurred for {query}: {str(e)}")
    finally:
        driver.quit()

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    tasks = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for line in lines:
            line = line.strip()
            if line:  # Only process non-empty lines
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    artist, song = parts
                    print(f"Processing: {artist} - {song}")
                    tasks.append(executor.submit(search_and_download, artist, song))
        for task in tasks:
            task.result()  # Wait for all tasks to complete

def main():
    file_path = sys.argv[1]
    print(f'read {file_path}')
    process_file(file_path)

if __name__ == '__main__':
    main()
