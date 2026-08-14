import os
import requests
from bs4 import BeautifulSoup

WP_BASE_URL = os.getenv("WP_BASE_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# Dictionary mapping your WordPress Post ID to the scraping source
# (You can add all your games here!)
GAMES_CONFIG = [
    {
        "post_id": 123,  # Replace with the exact Post ID of your Reaper 2 post
        "source_url": "https://example-reliable-source.com/reaper-2-codes",
        "game_name": "Reaper 2"
    }
]

def scrape_active_codes(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Custom selector based on your source structure
    # Example: finding list items or table rows containing codes
    extracted_codes = []
    
    # Example parsing logic: customize based on your target source's HTML
    for item in soup.select("ul li strong, table tr td:first-child"):
        code_text = item.get_text(strip=True)
        if len(code_text) >= 3 and not "expired" in code_text.lower():
            extracted_codes.append(code_text)
            
    return list(set(extracted_codes))

def update_wordpress_post(post_id, new_codes, game_name):
    # Format the extracted codes into GoGachaGame's styled HTML table/list
    code_rows = "".join([
        f'<tr><td class="p-3 font-mono font-bold text-[#0284C7] dark:text-[#00F0FF]">{c}</td><td class="p-3 text-emerald-500 font-bold">Working</td></tr>'
        for c in new_codes
    ])
    
    table_html = f"""
    <div class="overflow-x-auto my-6">
        <table class="w-full text-left text-sm border-collapse rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800">
            <thead class="bg-slate-100 dark:bg-[#161F30] text-[#0F172A] dark:text-white font-bold">
                <tr><th class="p-3">Active Code</th><th class="p-3">Status</th></tr>
            </thead>
            <tbody>{code_rows}</tbody>
        </table>
    </div>
    """

    # Fetch existing post content
    api_url = f"{WP_BASE_URL}/wp-json/wp/v2/posts/{post_id}"
    res = requests.get(api_url, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code != 200:
        print(f"Error fetching post {post_id}: {res.text}")
        return

    post_data = res.json()
    current_content = post_data.get("content", {}).get("rendered", "")

    # Update payload
    update_payload = {
        # You can replace specific sections or update post metadata
        "content": current_content,  # Swap out code block with table_html
        "status": "publish"
    }

    update_res = requests.post(api_url, json=update_payload, auth=(WP_USER, WP_APP_PASSWORD))
    if update_res.status_code == 200:
        print(f"✅ Successfully updated {game_name} (Post ID: {post_id})")
    else:
        print(f"❌ Failed to update {game_name}: {update_res.text}")

def main():
    for game in GAMES_CONFIG:
        print(f"Scraping codes for {game['game_name']}...")
        codes = scrape_active_codes(game["source_url"])
        if codes:
            update_wordpress_post(game["post_id"], codes, game["game_name"])

if __name__ == "__main__":
    main()
