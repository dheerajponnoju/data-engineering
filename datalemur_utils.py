import json
import re
from bs4 import BeautifulSoup
from IPython.display import IFrame
import markdown
import requests


def extract_iframe_from_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    try:
        # 1. Fetch data directly over the network
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    
        soup = BeautifulSoup(response.text, "html.parser")
        next_data_script = soup.find("script", id="__NEXT_DATA__")
    
        raw_markdown = ""
    
        # 2. Parse the dynamic database tree state correctly
        if next_data_script:
            page_json = json.loads(next_data_script.string)
    
            # Access the Next.js React Query cache array directly
            queries_list = (
                page_json.get("props", {})
                .get("pageProps", {})
                .get("dehydratedState", {})
                .get("queries", [])
            )
    
            # Loop over cache entries to locate the specific interview question block
            for entry in queries_list:
                data_block = entry.get("state", {}).get("data", {})
                if isinstance(data_block, dict) and "description" in data_block:
                    raw_markdown = data_block.get("description", "")
                    break
    
        # 3. Fallback regex approach if the internal dictionary shifts structures again
        if not raw_markdown:
            match = re.search(
                r'"description"\s*:\s*"([^"]+)"', response.text, re.IGNORECASE
            )
            if match:
                # Decode encoded escape characters (\n, \t) back to normal text
                raw_markdown = match.group(1).encode().decode("unicode_escape")
    
        if not raw_markdown:
            raise ValueError("Could not find the question data layer.")
    
        # 4. Clean the raw string blocks (removes potential string escaping artifacts)
        raw_markdown = raw_markdown.replace("\\n", "\n").replace('\\"', '"')
    
        # 5. Convert markdown elements to native HTML tables
        formatted_html_body = markdown.markdown(raw_markdown, extensions=["tables"])
    
        # 6. Apply pristine layout styles matching the original platform
        complete_styled_page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    color: #2d3748;
                    line-height: 1.6;
                    padding: 24px;
                    background-color: #ffffff;
                    max-width: 850px;
                    margin: 0 auto;
                }}
                h1, h2, h3, h4 {{
                    color: #1a202c;
                    font-weight: 700;
                    margin-top: 24px;
                    margin-bottom: 12px;
                }}
                h2 {{ border-bottom: 2px solid #edf2f7; padding-bottom: 8px; color: #2b6cb0; }}
                p {{ margin-bottom: 16px; font-size: 16px; }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                    border-radius: 4px;
                    overflow: hidden;
                }}
                th, td {{
                    border: 1px solid #e2e8f0;
                    padding: 12px 16px;
                    text-align: left;
                }}
                th {{
                    background-color: #f7fafc;
                    font-weight: 600;
                    color: #4a5568;
                    text-transform: uppercase;
                    font-size: 13px;
                    letter-spacing: 0.5px;
                }}
                tr:nth-child(even) {{ background-color: #f8fafc; }}
                code {{
                    background-color: #edf2f7;
                    color: #c53030;
                    padding: 3px 6px;
                    border-radius: 4px;
                    font-family: "SFMono-Regular", Menlo, Monaco, Consolas, monospace;
                    font-size: 14px;
                }}
                strong {{ color: #1a202c; }}
            </style>
        </head>
        <body>
            {formatted_html_body}
        </body>
        </html>
        """
    
        # 7. Write cleanly down to file cache to satisfy the positional argument
        question = url.split("/")[-1]
        output_filename = f"{question}.html"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(complete_styled_page)
    
        # 8. Mount seamlessly inside your Jupyter workspace
        display(IFrame(src=output_filename, width="100%", height="550px"))
    
    except Exception as e:
        print(f"Failed to generate layout target: {e}")