import csv
import random
import time
from datetime import datetime, timedelta, timezone
from mastodon import Mastodon
import os
import json
from dotenv import load_dotenv
import calendar

load_dotenv()

# Retrieve environment variables
instance_url = os.getenv("instance_url")
access_token = os.getenv("access_token")

# remove entries which are in the past
def remove_past_entries():
    current_time_utc = int(datetime.utcnow().timestamp())

    if os.path.exists('posts.json'):
        with open('posts.json', 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)

        
        existing_data = [entry for entry in existing_data if entry['timestamp_utc'] >= current_time_utc]

        
        with open('posts.json', 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, ensure_ascii=False, indent=4)


remove_past_entries()

# get the last scheduled entry
def get_latest_scheduled_time():
    if os.path.exists('posts.json'):
        with open('posts.json', 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)

        existing_data.sort(key=lambda x: x['timestamp_utc'])

        if existing_data:
            return existing_data[-1]['timestamp_utc']

    return None

latest_scheduled_time = get_latest_scheduled_time()

# select random vid
def select_random_video(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        data = [entry for entry in reader if "[BLACKLIST]" not in entry['channel']]

        if not data:
            return None

        random_entry = random.choice(data)
        return random_entry
def convert_numeric_month_to_name(numeric_month):
    return calendar.month_name[numeric_month]
# get vid data from csv file
def display_video_info(video_data):
    title = video_data['title']
    channel = video_data['channel']
    month = video_data['month']
    numeric_month = int(video_data['month'])  # Convert to an integer
    month_name = convert_numeric_month_to_name(numeric_month)  # Convert numeric month to name
    year = video_data['year']
    link = video_data['link']
    
    message = f'The randomly selected top pony video of the day is: "{title}" from "{channel}" from {month_name} {year}:\n{link}'
    return message

# save entries to json file
def save_post_data_to_json(post_data):
    existing_data = []
    if os.path.exists('posts.json'):
        with open('posts.json', 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)
    existing_data.append(post_data)

    with open('posts.json', 'w', encoding='utf-8') as json_file:
        json.dump(existing_data, json_file, ensure_ascii=False, indent=4)

# Function to schedule a mastodon post (its actually puplic)
def schedule_private_mastodon_post(instance_url, access_token, message, scheduled_time_utc):
    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=instance_url
    )

    scheduled_time = datetime.utcfromtimestamp(scheduled_time_utc).replace(tzinfo=timezone.utc)
    response = mastodon.status_post(message, scheduled_at=scheduled_time, visibility='puplic') # see its puplic :PPPP
    print(scheduled_time, message)

    post_data = {
        'timestamp_utc': scheduled_time_utc,
        'message': message,
        'post_id': response['id']
    }
    save_post_data_to_json(post_data)

def bulk_post_to_mastodon(instance_url, access_token, num_posts):
    global latest_scheduled_time  

    for i in range(num_posts):
        csv_file = 'Top_10_Pony_Videos.csv'  #replace this maybe idk
        random_video = select_random_video(csv_file)

        if random_video:
            message = display_video_info(random_video)

            if latest_scheduled_time:
                latest_scheduled_datetime = datetime.fromtimestamp(latest_scheduled_time)
                scheduled_datetime = latest_scheduled_datetime + timedelta(days=1)
            else:
                # If it's the first post, schedule it for the next day at 9 AM NY time
                current_time = datetime.now()
                ny_time = current_time - timedelta(hours=4)  # Eastern Daylight Time (EDT)
                scheduled_datetime = ny_time.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)

            scheduled_time_utc = int(scheduled_datetime.timestamp())
            schedule_private_mastodon_post(instance_url, access_token, message, scheduled_time_utc)
            print(f'Post {i+1} scheduled on Mastodon for {scheduled_datetime}.')
            latest_scheduled_time = scheduled_time_utc
        else:
            print('No eligible videos found in the CSV file.')

        # Delay for one second before the next post
        time.sleep(1)

# Main function
if __name__ == '__main__':
    max_posts = 300
    num_posts = int(input(f'Enter the number of posts to generate (1-{max_posts}): '))

    if num_posts < 1 or num_posts > max_posts:
        print('Invalid number of posts. Please enter a valid number between 1 and 300.')
    else:
        bulk_post_to_mastodon(instance_url, access_token, num_posts)
