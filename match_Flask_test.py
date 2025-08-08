from flask import Flask, jsonify, redirect
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return redirect('/live-scores')

@app.route('/live-scores', methods=['GET'])
def get_live_scores():
    try:
        url = "https://www.cricbuzz.com/cricket-match/live-scores"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        matches = []
        
        match_containers = soup.find_all('div', class_="cb-mtch-lst cb-col cb-col-100 cb-tms-itm")
        
        if not match_containers:
            match_containers = soup.find_all('div', class_="cb-col cb-col-100 cb-tms-itm")
        
        for match in match_containers:
            try:
                match_status = match.find('div', class_="cb-text-live").text
            except:
                match_status = ''
            team_names = match.find_all('div', class_="cb-ovr-flo cb-hmscg-tm-nm")
            team_1 = team_names[0].text.strip() if len(team_names) > 0 else 'TBD'
            team_2 = team_names[1].text.strip() if len(team_names) > 1 else 'TBD'
            
            score_divs = match.find_all('div', {'style': 'display:inline-block; width:140px'})
            team_1_score = score_divs[0].text.strip() if len(score_divs) > 0 else ''
            team_2_score = score_divs[1].text.strip() if len(score_divs) > 1 else ''
            
            time_div = match.find('div', class_="text-gray")
            if not time_div:
                time_div = match.find('div', class_="cb-font-12 text-gray")
            match_time = time_div.text.strip() if time_div else 'Time not available'
            
            link = match.find('a')
            if not link:
                link = match.find('a', class_="text-hvr-underline")
            match_url = "https://www.cricbuzz.com" + link['href'] if link and 'href' in link.attrs else ''
            
            matches.append({
                "match_time": match_time,
                "match_url": match_url,
                "team_1": team_1,
                "team_1_score": team_1_score,
                "team_2": team_2,
                "team_2_score": team_2_score,
                "match_status": match_status,
            })
        
        return jsonify({
            "count": len(matches),
            "matches": matches,
            "status": "success"
        })
        
    except requests.RequestException as e:
        return jsonify({
            "error": f"Network error: {str(e)}",
            "status": "error"
        }), 500
        
    except Exception as e:
        return jsonify({
            "error": f"Processing error: {str(e)}",
            "status": "error"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


