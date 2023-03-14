from pypdf import PdfMerger
import os
from os import listdir
from os.path import isfile, join
from sys import argv

start = 1
end =50
split_by = 25

dir = os.path.join("C:\\", "Users", "qorya", "Documents", "weak_hero")

if len(argv) > 1:
	if int(argv[1]) != 0:
		dir = int(argv[1])
if len(argv) > 2:
	start = int(argv[2])
if len(argv) > 3:
	end = int(argv[3])
if len(argv) > 4:
	split_by = int(argv[4])
if split_by > start-end:
	split_by = start-end

pdfs = [f for f in listdir(dir) if isfile(join(dir, f))]
pdfs = [p for p in pdfs if not "-" in p]
pdfs.sort(key=lambda x: int(x.split(".")[0]))

merger = PdfMerger()

batch = 0
counter = 0
for i in range(start, end+1):
	index = pdfs.index(str(i)+".pdf")
	pdf_name = os.path.join(dir, pdfs[index])
	merger.append(pdf_name)
	print(pdfs[index], "merged")
	counter = counter + 1
	if counter == split_by and i != end-1:
		filename = str(start + (split_by * batch)) + "-" + str(split_by*(batch+1)) + ".pdf"
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
print(filename, "created")