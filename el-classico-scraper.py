import pycurl
from io import BytesIO
from bs4 import BeautifulSoup
import re
import json
import sys

url_jedilnik = "https://el-clasico.si/jedilnik-1/"
slack_webhook_url = "https://hooks.slack.com/services/TVOJ/DEJANSKI/WEBHOOK"  # ← tukaj svoj Slack URL

buffer_get = BytesIO()
c_get = pycurl.Curl()

c_get.setopt(c_get.URL, url_jedilnik)
c_get.setopt(c_get.WRITEDATA, buffer_get)
c_get.setopt(c_get.USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
c_get.setopt(c_get.FOLLOWLOCATION, True)
c_get.setopt(c_get.TIMEOUT, 60)


try:
    c_get.perform()
    status = c_get.getinfo(c_get.RESPONSE_CODE)
    c_get.close()  

    if status != 200:
        print(f"GET napaka: HTTP {status}")
        exit()

    html = buffer_get.getvalue().decode('utf-8', errors='ignore')
    print("Stran uspešno prenesena!")

    
    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text(separator="").split("\n") if line.strip()]

    food_items = []
    food_items_over_10 = []

    price_regex = re.compile(r"(\d+(?:[ ,]?\d+)*) ?€")

    for line in lines:
        if "€" in line:
            cleaned = line.strip()
            match = price_regex.search(line)
            if match:
                price_str_raw = match.group(1)
                price_str = price_str_raw.replace(" ", "").replace(",", ".")
                try:
                    price = float(price_str)
                    if price <= 10.00:
                        food_items.append(cleaned)
                    else:
                        food_items_over_10.append(cleaned)
                except ValueError:
                    print(f"Preskočena neveljavna cena v vrstici: {cleaned}")
                    continue

    food_items.sort(key=lambda x: float(re.search(r"([\d,]+ ?\d*)", x).group(1).replace(" ", "").replace(",", ".")) if re.search(r"([\d,]+ ?\d*)", x) else 0)
    food_items_over_10.sort(key=lambda x: float(re.search(r"([\d,]+ ?\d*)", x).group(1).replace(" ", "").replace(",", ".")) if re.search(r"([\d,]+ ?\d*)", x) else 0)

    print("\nDO 10 €:\n" + "\n".join(food_items))
    print("\nNAD 10 €:\n" + "\n".join(food_items_over_10))

    with open("food_items.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(food_items))
    with open("el_clasico_over_10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(food_items_over_10))

    
    message = (
        "*Dnevni jedilnik El Clasico (23.12.2025)* 🍕\n\n"
        "*Do 10 €:*\n" + "\n".join([f"• {i}" for i in food_items]) + "\n\n"
        "*Nad 10 €:*\n" + "\n".join([f"• {i}" for i in food_items_over_10]) + "\n\n"
        "Juha ali sladica: 2,50 €\nDober tek! 😋"
    )

    payload = json.dumps({"text": message}).encode('utf-8')

    buffer_post = BytesIO()
    c_post = pycurl.Curl()

    c_post.setopt(c_post.URL, sys.argv[1])
    c_post.setopt(c_post.POST, True)
    c_post.setopt(c_post.POSTFIELDS, payload)
    c_post.setopt(c_post.HTTPHEADER, ['Content-Type: application/json'])
    c_post.setopt(c_post.WRITEDATA, buffer_post)
    c_post.setopt(c_post.TIMEOUT, 30)

    c_post.perform()
    post_status = c_post.getinfo(c_post.RESPONSE_CODE)
    c_post.close()

    if post_status == 200:
        print("Sporočilo uspešno poslano na Slack!")
    else:
        print(f"Slack napaka: HTTP {post_status}")
        print(buffer_post.getvalue().decode('utf-8'))

except pycurl.error as e:
    print(f"Pycurl napaka: {e}")
except Exception as e:
    print(f"Splošna napaka: {e}")