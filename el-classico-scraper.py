import requests
from bs4 import BeautifulSoup

url = "https://el-clasico.si/jedilnik-1/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    
    content = soup.find("pre")
    if content:
        menu_text = content.get_text(strip=True)
    else:
        menu_text = soup.get_text(strip=True)
    
    print(menu_text) 
    
    with open("el_clasico_menu.txt", "w", encoding="utf-8") as f:
        f.write(menu_text)
    
    print("Menu saved to el_clasico_menu.txt")
else:
    print("Error:", response.status_code)