from imutils.object_detection import non_max_suppression
import numpy as np
import pytesseract
import argparse
import cv2
import os
from PIL import Image, ImageFilter, ImageEnhance
import pandas as pd
import io
import os
import pathlib



def ocr_core(filename):
    text = (pytesseract.image_to_data(Image.open(filename)))
    df = pd.read_csv(io.StringIO(text), sep='\t')
    return df


def show_ocr(filename):
    filename = pathlib.Path(working_dir, img_dir, filename)
    filename = str(filename)
    df = ocr_core(filename)
    img = cv2.imread(filename)
    h, w, _ = img.shape

    for ir, b in df.iterrows():
        img = cv2.rectangle(img, (b['left'], b['top']), (b['left']+b['width'], b['top']+b['height']), (0,255,0), 6-b['level'])

    font = cv2.FONT_HERSHEY_SIMPLEX
    for ir, b in df.loc[df['level']==5,:].iterrows():
        try:
            cv2.putText(img, b['text'], (b['left'], b['top']+b['height']), font, 1, (255, 0, 0), 2, cv2.LINE_AA)
        except:
            print('error')
    cv2.imshow(filename, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imwrite('output/output_rect.png', img)
    return img


def save_to_pdf_or_html(filename,pdf_or_html):
    pdf_or_html_output = pytesseract.image_to_pdf_or_hocr(Image.open(filename), extension=pdf_or_html)
    f = open("output/ocr_output."+pdf_or_html, "w+b")
    f.write(bytearray(pdf_or_html_output))
    f.close()

if __name__=='__main__':
    os.chdir(pathlib.Path(r"C:\\Users\\wenluyang\\Documents\\projet\\OCR"))
    working_dir = os.getcwd()
    img_dir = "data/img"
    filename = "0002.jpg"

    path = pathlib.Path(working_dir, img_dir, filename)
    print(path)

    #df = ocr_core(path)
    show_ocr(path)
    #df.to_csv('output/datadf.csv')


