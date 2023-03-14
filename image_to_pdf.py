from PIL import Image
import os
from os import listdir
from os.path import isfile, join
import sys

root_dir = os.path.join("C:\\", "Users", "qorya", "Documents", "weak_hero")

skips = []
start = 0
limit = 5

if len(sys.argv) > 1:
	start = int(sys.argv[1])
if len(sys.argv) > 2:
	limit = int(sys.argv[2])
if len(sys.argv) > 3:
	skips = sys.argv[3].split(",")

for i in range(limit):
	folder_number = f"{i+1:03}"
	dir = os.path.join(root_dir, folder_number)
	onlyfiles = [f for f in listdir(dir) if isfile(join(dir, f))]
	onlyfiles.sort(key=lambda x: int(x.split(".")[0]))

	if i+1 < start or i+1 in skips:
		continue

	first_cimage = 0
	cimage_list = []
	print("Merging Image......")
	for x, image in enumerate(onlyfiles):
		img_path = os.path.join(dir, image)
		io = Image.open(img_path)
		ie = io.convert('RGB')
		if x == 0:
			first_cimage = ie
		else:
			cimage_list.append(ie)
	pdf_number = f"{i+1:03}"
	pdf_path = root_dir + "\\" + pdf_number + ".pdf"
	print("Converting to PDF......")
	first_cimage.save(pdf_path, save_all=True, append_images=cimage_list)
	print("------------------- Success -------------------")
	print("|")
	print(pdf_path)
	print("|")
	print("-------------------------------------------------")