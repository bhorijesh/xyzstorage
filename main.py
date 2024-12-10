from bs4 import BeautifulSoup
import requests
import pandas as pd
import datetime
import time
from base.log_config import logger

# API URL and initial parameters
url = "https://dashboard.n49.com/native/filterReviews/null/jhs0krj2kdzgwej4s"
querystring = {"mode": "multi"}
payload = {}

# Headers (ensure these match your session details)
headers = {
    "cookie": "XSRF-TOKEN=eyJpdiI6Ik1oRHpXTFVCM1NocW1xS2F0SFB6WHc9PSIsInZhbHVlIjoi...",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOj...",
    "Referer": "https://www.xyzstorage.com/",
}

# Initialize variables
all_reviews = []

# Function to format UNIX timestamp to readable date
def format_date(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "N/A"

# Function to clean content by extracting text from HTML
# def clean_html(content):
#     return BeautifulSoup(content, "html.parser").get_text() if content else "N/A"

# Start timing the process
start_time = time.time()

# Fetch reviews loop
while True:
    try:
        # Make the request
        response = requests.post(url, json=payload, headers=headers, params=querystring)
        
        if response.status_code == 200:
            reviews_data = response.json()
            
            # Process each review
            for review in reviews_data.get("reviews", []):
                content = review.get("content") 
                # cleaned_content = clean_html(content)  # Clean HTML from content

                # Ensure dateCreated is extracted correctly
                date_created = review.get("dateCreated", None)
                created_date = format_date(date_created) if date_created else "N/A"

                # Extract the name properly (handle fullName or firstName)
                name = review.get('user', {}).get('fullName') or review.get('user', {}).get('firstName', 'N/A')
                email_id = review.get("user", {}).get("email", "N/A")
                review_type = review.get("reviewType", "N/A")
                location = review.get("entityInfo", {}).get("name", "N/A")
                rating = review.get("rating")

                # Log the review (for debugging or info purposes)
                logger.info(f"Name: {name}, Rating: {rating}, Date Created: {created_date}")

                # Append to the list, ensuring all fields are correctly mapped
                all_reviews.append({
                    "Date Created": created_date,
                    "Name": name,
                    "Email ID": email_id,
                    "Review Type": review_type,
                    "Location": location,
                    "Rating": rating,
                    "Content":content,
                })

            # Handle pagination (if there are more reviews to fetch)
            if "LastEvaluatedKey" in reviews_data and reviews_data["LastEvaluatedKey"]:
                payload["LastEvaluatedKey"] = reviews_data["LastEvaluatedKey"]
            else:
                logger.info("All reviews fetched.")
                break

        else:
            logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
            break

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        break

# Stop timing and calculate duration
end_time = time.time()
total_time = end_time - start_time

# Log the total time taken
logger.info(f"Review fetching process completed in {total_time:.2f} seconds.")

# Save reviews to CSV
df = pd.DataFrame(all_reviews)
df = df.drop_duplicates(subset=["Content", "Date Created", "Name", "Email ID", "Review Type", "Location"])
df.to_csv('all_reviews_cleaned.csv', index=False)
logger.info(f"All reviews saved to 'all.csv'. Total reviews fetched: {len(df)}")
