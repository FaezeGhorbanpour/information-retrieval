# He is the cause of excellence and salvation.
# Hamshahri newspaper information retrieval system

from __future__ import division
from __future__ import unicode_literals

import io
import os
import sys
import traceback

import hazm

from Document import Document
from Measurement import Measurement


def return_content(file_address):
    address = '..\HamshahriData\\' + file_address
    with io.open(address, 'r', encoding='utf8') as f:
        text = f.read()
    return text

test = Document()
measurement = None
print(
    'شماره فولدرها جهت مقداردهی اولیه به دیکشنری را وارد کنید. (این شمارهها باید 2003 تا 2007 باشد و بین آنها فاصله قرار دهید.)')
folder_number = [int(i) for i in input().split(" ")]
test.add_several_doc(folder_number)
temp = True
while temp:
    try:
        print(
            'برای اتمام برنامه کاراکتر x را وارد کنید. \n'
            ' در غیر اینصورت برای وارد کردن پرسمان کاراکتر p\n '
            'برای نمایش لغات پر تکرار اسناد کاراکتر m\n'
            ' برای اضافه کردن پوشه خاص کاراکتر a\n '
            'برای حذف پوشه خاص کاراکتر d\n '
            'برای ذخیره سازی مجموعه اسناد کاراکتر s\n '
            'و برای بارگزاری از فایل کاراکتر l\n'
            ' برای واردکردن متن جهت مشاهده کلمات پردازش شده آن کاراکتر u\n'
            ' برای وارد کردن کلمه جهت جستجو در مجموعه اسناد کاراکتر i\n'
            ' جهت مشاهده سند خاص کاراکتر t\n'
            'برای بارگذاری فایل ارزیابی نهایی کاراکتر z\n'
            ' را وارد کنید. ')
        state = input()
        if state == 'x':
            temp = False
        elif state == 'p':
            print(
                'پرسمان خود را وارد کنید. در صورتی که مایلید از پرسمان های آماده استفاده کنید، کاراکتر $ را وارد کنید.')
            text = input()
            all = False
            number = 0
            if '$' in text:
                print('شماره پرسمان را وارد کنید در صورتی که مایلید تمام پرسمان ها را اجرا کنیم all را بنویسید.')
                number = input()
                if 'a' in number:
                    all = True
                else:
                    address = 'Queris\\' + number + '.q'
                    text = return_content(address)
            print('نوع جستجو را مشخص کنید. برای جستجوی ترتیبی عدد 0 و برای جستجوی دقیق عدد 1 را وارد کنید.')
            search_type = int(input())
            print(
                'نوع بازیابی را مشخص کنید. برای بازیابی از نوع lnn-ltn عدد 0 و برای بازیابی از نوع lnc-ltc عدد 1 را وارد')
            retrival_type = int(input())
            print(
                'نوع ارزیابی را مشخص کنید. \nبرای ارزیابی از نوع F Measure عدد 1 \nو برای بازیابی از نوع MAP عدد 2 \nو برای هر دو معیار 3 \nو برای هیچ کدام 0 را وارد کنید.\n برای ارزیابی باید ابتدا فایل ارزیابی را بارگذاری کنید.')
            measure_type = input()
            if measurement is None:
                print('فایل ارزیابی بارگذاری نشده است!')
                measure_type = '0'

            if all:
                all_F = 0
                all_M = 0
                count = 0
                for root, dirs, files in os.walk('..\HamshahriData\\' + 'Queris\\'):
                    count = len(files)
                    for file in files:
                        print(file, end=' :  ')
                        with open(os.path.join(root, file), 'r', encoding='utf8') as f:
                            text = f.read()
                            docs = test.search(text, search_type, retrival_type)
                            print(docs)
                            if measure_type == '1' or measure_type == '3':
                                print('F measure : ', end=" ")
                                temp = measurement.F_measure(int(file[:-2]), docs)
                                all_F += temp
                                print(temp)
                            if measure_type == '2' or measure_type == '3':
                                print('MAP :', end=" ")
                                temp = measurement.MAP(int(file[:-2]), docs)
                                all_M += temp
                                print(temp)
                if measure_type == '1' or measure_type == '3':
                    print('Average F measure : ', end=" ")
                    print(all_F / count)
                if measure_type == '2' or measure_type == '3':
                    print('Average MAP :', end=" ")
                    print(all_M / count)
            else:
                docs = (test.search(text, search_type, retrival_type))
                print(docs)
                if measure_type == '1' or measure_type == '3':
                    print('F measure : ', end=" ")
                    print(measurement.F_measure(int(number), docs))
                if measure_type == '2' or measure_type == '3':
                    print('MAP :', end=" ")
                    print(measurement.MAP(int(number), docs))

        elif state == 't':
            print('نام سند را جهت مشاهده محتوا وارد کنید. ')

            file_name = input()
            if file_name in test.docs:
                raw_text = return_content('HamshahriCorpus\\' + str(test.docs[file_name]) + '\\' + file_name + '.ham')
            else:
                print("سال را نیز وارد کنید.")
                year = input()
                raw_text = return_content('HamshahriCorpus\\' + year + '\\' + file_name + '.ham')
            print(raw_text)
        elif state == 'm':
            print(test.most_repeated_words)
        elif state == 's':
            print('نام فایل جهت ذخیره سازی مجموعه اسناد وارد کنید.')
            test.save_dictionary(input())
        elif state == 'l':
            print('نام فایل جهت بارگذاری مجموعه اسناد وارد کنید.')
            test.load_dictionary(input())
        elif state == 'a':
            print('نام فایل و سالی که فایل در آن قرار دارد، را وارد کنید. (بین نام و سال فاصله قرار دهید.)')
            year, file_name = (i for i in input().split(" "))
            test.add_document(year, file_name)
        elif state == 'd':
            print('نام فایل و سالی که فایل در آن قرار دارد، را وارد کنید. (بین نام و سال فاصله قرار دهید.)')
            year, file_name = (i for i in input().split(" "))
            test.delete_document(int(year), file_name)
        elif state == 'u':
            print('متن فارسی خود را جهت پردازش وارد کنید. در انتهای متن $ قرار دهید.')
            text = input()
            while '$' not in text :
                text += input()
            words, x = test.prepare({'test': text[:-1]})
            print(words)
        elif state == 'i':
            print('کلمه خود را وارد کنید.')
            word = hazm.Stemmer().stem(input())
            related_doc = test.find_relevent_doc(word)
            for i in related_doc:
                print(i.data, i.frequency, i.posting_list)
        elif state == 'z':
            query_docs = dict()
            with io.open('..\HamshahriData\\' + 'RelativeAssesemnt\judgements.txt', 'r', encoding='utf8') as f:
                text = f.readlines(100000)
                for line in text:
                    query, doc = line.split(" ")
                    query = int(query)
                    if query in query_docs:
                        query_docs[query].append(doc[:-1])
                    else:
                        query_docs[query] = [doc[:-1]]
            measurement = Measurement(query_docs, len(test.docs))
            print('فایل ارزیابی بار گذاری شد.')
        print('=' * 75)
    except:
        type, value, traceBack = sys.exc_info()
        lines = traceback.format_exception(type, value, traceBack)
        print(''.join(line for line in lines))
        pass
