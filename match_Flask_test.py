from flask import Flask, jsonify, redirect
from bs4 import BeautifulSoup
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_live_scores():
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        logger.info("Fetching live scores from Cricbuzz")
        page = 'https://www.cricbuzz.com/cricket-match/live-scores'
        driver.get(page)

        # Wait for dynamic content to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cb-mtch-lst"))
        )
        time.sleep(2)  # Additional buffer

        response = driver.page_source
        soup = BeautifulSoup(response, 'html.parser')
        listing_tag = soup.find_all('div', class_="cb-mtch-lst")

        logger.info(f"Found {len(listing_tag)} match listings")

        matches = []
        for data in listing_tag:
            # Match time/status
            match_stat_time = data.find('div', class_="text-gray")
            match_stat_time = match_stat_time.text.strip() if match_stat_time else ''

            # Team names
            team_names = data.find_all('div', class_="cb-ovr-flo")
            first_team_name = team_names[0].text.strip() if len(team_names) > 0 else ''
            second_team_name = team_names[1].text.strip() if len(team_names) > 1 else ''

            # Scores
            scores = data.find_all('div', {'style': 'display:inline-block; width:140px'})
            first_team_score = scores[0].text.strip() if len(scores) > 0 else ''
            second_team_score = scores[1].text.strip() if len(scores) > 1 else ''

            # Match URL
            match_link = data.find('a')
            live_match_url = "https://www.cricbuzz.com" + match_link['href'] if match_link else ''

            # Match status
            match_day = data.find('div', class_="cb-text-live")
            match_day = match_day.text.strip() if match_day else ''

            matches.append({
                'match_time': match_stat_time,
                'team_1': first_team_name,
                'team_2': second_team_name,
                'team_1_score': first_team_score,
                'team_2_score': second_team_score,
                'match_status': match_day,
                'match_url': live_match_url
            })

        return matches
    except Exception as e:
        logger.error(f"Error fetching live scores: {str(e)}")
        return []
    finally:
        driver.quit()


@app.route('/')
def home():
    return redirect('/live-scores')


@app.route('/favicon.ico')
def favicon():
    return '', 404


@app.route('/live-scores', methods=['GET'])
def live_scores():
    try:
        matches = get_live_scores()
        return jsonify({
            'status': 'success',
            'count': len(matches),
            'matches': matches
        })
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)