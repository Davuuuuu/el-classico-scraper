import json
import sys
from bs4 import BeautifulSoup
import re 
import pycurl
from io import BytesIO


buffer = BytesIO()
c = pycurl.Curl()
c.setopt(c.URL, "https://el-clasico.si/jedilnik-1/")
c.setopt(c.WRITEDATA, buffer)
c.perform()
c.close()

body = buffer.getvalue()
print(body.decode('utf-8'))

url = "https://el-clasico.si/jedilnik-1/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

c.setopt(c.URL, url)
c.setopt(c.WRITEDATA, buffer)
c.setopt(c.USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
c.setopt(c.FOLLOWLOCATION, True)
c.setopt(c.TIMEOUT, 30)

try:
    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    c.close()
    
    soup = BeautifulSoup(body, "html.parser")
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
      

    message = (
        "*Danes v El Clasicu (23.12.2025)* 🍽️\n\n"
        "*Do 10 €:*\n" + "\n".join([f"• {item}" for item in food_items]) + "\n\n"
        "*Nad 10 €:*\n" + "\n".join([f"• {item}" for item in food_items_over_10]) + "\n\n"
        "Juha ali sladica: 2,50 €\n"
        "Lep dan in dober tek! 😋"
    )

    payload = json.dumps({
        "text": message
    }).encode('utf-8')

    buffer_post = BytesIO()
    c_post = pycurl.Curl()
    c_post.setopt(c_post.URL, sys.argv[1])  
    c_post.setopt(c_post.POSTFIELDS, payload)
    c_post.setopt(c_post.HTTPHEADER, [
        "Content-Type: application/json",
        f"Content-Length: {len(payload)}"
    ])
    c_post.setopt(c_post.WRITEDATA, buffer_post)
    c_post.setopt(c_post.USERAGENT, "Mozilla/5.0 (compatible; Python pycurl)")
    c_post.setopt(c_post.TIMEOUT, 30)

    c_post.perform()
    post_status = c_post.getinfo(c_post.RESPONSE_CODE)
    c_post.close()

    print(f"SLACK_WEBHOOK_URL: {sys.argv[1]}")
    


except Exception as e:
    print(f"Error: {e}")