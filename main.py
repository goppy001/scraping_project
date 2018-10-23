#!/home/tgoto/.pyenv/versions/3.7.0/bin/python
# -*- coding: utf-8 -*-

from flask import *
from bs4 import BeautifulSoup
import requests
import math
import numpy as np
import re

app = Flask(__name__)

@app.route('/', methods=["GET", "POST"])
def post():
    return render_template("form.html")

@app.route('/result', methods=["GET", "POST"])
def result():
    if request.method == "GET":
        return render_template('form.html')
    else:
        url = str(request.form["url"])
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'lxml')
        # "希望職種"の抽出
        job_list = soup.find_all(class_="job js_inputAreaJob")
        for job_elem in job_list:
            job_name = job_elem.find_all(class_="inputSelect")[0].text
        # "希望勤務地"の抽出
        area_list = soup.find_all(class_="area js_inputAreaArea")
        for area_elem in area_list:
            area_names = area_elem.find_all(class_="inputSelect")
            area_name = area_names[0].text
        # "希望業種"の抽出
        type_list = soup.find_all(class_="type")
        type_list2 = []
        for type_elem in type_list:
            type_names = type_elem.find_all(class_="inputSelect")
            for type_name in type_names:
                type_list2.append(type_name.text)
        genre = type_list2[0]
        # 給料の抽出
        salary_list = soup.find_all(itemprop="baseSalary")
        salary_list2 = []
        for salary in salary_list:
            salary_list2.append(salary.text)
        salary_list3 = []
        for line in salary_list2:
            elem = line.split("円")
            # "月給"から始まっている給料部分を抽出
            if elem[0].startswith("月給"):
                salary_list3.append(elem[:2])
        # 「月給○○円～」形式になっているものを抽出。「～」以降が文字列なら対象外とする
        pu_salary = []
        for salary in salary_list3:
            if salary[1].startswith("～"):
                if salary[1].endswith("万") or salary[1].endswith("千"):
                    pass
                else:
                    salary[1] = ""
            else:
                salary[1] = ""
            pu_salary.append(salary)
        re_salary = []

        # "~"がくっついてしまっているものに対して処理
        for salary in pu_salary:
            if "～" in salary[0]:
                salary2 = salary[0].split("～")
                if salary2[1] != "":
                    if not salary2[0].endswith("万"):
                        s = re.sub(r'\D', '', salary2[0])
                        s_size = int(math.log10(int(s)) + 1)
                        if s_size < 6:
                            salary2[0] = str(salary2[0]) + "万"
                        if s_size == 6:
                            salary2[0] = float(salary2[0]) / 1000
                            salary2[0] = str(salary2[0]) + "万"
                    if salary2[0].endswith("千"):
                        front = float(salary2[0].split("万")[0])
                        back = float(salary2[0].split("万")[1])
                        back /= 10
                        salary2[0] = str(front + back)
                    salary[0] = salary2[0]
                    salary[1] = salary2[1]
                else:
                    pass
            else:
                pass
            re_salary.append(salary)

        # 給料を数値化し計算できる状態にする
        under_array = np.array([])
        limit_array = np.array([])
        for salary in re_salary:
            under_salary = salary[0]
            if salary[1] != "":
                limit_salary = salary[1]
                separate_limit = limit_salary.split("万")
                if separate_limit[1] != "":
                    limit_salary_num = re.sub(r'\D', '', separate_limit[0])
                    separate_limit_num = re.sub(r'\D', '', separate_limit[1])
                    separate_limit_size = int(math.log10(int(separate_limit_num)) + 1)
                    #抽出した給料の桁数に応じて処理
                    if separate_limit_size == 1:
                        separate_limit[1] = float(separate_limit_num) / 10
                        separate_limit[0] = float(limit_salary_num) + separate_limit[1]
                        limit_salary = str(separate_limit[0])
                    if separate_limit_size == 4:
                        separate_limit[1] = float(separate_limit_num) / 100000                        
                        separate_limit[0] = float(limit_salary_num) + separate_limit[1]
                        limit_salary = str(separate_limit[0])
            else:
                limit_salary = str(0)
            separate_under = under_salary.split("万")
            # 万より下の端数がある場合の処理
            if separate_under[1] != "":
                under_salary_num = re.sub(r'\D', '', separate_under[0])
                separate_under_num = re.sub(r'\D', '', separate_under[1])
                separate_under_size = int(math.log10(int(separate_under_num)) + 1)
                # 抽出した給料の桁数に応じて処理
                if separate_under_size == 1:
                    separate_under[1] = float(separate_under_num) / 10
                    separate_under[0] = float(under_salary_num) + separate_under[1]
                    under_salary = str(separate_under[0])
                if separate_under_size == 4:
                    separate_under[1] = float(separate_under_num) / 10000
                    separate_under[0] = float(under_salary_num) + separate_under[1]
                    under_salary = str(separate_under[0])
            else:
                pass
            under_salary_num = under_salary.replace("月給", "")
            under_salary_num = under_salary_num.replace("万", "")
            limit_salary_num = limit_salary.replace("月給", "")
            limit_salary_num = limit_salary_num.replace("～", "")
            limit_salary_num = limit_salary_num.replace("万", "")
            under_salary_num = float(under_salary_num)
            limit_salary_num = float(limit_salary_num)
            under_array = np.append(under_array, under_salary_num)
            limit_array = np.append(limit_array, limit_salary_num)

        #平均値を求める
        under_array = under_array[~np.isnan(under_array)]
        under_ave  = np.average(under_array)
        limit_array = limit_array[~(limit_array == 0)]
        limit_ave  = np.average(limit_array)
        under_array_size = under_array.shape[0]
        limit_array_size = limit_array.shape[0]
        under_ave = round(under_ave, 2)
        limit_ave = round(limit_ave, 2)
    return render_template('result.html', job_name=job_name, area_name=area_name, genre=genre, under_array_size=under_array_size, under_ave=under_ave, limit_array_size=limit_array_size, limit_ave=limit_ave)

if __name__ == "__main__":
	app.run(debug=True)
