import sys
import requests
from bs4 import BeautifulSoup
import re 

url = "https://el-clasico.si/jedilnik-1/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    lines = [line.strip() for line in soup.get_text(separator="").split("\n") if line.strip()]
    food_items_over_10 = []
    food_items = []
    for line in lines:
        if "€" in line:
            cleaned_line = line.replace(":", "").strip()
            price_match = re.search(r"([\d,]+ ?\d*) ?€", line)
            if price_match:
                price_str = price_match.group(1).replace(" ", "").replace(",", ".")
                price = float(price_str)
                if price <= 10.00:  
                    cleaned_line = line.replace(":", "").strip()
                    food_items.append(cleaned_line)
                elif price > 10.00:
                    food_items_over_10.append(cleaned_line)
    
    def cena(item):
        price_match = re.search(r"([\d,]+ ?\d*) ?€", item)
        if price_match:
            price_str = price_match.group(1).replace(" ", "").replace(",", ".")
            return float(price_str)
        return 0
    
    food_items.sort(key=cena)
    food_items_over_10.sort(key=cena)
    



    print("\n".join(food_items))
    print()
    print()
    print("\n".join(food_items_over_10))
    with open("food_items", "w", encoding="utf-8") as f:
        f.write("\n".join(food_items))
    with open("el_clasico_food_items_over_10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(food_items_over_10))
    print("\n\nSaved to food_items.txt")
    print("\n\nSaved to el_clasico_food_items_over_10.txt")
      

    payload = {
     "channel": "CHANNEL_ID",
     "text": "test message"
    }

    headers = {
      'Content-Type': 'application/json'
    }


    response = requests.post(
      url="https://webhook.site/cfb9d233-7ead-4b03-8c98-99724eafae3a",
      headers=headers,
      json=payload,
      timeout=60
    )

    print(sys.argv[1])


except Exception as e:
    print(f"Error: {e}")