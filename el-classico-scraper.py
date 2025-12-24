import pycurl
from io import BytesIO
from bs4 import BeautifulSoup
import re
import json
import sys
from datetime import datetime

url_jedilnik = "https://el-clasico.si/jedilnik-1/"
slack_webhook_url = sys.argv[1]  # Incoming Webhook URL

buffer_get = BytesIO()
c_get = pycurl.Curl()

c_get.setopt(c_get.URL, url_jedilnik)
c_get.setopt(c_get.WRITEDATA, buffer_get)
c_get.setopt(c_get.USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
c_get.setopt(c_get.FOLLOWLOCATION, True)
c_get.setopt(c_get.TIMEOUT, 60)

try:
    c_get.perform()
    status = c_get.getinfo(c_get.RESPONSE_CODE)
    c_get.close()

    if status != 200:
        print(f"GET napaka: HTTP {status}")
        sys.exit(1)

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
                    continue

    # Sortiraj po ceni naraščajoče
    def get_price(item):
        match = price_regex.search(item)
        if match:
            ps = match.group(1).replace(" ", "").replace(",", ".")
            try:
                return float(ps)
            except:
                return 0
        return 0

    food_items.sort(key=get_price)
    food_items_over_10.sort(key=get_price)

    # Priprava podatkov za tabelo: ločimo jed in ceno
    def loci_jed_cena(item):
        if " €" in item:
            deli = item.rsplit(" €", 1)
            jed = deli[0].strip()
            cena = deli[1].strip() + " €"
        elif "€" in item:
            deli = item.rsplit("€", 1)
            jed = deli[0].strip()
            cena = deli[1].strip() + "€" if deli[1].strip() else ""
            cena = cena.strip() + " €" if cena else ""
        else:
            jed = item.strip()
            cena = ""
        return jed, cena

    # Pretvorba v format za Block Kit tabelo
    def naredi_table_rows(items):
        rows = []
        for item in items:
            jed, cena = loci_jed_cena(item)
            rows.append([
                {"type": "plain_text", "text": jed},
                {"type": "plain_text", "text": cena or "-"}
            ])
        return rows

    rows_do_10 = naredi_table_rows(food_items)
    rows_nad_10 = naredi_table_rows(food_items_over_10)

    # Datum
    dnevi_sl = {0: "PONEDELJEK", 1: "TOREK", 2: "SREDA", 3: "ČETRTEK", 4: "PETEK", 5: "SOBOTA", 6: "NEDELJA"}
    zdaj = datetime.now()
    ime_dneva = dnevi_sl[zdaj.weekday()]
    dan_mesec_leto = zdaj.strftime("%d.%m.%Y")
    datum_naslov = f"{ime_dneva}, {dan_mesec_leto}"

    # Block Kit struktura
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🍽️ Dnevni jedilnik El Clasico – {datum_naslov}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Jedi do 10 €:*"
            }
        }
    ]

    if rows_do_10:
        blocks.append({
            "type": "table",
            "columns": [
                {"title": {"type": "plain_text", "text": "Jed"}},
                {"title": {"type": "plain_text", "text": "Cena"}}
            ],
            "rows": [
                {
                    "type": "table_row",
                    "cells": [
                        {"type": "plain_text", "text": row[0]["text"]},
                        {"type": "plain_text", "text": row[1]["text"]}
                    ]
                } for row in rows_do_10
            ]
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "_Ni jedi do 10 €._"}
        })

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Jedi nad 10 €:*"
        }
    })

    if rows_nad_10:
        blocks.append({
            "type": "table",
            "columns": [
                {"title": {"type": "plain_text", "text": "Jed"}},
                {"title": {"type": "plain_text", "text": "Cena"}}
            ],
            "rows": [
                {
                    "type": "table_row",
                    "cells": [
                        {"type": "plain_text", "text": row[0]["text"]},
                        {"type": "plain_text", "text": row[1]["text"]}
                    ]
                } for row in rows_nad_10
            ]
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "_Ni jedi nad 10 €._"}
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🍲 Juha ali sladica: *2,50 €*  😋  Dober tek!"
            }
        ]
    })

    # Pošlji preko Incoming Webhook (podpira blocks!)
    payload = json.dumps({
        "channel": "#el-classico-scraper",
        "blocks": blocks,
        "text": f"Dnevni jedilnik El Clasico za {datum_naslov}"  # fallback
    }).encode('utf-8')

    buffer_post = BytesIO()
    c_post = pycurl.Curl()

    c_post.setopt(c_post.URL, slack_webhook_url)
    c_post.setopt(c_post.POST, 1)
    c_post.setopt(c_post.POSTFIELDS, payload)
    c_post.setopt(c_post.HTTPHEADER, ["Content-Type: application/json"])
    c_post.setopt(c_post.WRITEDATA, buffer_post)
    c_post.setopt(c_post.TIMEOUT, 30)

    try:
        c_post.perform()
        post_status = c_post.getinfo(c_post.RESPONSE_CODE)
        response_body = buffer_post.getvalue().decode('utf-8', errors='ignore')

        print(f"Slack odgovor: HTTP {post_status}")
        print(f"Odgovor: {response_body}")

        if post_status == 200:
            print("✅ Jedilnik uspešno poslan na Slack z lepimi tabelami!")
        else:
            print("❌ Napaka pri pošiljanju na Slack.")

    except pycurl.error as e:
        print(f"Pycurl POST napaka: {e}")
    finally:
        c_post.close()

except Exception as e:
    print(f"Splošna napaka: {e}")