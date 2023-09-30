import csv #csv file handling
import random #randomizing post selection
import time #time stuff
from datetime import datetime, timedelta #time stuff
from mastodon import Mastodon #mastodon post gen
import os # dot environment variables
import json #json file handling
from dotenv import load_dotenv #dot environment variables
import calendar #displaying month as name
import tkinter as tk #UI
from tkinter import messagebox, simpledialog, ttk #UI
import threading #UI
import pytz  #timezone handling

load_dotenv()

# Retrieve environment variables
instance_url = os.getenv("instance_url")
access_token = os.getenv("access_token")

# default timezone -> when changed also change in the UI Window settings
default_timezone = pytz.timezone('US/Eastern')

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

# get video data from csv file
def display_video_info(video_data):
    title = video_data['title']
    channel = video_data['channel']
    numeric_month = int(video_data['month'])
    month_name = convert_numeric_month_to_name(numeric_month)
    year = video_data['year']
    alternatelink = video_data['alternate link']
    message = f'The randomly selected top pony video of the day is: "{title}" from "{channel}" from {month_name} {year}:\n{alternatelink}'
    return message

# save entries to json file
def save_post_data_to_json(post_data):
    existing_data = []
    if os.path.exists('posts.json'):
        with open('posts.json', 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)
    
    # Check if there is an existing entry with the same date and timezone
    for entry in existing_data:
        if 'timestamp_date' in entry and 'timezone' in entry and entry['timestamp_date'] == post_data['timestamp_date'] and entry['timezone'] == post_data['timezone']:
            # Update the timestamp_utc and message for the existing entry
            entry['timestamp_utc'] = post_data['timestamp_utc']
            entry['message'] = post_data['message']
            break
    else:
        existing_data.append(post_data)

    with open('posts.json', 'w', encoding='utf-8') as json_file:
        json.dump(existing_data, json_file, ensure_ascii=False, indent=4)

# Function to schedule a mastodon post (its actually public)
def schedule_private_mastodon_post(instance_url, access_token, message, scheduled_time_utc):
    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=instance_url
    )

    scheduled_time = datetime.utcfromtimestamp(scheduled_time_utc).replace(tzinfo=pytz.utc)
    response = mastodon.status_post(message, scheduled_at=scheduled_time, visibility='public')
    print(scheduled_time, message)

    post_data = {
        'timestamp_utc': scheduled_time_utc,
        'timestamp_date': scheduled_time.strftime("%Y-%m-%d"),
        'timezone': timezone_combo.get(),
        'message': message,
        'post_id': response['id']
    }
    save_post_data_to_json(post_data)

def bulk_post_to_mastodon(instance_url, access_token, num_posts, selected_timezone, scheduled_time):
    global latest_scheduled_time

    for i in range(num_posts):
        csv_file = 'Top_10_Pony_Videos.csv'  # replace this maybe idk
        random_video = select_random_video(csv_file)

        if random_video:
            message = display_video_info(random_video)

            if latest_scheduled_time:
                latest_scheduled_datetime = datetime.fromtimestamp(latest_scheduled_time, tz=selected_timezone)
                scheduled_datetime = latest_scheduled_datetime.replace(hour=scheduled_time[0] + 2, minute=scheduled_time[1], second=0, microsecond=0) + timedelta(days=1)
            else:
                current_time = datetime.now()
                ny_time = current_time.astimezone(selected_timezone)
                scheduled_datetime = ny_time.replace(hour=scheduled_time[0] + 2, minute=scheduled_time[1], second=0, microsecond=0) + timedelta(days=1)

            scheduled_time_utc = int(scheduled_datetime.timestamp())

            schedule_private_mastodon_post(instance_url, access_token, message, scheduled_time_utc)
            print(f'Post {i + 1} scheduled on Mastodon for {scheduled_datetime}.')
            latest_scheduled_time = scheduled_time_utc
        else:
            print('No eligible videos found in the CSV file.')

        time.sleep(1)


# Tkinter UI functions
def generate_posts():
    num_posts = int(posts_entry.get())
    selected_timezone = pytz.timezone(timezone_combo.get())
    scheduled_time_str = scheduled_time_entry.get()
    scheduled_time = [int(x) for x in scheduled_time_str.split(":")]

    if num_posts < 1 or num_posts > max_posts:
        messagebox.showerror("Error", "Invalid number of posts. Please enter a valid number between 1 and 300.")
    else:
        generate_button["state"] = "disabled"

        def run_generate_posts():
            bulk_post_to_mastodon(instance_url, access_token, num_posts, selected_timezone, scheduled_time)
            generate_button["state"] = "normal"

        generation_thread = threading.Thread(target=run_generate_posts)
        generation_thread.start()

# UI Window
root = tk.Tk()
root.title("Mastodon Post Generator")

scheduled_time = None

posts_label = tk.Label(root, text="Enter the number of posts to generate (1-300):")
posts_label.pack(pady=10)
posts_entry = tk.Entry(root)
posts_entry.pack()

scheduled_time_label = tk.Label(root, text="Enter scheduled time (hh:mm):")
scheduled_time_label.pack(pady=10)
scheduled_time_entry = tk.Entry(root)
scheduled_time_entry.pack()

timezone_label = tk.Label(root, text="Select timezone:")
timezone_label.pack(pady=10)
timezone_combo = ttk.Combobox(root, values=pytz.all_timezones)
timezone_combo.set('US/Eastern')  # Set a default timezone
timezone_combo.pack()

generate_button = tk.Button(root, text="Generate Posts", command=generate_posts)
generate_button.pack(pady=10)

# Set the maximum number of posts
max_posts = 300

root.mainloop()
