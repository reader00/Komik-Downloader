import grequests
import requests
from bs4 import BeautifulSoup
import os
from PIL import Image
import sys

start = 1
limit = 2
skips = []

if len(sys.argv) > 1:
    start = int(sys.argv[1])
if len(sys.argv) > 2:
    limit = int(sys.argv[2])
if len(sys.argv) > 3:
    skips = sys.argv[3].split(",")

url = 'https://komikcast.net/weak-hero-chapter-01'
if start != 1:
    page = requests.get("https://komikcast.net/komik/598427-weak-hero/")
    soup = BeautifulSoup(page.content, 'html.parser')
    chapter_list = soup.select("#chapter_list li")
    url = chapter_list[-start-1].select('.dt>a')[0]['href']
    print(url)

for i in range(start-1, limit):
    print(url)

    folder_number = f"{i+1:03}"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    images = soup.select("#chimg img")
    next_url = soup.select(".nextprev a")
    url = next_url[-1]['href']

    print("Next :", url)

    if i+1 in skips:
        continue

    root_dir = os.path.join("C:\\", "Users", "qorya",
                            "Documents", "Komik", "weak_hero")
    dir = os.path.join(root_dir, folder_number)
    if not os.path.exists(dir):
        os.mkdir(dir)
    print(dir)

    isFirst = True
    first_cimage = 0
    cimage_list = []

    for x, image in enumerate(images):
        img_url = image['src']
        response = grequests.get(img_url)

    img_requests = (grequests.get(image['src']) for image in images)
    responses = grequests.map(img_requests)
    image_responses = [res.content for res in responses]

    for x, image in enumerate(image_responses):
        path = dir + "\\" + f"{x+1:03}" + '.jpg'
        if os.path.exists(path):
            print("File" + path + " exist.....")
        else:
            print(path)
            with open(path, "wb") as f:
                f.write(image)
        io = Image.open(path)
        ie = io.convert('RGB')
        if isFirst:
            first_cimage = ie
            isFirst = False
        else:
            cimage_list.append(ie)

    pdf_path = root_dir + "\\" + f"{i+1:03}" + ".pdf"
    if os.path.exists(pdf_path):
        print("File " + path + " exist.....")
        continue

    first_cimage.save(pdf_path, save_all=True, append_images=cimage_list)
    del first_cimage
    del cimage_list
    print(pdf_path)

    if "Chapter Selanjutnya" not in next_url[-1].text:
        print("Last chapter")
        break
