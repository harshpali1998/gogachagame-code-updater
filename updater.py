import os
import re
import requests
from bs4 import BeautifulSoup

# Read credentials securely from GitHub Secrets
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://gogachagame.com").rstrip("/")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# =====================================================================
# 🎮 CONFIGURATION: Add your games, Post IDs, and scraping URLs below
# =====================================================================
GAMES_CONFIG = [
    {
        "game_name": "Reaper 2",
        "post_id": 142,  # 👈 REPLACE with your WordPress Post ID
        "source_url": "https://example-source.com/reaper-2-codes",  # 👈 REPLACE with source URL
        "selector": "ul li strong, table tbody tr td:first-child"   # Element selector
    }
]

def scrape_codes(source_url, selector):
    """Fetches and extracts working codes from the target source."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(source_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Failed to reach {source_url} (Status: {response.status_code})")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        codes = []

        elements = soup.select(selector)
        for el in elements:
            code_text = el.get_text(strip=True)
            # Filter out expired keywords, empty items, or tiny words
            if code_text and len(code_text) >= 3 and "expired" not in code_text.lower():
                # Clean up any trailing colons or punctuation
                cleaned = re.sub(r"[:\-–—].*", "", code_text).strip()
                if cleaned:
                    codes.append(cleaned)

        # Remove duplicates while preserving original order
        unique_codes = list(dict.fromkeys(codes))
        print(f"✅ Found {len(unique_codes)} active codes from {source_url}")
        return unique_codes

    except Exception as e:
        print(f"❌ Scraping error for {source_url}: {e}")
        return []

def generate_bullet_list_html(codes):
    """Builds a clean bulleted list matching GoGachaGame's post style."""
    if not codes:
        return '<!-- CODES_START -->\n<p><em>No active codes currently available. Check back soon!</em></p>\n<!-- CODES_END -->'

    list_items = ""
    for code in codes:
        list_items += f'    <li class="my-1.5"><strong class="font-mono text-[#0284C7] dark:text-[#00F0FF] font-bold text-sm tracking-wide">{code}</strong> – <span class="text-emerald-600 dark:text-emerald-400 font-semibold text-xs uppercase font-mono">Working</span></li>\n'

    list_html = f"""<!-- CODES_START -->
<ul class="list-disc pl-6 space-y-2 my-4">
{list_items}</ul>
<!-- CODES_END -->"""
    return list_html

def update_wordpress_post(post_id, new_list_html, game_name):
    """Replaces only the bulleted list between markers and updates WordPress."""
    api_url = f"{WP_BASE_URL}/wp-json/wp/v2/posts/{post_id}"
    auth = (WP_USER, WP_APP_PASSWORD)

    # 1. Fetch existing post content from WordPress
    res = requests.get(api_url, auth=auth)
    if res.status_code != 200:
        print(f"❌ Error fetching WordPress post ID {post_id}: {res.status_code} - {res.text}")
        return

    post_data = res.json()
    current_content = post_data.get("content", {}).get("raw", "")
    if not current_content:
        current_content = post_data.get("content", {}).get("rendered", "")

    # 2. Replace content between <!-- CODES_START --> and <!-- CODES_END -->
    pattern = r"<!-- CODES_START -->.*?<!-- CODES_END -->"
    if re.search(pattern, current_content, flags=re.DOTALL):
        updated_content = re.sub(pattern, new_list_html, current_content, flags=re.DOTALL)
    else:
        print(f"⚠️ Markers not found in post {post_id}. Appending bullet list above content.")
        updated_content = new_list_html + "\n\n" + current_content

    # 3. Save updated content back to WordPress
    payload = {
        "content": updated_content
    }
    update_res = requests.post(api_url, json=payload, auth=auth)
    if update_res.status_code == 200:
        print(f"🎉 Successfully updated '{game_name}' with new bullet points on GoGachaGame!")
    else:
        print(f"❌ Failed to update post {post_id}: {update_res.status_code} - {update_res.text}")

def main():
    if not WP_USER or not WP_APP_PASSWORD:
        print("❌ Missing WP_USER or WP_APP_PASSWORD environment variables.")
        return

    print("🚀 Running GoGachaGame bullet-list auto-updater...")
    for game in GAMES_CONFIG:
        print(f"\n--- Scraping: {game['game_name']} (Post ID: {game['post_id']}) ---")
        codes = scrape_codes(game["source_url"], game["selector"])
        if codes:
            new_list_html = generate_bullet_list_html(codes)
            update_wordpress_post(game["post_id"], new_list_html, game["game_name"])
        else:
            print(f"⚠️ No codes found for {game['game_name']}. Skipping post update.")

if __name__ == "__main__":
    main()
