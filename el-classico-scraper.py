import pycurl
from io import BytesIO
from bs4 import BeautifulSoup
import re
import json
import sys
from prettytable import PrettyTable

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

    def get_price(item):
        match = price_regex.search(item)
        if match:
            ps = match.group(1).replace(" ", "").replace(",", ".")
            try:
                return float(ps)
            except ValueError:
                return 0
        return 0

    print("\nDO 10 €:\n" + "\n".join(food_items))
    print("\nNAD 10 €:\n" + "\n".join(food_items_over_10))

    with open("food_items.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(food_items))
    with open("el_clasico_over_10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(food_items_over_10))

    
    message = (
        "*Dnevni jedilnik El Clasico*{current_date} 🍕\n\n"
        "*Do 10 €:*\n" + "\n".join([f"• {i}" for i in food_items]) + "\n\n"
        "*Nad 10 €:*\n" + "\n".join([f"• {i}" for i in food_items_over_10]) + "\n\n"
        "Juha ali sladica: 2,50 €\nDober tek! 😋"
    )

    payload = json.dumps({
        "channel": "#el-classico-scraper",
        "text": message}).encode('utf-8')

    buffer_post = BytesIO()
    c_post = pycurl.Curl()

    c_post.setopt(c_post.URL, sys.argv[1])
    c_post.setopt(c_post.POST, True)
    c_post.setopt(c_post.POSTFIELDS, payload)
    c_post.setopt(c_post.HTTPHEADER, ['Content-Type: application/json'])
    c_post.setopt(c_post.WRITEDATA, buffer_post)
    c_post.setopt(c_post.TIMEOUT, 30)

    try:
        c_post.perform()

        post_status = c_post.getinfo(pycurl.RESPONSE_CODE)
        uploaded = c_post.getinfo(pycurl.SIZE_UPLOAD)        
        downloaded = c_post.getinfo(pycurl.SIZE_DOWNLOAD)
        content_type = c_post.getinfo(pycurl.CONTENT_TYPE)
        effective_url = c_post.getinfo(pycurl.EFFECTIVE_URL)
        total_time = c_post.getinfo(pycurl.TOTAL_TIME)

        response_body = buffer_post.getvalue().decode('utf-8', errors='ignore')

        print("Slack POST debug:")
        print(f"  HTTP Status: {post_status}")
        print(f"  Poslanih bajtov: {uploaded}")
        print(f"  Prejetih bajtov: {downloaded}")
        print(f"  Content-Type: {content_type}")
        print(f"  Končni URL: {effective_url}")
        print(f"  Čas: {total_time:.2f}s")
        print(f"  Odgovor body: '{response_body}'")

        if post_status == 200 and uploaded > 100:
            print("Tehnično uspešno poslano – če sporočilo ne pride, ustvari NOV webhook in izberi PRAVI kanal!")
        else:
            print("Problem pri pošiljanju (payload ni poslan pravilno).")

    except pycurl.error as e:
        print(f"Pycurl POST napaka: {e}")
    finally:
        c_post.close()

except pycurl.error as e:
    print(f"Pycurl napaka: {e}")
except Exception as e:
    print(f"Splošna napaka: {e}")