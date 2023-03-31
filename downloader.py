import grequests
from bs4 import BeautifulSoup
import os
from PIL import Image
import json

from pypdf import PdfMerger, PdfReader, PdfWriter
from os import listdir
from os.path import isfile, join, isdir
from sys import argv
from urllib.parse import urlparse
import PyTaskbar


taskBar = PyTaskbar.Progress()
taskBar.init()
taskBar.setState('normal')
taskBar.setProgress(0)


db_name = "database.json"
loading_char = "█"
incomplete_char = "░"
debug_status = False
open_state = False
reverse_state = False
blank_page_path = "C:\\Users\\qorya\\Desktop\\r.eader\\Komik\\blank.pdf"

if len(argv) > 1:
    arg1 = argv[1]
    prefix = argv[1]
    if '-' in argv[1]:
        splited = argv[1].split("-")
        prefix = splited[0]
        argv[1] = splited[1]
        if 'd' in prefix:
            debug_status = True
        if 'o' in prefix:
            open_state = True
        if 'r' in prefix:
            reverse_state = True
    else:
        if 'd' in argv[1]:
            argv[1] = argv[1].replace('d', '', 1)
            debug_status = True

        if 'o' in argv[1]:
            argv[1] = argv[1].replace('o', '', 1)
            open_state = True

        if 'r' in argv[1]:
            argv[1] = argv[1].replace('r', '', 1)
            reverse_state = True


f = open(db_name)
config = json.load(f)['config']


def debug(obj, name=""):
    if debug_status:
        print(name)
        print(obj)
        print()


def hero():
    length = 42
    h_border = "="
    v_border = "|"
    space = " "
    text = "Comics Downloader"
    height = 7  # min: 3
    i = height - 3

    for x in range(height):
        if x == 0 or x == height-1:
            print(v_border, end="")
            print(h_border * (length-2), end="")
            print(v_border)
        elif x == height//2:
            print("|", end="")
            print(text.center(length-2), end="")
            print("|")
        else:
            print(v_border, end="")
            print(space * (length-2), end="")
            print(v_border)


def comic_list(isPrint=True, comic_index=False):
    debug(comic_index, 'comic_index')
    f = open(db_name)
    data = json.load(f)
    f.close()

    comics = data['comics']

    if isPrint:
        for i, comic in enumerate(comics):
            print(f'[{i+1}] {comic["name"]}')

    if comic_index != False:
        if comic_index.isdigit():
            index = int(comic_index) - 1
        else:
            if comic_index != "":
                comics = [
                    comic for comic in comics if comic_index.lower() in comic['name'].lower()]
            if len(comics) > 1:
                [print(f'[{x+1}] {comic["name"]}')
                 for x, comic in enumerate(comics)]
                print()
                index = int(input("Choose comic\t:")) - 1
            elif len(comics) == 0:
                print(
                    f"Comic not found. There is no comic name that contain word '{comic_index.upper()}'")
                exit(0)
            else:
                index = 0
        debug(index, 'index')
        debug(len(comics), 'length')
        if index+1 > len(comics):
            print(f"Comic not found. There is only {len(comics)} comics.")
            exit(0)
        return comics[index]
    else:
        return comics


def divider():
    length = 42
    character = "-"

    print()
    print(character * length)
    print()


def db_add(name, list_url, list_el, chapter_link_el, img_el, next_el):
    f = open(db_name)
    data = json.load(f)
    comics = data["comics"]

    folder_name = name.replace(" ", "_")

    root_dir = folder_name

    parsed_url = urlparse(list_url)
    domain = parsed_url.netloc

    comics.append({
        "name": name,
        "domain": domain,
        "list_url": list_url,
        "list_el": list_el,
        "chapter_link_el": chapter_link_el,
        "img_el": [img_el],
        "img_alt": {},
        "next_el": next_el,
        "root_dir": root_dir
    })
    data['comics'] = comics

    with open(db_name, "w") as outfile:
        json.dump(data, outfile)

    f.close()
    print()
    print((" " + name + " ADDED ").center(42, "-"))
    menu()


def db_edit(index, name, list_url, list_el, chapter_link_el, img_el, next_el):
    f = open(db_name)
    data = json.load(f)
    comics = data["comics"]

    folder_name = name.replace(" ", "_")

    parsed_url = urlparse(list_url)
    domain = parsed_url.netloc

    new_data = {
        "name": name,
        "domain": domain,
        "list_url": list_url,
        "list_el": list_el,
        "chapter_link_el": chapter_link_el,
        "img_el": img_el,
        "img_alt": comics[index]['img_alt'],
        "next_el": next_el,
        "root_dir": comics[index]['root_dir'],
    }

    comics[index] = new_data
    data['comics'] = comics

    with open(db_name, "w") as outfile:
        json.dump(data, outfile)

    f.close()
    print()
    print((" " + name + " EDITED ").center(42, "-"))
    menu()


def db_delete(index):
    f = open(db_name)
    data = json.load(f)
    comics = data['comics']

    comic_name = comics[index]["name"]
    del comics[index]
    data['comics'] = comics

    with open(db_name, "w") as outfile:
        json.dump(data, outfile)

    f.close()
    print()
    print((" " + comic_name.upper() + " DELETED ").center(42, "-"))
    menu()


def download_images(images, already_downloaded):
    img_requests = (grequests.get(image['src'])
                    for image in images[already_downloaded:])
    responses = grequests.map(img_requests)
    return responses


def downloader(comic, start, end, skips, isBackToMenu=True):
    debug(comic, "comic")
    if not isinstance(start, int):
        url = start
        start = end
    else:
        list_start = start
        if 'start_chapter' in comic:
            list_start = start - comic['start_chapter'] + 1
        page = grequests.map([grequests.get(comic["list_url"])])[0]
        soup = BeautifulSoup(page.content, 'html.parser')
        chapter_list_selector = comic["list_el"] + \
            " " + comic["chapter_link_el"]
        # chapter_list_selector = comic["chapter_link_el"]

        chapter_list = soup.select(chapter_list_selector)
        # print(chapter_list)
        chapter_list.reverse()
        debug(chapter_list, "CHAPTER LIST")
        if list_start > len(chapter_list):
            print("There is no chapter", start)
            print("Latest chapter is", len(chapter_list))
            menu(isBackToMenu)
        url = chapter_list[list_start-1]['href']

    root_dir = os.path.join(config['comics_path'], comic["root_dir"])
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

    img_dir = os.path.join(root_dir, "Images")
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)

    pdf_dir = os.path.join(root_dir, "PDF")
    if not os.path.exists(pdf_dir):
        os.mkdir(pdf_dir)

    for i in range(start-1, end):
        tb_done = i-(start-1)+1
        tb_full = end-(start-1)
        tb_prog = int(float(tb_done/tb_full)*100)
        taskBar.setProgress(tb_prog)

        if comic['domain'] not in url:
            url = comic['domain'] + url

        tb_printed = "Current URL\t: " + url
        print((" Downloading chapter " + str(i+1) + " [of " + str(end) + "] "
               ).center(len(tb_printed), "-"))
        print()
        print("Progress\t: " + str(tb_done) +
              "/" + str(tb_full) + f" ({tb_prog}%)")
        print(tb_printed)

        folder_number = f"{i+1:03}"
        page = grequests.map([grequests.get(url)])[0]
        soup = BeautifulSoup(page.content, 'html.parser')

        images = []
        for img_el in comic["img_el"]:
            images = soup.select(img_el)
            if len(images) == 0:
                continue
            break

        next_url = soup.select(comic["next_el"])
        debug(next_url, "NEXT")
        if len(next_url) == 0:
            url = ""
        else:
            url = next_url[-1]['href']

        if url == "#/next/":
            diff = start
            if 'start_chapter' in comic:
                diff = i - comic['start_chapter'] + 1
            if len(chapter_list) == diff+1:
                url = ""
            else:
                url = chapter_list[diff+1]['href']

        print("Next\t\t:", url)

        if str(i+1) in skips:
            continue

        dir = os.path.join(img_dir, folder_number)
        if not os.path.exists(dir):
            os.mkdir(dir)

        tb_printed = "Downloaded to\t: " + dir
        print(tb_printed)
        print()

        isFirst = True
        first_cimage = 0
        cimage_list = []
        image_compleated = False
        image_responses = []

        already_downloaded = 0
        for x in range(len(images)):
            path = dir + "\\" + f"{x+1:03}" + '.jpg'
            if os.path.exists(path):
                print("File " + path + " already exist.....")
                already_downloaded = already_downloaded + 1

        responses = download_images(images, already_downloaded)
        responses = [res for res in responses if res is not None]
        debug(responses, 'responses')
        image_responses = [
            res.content for res in responses if res.status_code != 404]

        if len(responses) == 0 and already_downloaded != 0:
            image_compleated = True
            image_responses = images
            already_downloaded = 0

        if not image_compleated and responses[0].status_code != 200:
            print("IMAGE CANNOT BE DOWNLOADED")
            if bool(comic['img_alt']):
                print(" SEARCHING FOR ALTERNATIVE ".center(42, "-"))
                prop = comic['img_alt']['prop']
                substr_start = comic['img_alt']['substr_start']
                substr_end = comic['img_alt']['substr_end']
                for j in range(len(images)):
                    start_idx = images[j][prop].find(substr_start)
                    end_idx = images[j][prop].find(substr_end)
                    # debug(images[j]['src'], "BEFORE:")
                    images[j]['src'] = images[j][prop][start_idx:end_idx]
                    # debug(images[j]['src'], "AFTER:")
                responses = download_images(images, already_downloaded)
                debug(responses)
            else:
                print("STATUS CODE:", responses[0].status_code)
            image_responses = [
                res.content for res in responses if res.status_code != 404]

        debug(len(image_responses), 'Image Responses:')
        for x, image in enumerate(image_responses, already_downloaded):
            path = dir + "\\" + f"{x+1:03}" + '.jpg'
            percentage = float((x+1)/len(image_responses))*100
            filled = int(percentage/2)
            tb_printed = "|" + loading_char * filled + incomplete_char * \
                (50-filled) + "| " + str("%.2f" % percentage) + "% Complete"

            if not image_compleated:
                with open(path, "wb") as f:
                    f.write(image)
            if os.path.exists(path):
                io = Image.open(path)
                ie = io.convert('RGB')
                if isFirst:
                    first_cimage = ie
                    isFirst = False
                else:
                    cimage_list.append(ie)
                    print("\r", tb_printed, end="")
            else:
                print("File " + path + " do not exist.....")

        if not isFirst:
            print()
            pdf_name = f"{i+1:03}" + ".pdf"
            pdf_path = os.path.join(pdf_dir, pdf_name)
            if os.path.exists(pdf_path):
                print("File " + pdf_path + " exist.....")
                print()
                continue

            first_cimage.save(pdf_path, save_all=True,
                              append_images=cimage_list)
            del first_cimage
            del cimage_list
            print()
            print("PDF Created\t:", pdf_path)
            print()

        if url == "":
            print("Last Chapter")
            break

    print()
    print(" DOWNLOAD COMPLETED ".center(42, "-"))
    menu(isBackToMenu)


def download():
    divider()

    data = comic_list()
    print(str(len(data)+1) + ". Back to menu")

    print()
    index = int(input("Choose comic: ")) - 1
    print()

    if index == len(data):
        menu()

    start = input("Start from chapter\t\t: ")
    if start == "bylink":
        by_link = input("Input URL\t\t\t: ")
        end = int(input("Chapter number\t\t\t: "))

        by_link = by_link.split(" ")
        start = by_link[0]
        if len(by_link) > 1:
            data[index]['img_el'] = " ".join(by_link[1:])

        downloader(data[index], start, end, [])

    else:
        start = int(start)
        end = int(input("End at chapter\t\t\t: "))
        skips = input(
            "Skip chapter(s)?[enter to skip][separate with comma(,)] : ").split(",")
        if skips[0] == "":
            del skips[0]

        print()
        print("Comic to be downloaded\t: " + data[index]["name"])
        print("Chapter\t\t\t: " + str(start) + " - " + str(end))
        print("Skipped chapter(s)\t: " + str(skips))

        print()
        confirm = (input("Is it correct [y/n]? [Default: y] ") or "y").lower()
        match confirm:
            case 'y':
                downloader(data[index], start, end, skips)
            case _:
                re = input("Resubmit data?[y/n] ").lower()
                match re:
                    case "y":
                        download()
                    case _:
                        menu()


def add():
    divider()

    name = input("Name\t\t\t: ")
    list_url = input("List URL\t\t: ")
    list_el = input("List Element\t\t: ")
    chapter_link_el = input("Chapter Link Element\t: ")
    img_el = input("Image Element\t\t: ")
    next_el = input("Next Element\t\t: ")

    divider()

    print("Name\t\t\t: " + name)
    print("List URL\t\t: " + list_url)
    print("List Element\t\t: " + list_el)
    print("Chapter Link Element\t: " + chapter_link_el)
    print("Image Element\t\t: " + img_el)
    print("Next Element\t\t: " + next_el)
    print()

    confirm = (input("Is it correct [y/n]? [Default: y] ") or "y").lower()

    match confirm:
        case "y":
            db_add(name, list_url, list_el, chapter_link_el, img_el, next_el)
        case _:
            menu()


def edit():
    divider()

    data = comic_list()
    print(str(len(data)+1) + ". Back to menu")

    print()
    index = int(input("Choose comic: ")) - 1

    if index == len(data):
        menu()
    comic = data[index]

    print("NOTE: Press Enter to use default value")

    print("Default:", comic["name"])
    name = input("Name\t\t\t: ")
    if name == "":
        name = comic["name"]
    print()

    print("Default:", comic["list_url"])
    list_url = input("List URL\t\t: ")
    if list_url == "":
        name = list_url["name"]
    print()

    print("Default:", comic["list_el"])
    list_el = input("List Element\t\t: ")
    if list_el == "":
        list_el = comic["list_el"]
    print()

    print("Default:", comic["chapter_link_el"])
    chapter_link_el = input("Chapter Link Element\t: ")
    if chapter_link_el == "":
        chapter_link_el = comic["chapter_link_el"]
    print()

    print("Default:", comic["img_el"])
    img_el = input("Image Element\t\t: ")
    if img_el == "":
        img_el = comic["img_el"]
    print()

    print("Default:", comic["next_el"])
    next_el = input("Next Element\t\t: ")
    if next_el == "":
        next_el = comic["next_el"]

    divider()

    print("Name\t\t\t: " + name)
    print("List URL\t\t: " + list_url)
    print("List Element\t\t: " + list_el)
    print("Chapter Link Element\t: " + chapter_link_el)
    print("Image Element\t\t: " + img_el)
    print("Next Element\t\t: " + next_el)
    print()

    confirm = (input("Is it correct [y/n]? [Default: y] ") or "y").lower()

    match confirm:
        case "y":
            db_edit(index, name, list_url, list_el,
                    chapter_link_el, img_el, next_el)
        case _:
            menu()


def delete():
    divider()

    data = comic_list()
    print(str(len(data)+1) + ". Back to menu")

    print()
    index = int(input("Choose comic: ")) - 1

    if index == len(data):
        menu()

    confirm = (input("Are you sure to delete " +
                     data[index]["name"].upper() + "?[y/n] ") or "y").lower()

    match confirm:
        case "y":
            db_delete(index)
        case _:
            menu()


def image_to_pdf():
    divider()


def available_chapter(pdfs, numbering=False):
    print()
    print("Available chapter: ")
    number = ""
    for i, ch in enumerate(pdfs):
        end_print = ", "
        if i == len(pdfs)-1 or numbering:
            end_print = "\n"
        elif (i+1) % 10 == 0:
            end_print = ",\n"

        if numbering:
            number = str(f'[{i+1}] ')

        print((number + ch.split(".")[0]), end=end_print)
    print()


def get_pdfs(dir, all=False):
    pdfs = [f for f in listdir(dir) if isfile(join(dir, f))]
    if not all:
        pdfs = [p for p in pdfs if not "-" in p]
        pdfs.sort(key=lambda x: int(x.split(".")[0]))
    else:
        pdfs.sort(key=lambda x: int(x.split(".")[0].split("-")[0]))
    return pdfs


def read(comic, index=False):
    pdf_dir = os.path.join(config['comics_path'], comic["root_dir"])
    pdfs = get_pdfs(pdf_dir, True)

    if index == False:
        available_chapter(pdfs, True)
        print()
        index = int(input("Pilih chapter\t: "))
    index = index - 1

    debug(pdf_dir, "PDFS")
    debug(pdfs, "PDFS")
    debug(index, "Open index")
    chapter_dir = os.path.join(pdf_dir, pdfs[index])
    debug(chapter_dir)
    os.startfile(chapter_dir)


def merger():
    divider()

    data = comic_list()
    print(str(len(data)+1) + ". Back to menu")

    print()
    index = int(input("Choose comic: ")) - 1

    if index == len(data):
        menu()

    comic = data[index]
    dir = os.path.join(config['comics_path'], comic["root_dir"])
    pdf_dir = os.path.join(dir, "PDF")

    pdfs = get_pdfs(pdf_dir)
    available_chapter(pdfs)

    start = int(input("Start from chapter\t\t: "))
    end = int(input("End at chapter\t\t\t: "))
    split_by = int(input("Divider per [default=50]\t: ") or 50)

    merger = PdfMerger()

    batch = 0
    counter = 0
    prev_pdf = ""
    print()
    for i in range(start, end+1):
        number = f"{i:03}"
        name = number+".pdf"
        index = 0
        if name in pdfs:
            index = pdfs.index(name)
        else:
            print(f"There is no chapter {number} ({name})")
            if prev_pdf != "":
                print("Try to add blank page")
                merger.append(blank_page_path)

            counter = counter + 1
            continue
        pdf_name = os.path.join(pdf_dir, pdfs[index])
        merger.append(pdf_name)
        prev_pdf = pdf_name
        print(pdfs[index], "merged")
        counter = counter + 1
        if counter == split_by and i != end:
            filename = str(start + (split_by * batch)) + "-" + \
                str(start + split_by*(batch+1) - 1) + ".pdf"
            filename = os.path.join(dir, filename)
            batch = batch + 1
            counter = 0
            print("Merging.........................")
            merger.write(filename)
            merger.close()
            print(filename, "created")
            merger = PdfMerger()

    filename = str(start + (split_by * batch)) + "-" + str(end) + ".pdf"
    filename = os.path.join(dir, filename)
    print("Merging.........................")
    merger.write(filename)
    merger.close()

    tb_printed = filename + " created"
    print()
    print(" MERGED ".center(len(tb_printed), "-"))
    print(tb_printed)
    print()
    menu()


# def shifter(comic, start, shift_by, shift_type):
def shifter(comic, start, shift_by, isPdfImg, shift_type="right"):

    pdf_dir = os.path.join(config['comics_path'], comic["root_dir"], "PDF")
    img_dir = os.path.join(config['comics_path'], comic["root_dir"], "Images")

    pdfs = [f for f in listdir(pdf_dir) if isfile(join(pdf_dir, f))]
    pdfs = [p for p in pdfs if not "-" in p]
    pdfs.sort(key=lambda x: int(x.split(".")[0]))

    imgs = [f for f in listdir(img_dir) if isdir(join(img_dir, f))]
    imgs.sort()

    if isPdfImg == "both" or isPdfImg == "pdf":
        print(" SHIFTING PDF ".center(42, "-"))
        print()
        print("Shift Type\t:", shift_type.upper())
        print()

        if shift_type == "right":
            loop_start = len(pdfs)
            loop_end = start-1
            loop_jump = -1
        else:
            loop_start = start
            loop_end = len(pdfs) + 1
            loop_jump = 1

        print("From", loop_start, "; To", loop_end)
        for i in range(loop_start, loop_end, loop_jump):
            number = f"{i:03}"
            name = number+".pdf"
            if name in pdfs:
                if shift_type == "right":
                    new_number = f"{i+shift_by:03}"
                else:
                    new_number = f"{i-shift_by:03}"
                new_name = new_number + ".pdf"

                if isfile(join(pdf_dir, new_name)):
                    print(f"Cannot shift file. Fix the numbering issue first!!!")
                    continue
                else:
                    os.rename(join(pdf_dir, name),
                              join(pdf_dir, new_name))
                    print(f"Renamed: {name}   --->   {new_name}")
            else:
                print(f"There is no chapter {number}")
                continue

        print()

    if isPdfImg == "both" or isPdfImg == "img":
        print(" SHIFTING IMAGE FOLDER ".center(42, "-"))
        print()
        print("Shift Type\t:", shift_type.upper())
        print()

        if shift_type == "right":
            loop_start = len(pdfs)
            loop_end = start-1
            loop_jump = -1
        else:
            loop_start = start
            loop_end = len(pdfs) + 1
            loop_jump = 1

        print("From", len(imgs), "; To", start-1)
        for i in range(loop_start, loop_end, loop_jump):
            name = f"{i:03}"

            if name in imgs:
                if shift_type == "right":
                    new_name = f"{i+shift_by:03}"
                else:
                    new_name = f"{i-shift_by:03}"
                if isdir(join(pdf_dir, new_name)):
                    print(f"Cannot shift folder. Fix the numbering issue first!!!")
                    continue
                else:
                    os.rename(join(img_dir, name),
                              join(img_dir, new_name))
                    print(f"Renamed: {name}   --->   {new_name}")
            else:
                print(f"There is no chapter {number}")
                continue

    print(" SHIFT SUCCESS ".center(42, "="))
    menu()


def shift():
    divider()
    data = comic_list()
    print(str(len(data)+1) + ". Back to menu")

    print()
    index = int(input("Choose comic: ")) - 1

    if index == len(data):
        menu()

    comic = data[index]

    start = int(input("Start shift from chapter\t: "))
    shift_by = int(input("Number of shift\t\t\t: "))
    isPdfImg = input(
        "PDF or Image Folder or Both[pdf/img/both][default:both]: ").lower()
    if isPdfImg == "":
        isPdfImg = "both"

    shift_type = input("Shift type[right,left][default: right]: ")
    if shift_type == "":
        shift_type = "right"

    divider()
    print("Start shift from chapter\t:", start)
    print("Number of shift\t\t\t:", shift_by)
    print("PDF or Image Folder or Both\t: " + isPdfImg)
    print("Shift type[next,prev][default: next]: " + shift_type)
    print()

    confirm = (input("Is it correct [y/n]? [Default: y] ") or "y").lower()
    print()
    match confirm:
        case "y":
            # shifter(comic, start, shift_by, shift_type)
            shifter(comic, start, shift_by, isPdfImg, shift_type)
        case _:
            menu()


def menu(isBackToMenu=True):
    if not isBackToMenu:
        exit(0)
    divider()
    print("1. Download Comic")
    print("2. Add Comic")
    print("3. Edit Comic")
    print("4. Delete Comic")
    print("5. Images to PDF")
    print("6. Merge PDF")
    print("7. Shift Chapter Number")
    print("8. Exit")
    print()

    menu = input("Select a menu: ")

    match menu:
        case "1":
            download()
        case "2":
            add()
        case "3":
            edit()
        case "4":
            delete()
        case "5":
            image_to_pdf()
        case "6":
            merger()
        case "7":
            shift()
        case "8":
            exit()


if len(argv) > 1:
    if len(argv) > 2:
        start = int(argv[2])
    if len(argv) > 3:
        end = int(argv[3])
    if len(argv) > 4:
        skips = argv[4]
    else:
        skips = []

    if open_state:
        comic_index = argv[1]
        comic = comic_list(False, comic_index)
        if len(argv) > 2:
            read(comic, start)
        else:
            read(comic)
    else:
        comic_index = int(argv[1]) - 1
        comic = comic_list(False)[comic_index]
        downloader(comic, start, end, skips, False)


elif __name__ == '__main__':
    hero()
    menu()
