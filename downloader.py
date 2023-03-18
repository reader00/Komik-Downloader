import grequests
from bs4 import BeautifulSoup
import os
from PIL import Image
import json

from pypdf import PdfMerger
from os import listdir
from os.path import isfile, join, isdir
from sys import argv


db_name = "database.json"
loading_char = "█"


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


def comic_list(isPrint=True):
    f = open(db_name)
    data = json.load(f)

    for i, comic in enumerate(data):
        if isPrint:
            print(str(i+1) + ".", comic["name"])
    return data


def divider():
    length = 42
    character = "-"

    print()
    print(character * length)
    print()


def db_add(name, list_url, list_el, chapter_link_el, img_el, next_el):
    f = open(db_name)
    data: list = json.load(f)

    folder_name = name.replace(" ", "_")

    root_dir = os.path.join("C:\\", "Users", "qorya",
                            "Documents", "Komik", folder_name)

    data.append({
        "name": name,
        "list_url": list_url,
        "list_el": list_el,
        "chapter_link_el": chapter_link_el,
        "img_el": img_el,
        "next_el": next_el,
        "root_dir": root_dir
    })

    with open(db_name, "w") as outfile:
        json.dump(data, outfile)

    print()
    print((" " + name + " ADDED ").center(42, "-"))
    menu()


def db_edit(index, name, list_url, list_el, chapter_link_el, img_el, next_el):
    f = open(db_name)
    data: list = json.load(f)

    folder_name = name.replace(" ", "_")

    root_dir = os.path.join("C:\\", "Users", "qorya",
                            "Documents", "Komik", folder_name)

    new_data = {
        "name": name,
        "list_url": list_url,
        "list_el": list_el,
        "chapter_link_el": chapter_link_el,
        "img_el": img_el,
        "next_el": next_el,
        "root_dir": root_dir
    }

    data[index] = new_data

    with open(db_name, "w") as outfile:
        json.dump(data, outfile)

    print()
    print((" " + name + " EDITED ").center(42, "-"))
    menu()


def db_delete(index):
    f = open(db_name)
    data: list = json.load(f)

    comic_name = data[index]["name"]
    del data[index]

    with open(db_name, "w") as outfile:
        json.dump(data, outfile)

    print()
    print((" " + comic_name.upper() + " DELETED ").center(42, "-"))
    menu()


def downloader(comic, start, end, skips, isBackToMenu=True):
    print()
    if not isinstance(start, int):
        url = start
        start = end
    else:
        page = grequests.map([grequests.get(comic["list_url"])])[0]
        soup = BeautifulSoup(page.content, 'html.parser')
        chapter_list_selector = comic["list_el"] + \
            " " + comic["chapter_link_el"]
        # chapter_list_selector = comic["chapter_link_el"]
        print(chapter_list_selector)

        chapter_list = soup.select(chapter_list_selector)
        # print(chapter_list)
        chapter_list.reverse()
        url = chapter_list[start-1]['href']

    root_dir = comic["root_dir"]
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

    img_dir = os.path.join(root_dir, "Images")
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)

    pdf_dir = os.path.join(root_dir, "PDF")
    if not os.path.exists(pdf_dir):
        os.mkdir(pdf_dir)

    for i in range(start-1, end):
        tb_printed = "Current URL\t: " + url
        print((" Downloading chapter " + str(i+1) + " "
               ).center(len(tb_printed), "-"))
        print()
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
        if len(next_url) == 0:
            url = ""
        else:
            url = next_url[-1]['href']

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

        already_downloaded = 0
        for x in range(len(images)):
            path = dir + "\\" + f"{x+1:03}" + '.jpg'
            if os.path.exists(path):
                print("File " + path + " already exist.....")
                already_downloaded = already_downloaded + 1

        img_requests = (grequests.get(image['src'])
                        for image in images[already_downloaded:])
        responses = grequests.map(img_requests)
        image_responses = [res.content for res in responses]

        for x, image in enumerate(image_responses, already_downloaded):
            path = dir + "\\" + f"{x+1:03}" + '.jpg'
            percentage = float((x+1)/len(images))*100
            filled = int(percentage/2)
            tb_printed = "|" + loading_char * filled + "-" * \
                (50-filled) + "| " + str("%.2f" % percentage) + "% Complete"
            with open(path, "wb") as f:
                f.write(image)
            io = Image.open(path)
            ie = io.convert('RGB')
            if isFirst:
                first_cimage = ie
                isFirst = False
            else:
                cimage_list.append(ie)
                print("\r", tb_printed, end="")

        print()
        pdf_name = f"{i+1:03}" + ".pdf"
        pdf_path = os.path.join(pdf_dir, pdf_name)
        if os.path.exists(pdf_path):
            print("File " + pdf_path + " exist.....")
            print()
            continue

        first_cimage.save(pdf_path, save_all=True, append_images=cimage_list)
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
    if isBackToMenu:
        menu()


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
    if start == "by link":
        start = input("Input URL\t\t\t: ")
        end = int(input("Chapter number\t\t\t: "))

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


def merger():
    divider()

    data = comic_list()
    print(str(len(data)+1) + ". Back to menu")

    print()
    index = int(input("Choose comic: ")) - 1

    if index == len(data):
        menu()

    comic = data[index]
    dir = comic["root_dir"]
    pdf_dir = os.path.join(comic["root_dir"], "PDF")

    pdfs = [f for f in listdir(pdf_dir) if isfile(join(pdf_dir, f))]
    pdfs = [p for p in pdfs if not "-" in p]
    pdfs.sort(key=lambda x: int(x.split(".")[0]))

    print()
    print("Available chapter: ")
    for i, ch in enumerate(pdfs):
        end_print = ", "
        if i == len(pdfs)-1:
            end_print = "\n"
        elif (i+1) % 10 == 0:
            end_print = ",\n"

        print(ch.split(".")[0], end=end_print)
    print()

    start = int(input("Start from chapter\t\t: "))
    end = int(input("End at chapter\t\t\t: "))
    split_by = int(input("Divider per [default=50]\t: ") or 50)

    merger = PdfMerger()

    batch = 0
    counter = 0
    print()
    for i in range(start, end+1):
        number = f"{i:03}"
        name = number+".pdf"
        index = 0
        if name in pdfs:
            index = pdfs.index(name)
        else:
            print(f"There is no chapter {number} ({name})")
            continue
        pdf_name = os.path.join(pdf_dir, pdfs[index])
        merger.append(pdf_name)
        print(pdfs[index], "merged")
        counter = counter + 1
        if counter == split_by and i != end:
            filename = str(start + (split_by * batch)) + "-" + \
                str(split_by*(batch+1)) + ".pdf"
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
def shifter(comic, start, shift_by, isPdfImg):

    pdf_dir = os.path.join(comic["root_dir"], "PDF")
    img_dir = os.path.join(comic["root_dir"], "Images")

    pdfs = [f for f in listdir(pdf_dir) if isfile(join(pdf_dir, f))]
    pdfs = [p for p in pdfs if not "-" in p]
    pdfs.sort(key=lambda x: int(x.split(".")[0]))

    imgs = [f for f in listdir(img_dir) if isdir(join(img_dir, f))]
    imgs.sort()

    if isPdfImg == "both" or isPdfImg == "pdf":
        print(" SHIFTING PDF ".center(42, "-"))

        for i in range(len(pdfs), start-1, -1):
            number = f"{i:03}"
            name = number+".pdf"
            if name in pdfs:
                new_number = f"{i+shift_by:03}"
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
        print("From", len(imgs), "; To", start-1)
        for i in range(len(imgs), start-1, -1):
            name = f"{i:03}"

            if name in imgs:
                new_name = f"{i+shift_by:03}"
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

    # shift_type = input("Shift type[next,prev][default: next]: ")
    # if shift_type == "":
    #     shift_type = "next"

    divider()
    print("Start shift from chapter\t:", start)
    print("Number of shift\t\t\t:", shift_by)
    print("PDF or Image Folder or Both\t: " + isPdfImg)
    # print("Shift type[next,prev][default: next]: " + shift_type)
    print()

    confirm = (input("Is it correct [y/n]? [Default: y] ") or "y").lower()
    print()
    match confirm:
        case "y":
            # shifter(comic, start, shift_by, shift_type)
            shifter(comic, start, shift_by, isPdfImg)
        case _:
            menu()


def menu():
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
    comic_index = int(argv[1]) - 1
    start = int(argv[2])
    end = int(argv[3])
    if len(argv) > 4:
        skips = argv[4]
    else:
        skips = []

    comic = comic_list(False)[comic_index]
    downloader(comic, start, end, skips, False)


elif __name__ == '__main__':
    hero()
    menu()
