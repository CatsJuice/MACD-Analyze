import pandas as pd
import os
from tqdm import tqdm
import math
import threading

import numpy as np
import matplotlib.pyplot as plt

class MACD(object):

    def __init__(self):
        pass

    def get_ema(self, day, close, ema_yesterday):
        # price_today = close_arr[len(close_arr)-day]
        alpha = 2 / (day + 1)
        return alpha * close + (1-alpha) * ema_yesterday
        
    def get_dif(self, ema_fast, ema_slow):
        return ema_fast - ema_slow

    def get_macd(self, dif, dea):
        return (dif-dea) * 2

class MACD_Analyze(object):

    def __init__(self, file_prefix, end_date='2019-01-01', short=12, long=26, mid=9, count_max=5, count_border=3):
        self.file_prefix = file_prefix
        self.end_date = end_date
        self.short = short
        self.long = long
        self.mid = mid
        self.macd_res = []
        self.count_max = count_max
        self.count_border = count_border

    # 计算单只股票的 MACD， DIF， EMA， DEA
    def calculate_one(self, code):
        try:
            df = pd.read_csv(self.file_prefix + str(code) + '.csv', encoding='gbk')
        except:
            print("文件: %s.csv 打开失败" % code)
            return
        # df = df[df.日期 > self.end_date]    # 筛选结束日期后的
        df = df.iloc[::-1]                  # 倒置

        colume_long = "EMA" + str(self.long)
        colume_short = "EMA" + str(self.short)
        colume_dif = "DIF"
        colume_dea = "DEA"
        colume_macd = "MACD"

        df[colume_long] = ''
        df[colume_short] = ''
        df[colume_dif] = ''
        df[colume_dea] = ''
        df[colume_macd] = ''

        # 迭代 排序后的数据
        macd = MACD()
        last_row = None
        for index, row in df.iterrows():
            if row['日期'] < self.end_date:
                continue
            if row['收盘价'] == "None" or row['收盘价'] == 0:
                # 数据不全， 不作处理
                continue
            if row['MACD'] != '':
                # print("已经有数据了")
                continue
            if last_row is None:
                # 第一天的 ema 默认为收盘价
                ema_long = row['收盘价']
                ema_short = row['收盘价']
                dif = macd.get_dif(ema_short, ema_long)
                dea = macd.get_ema(self.mid, dif, dif)
                macd_ = (dif-dea) * 2
            else:
                ema_long = macd.get_ema(self.long, row['收盘价'], ema_yesterday=last_row[colume_long])
                ema_short = macd.get_ema(self.short, row['收盘价'], ema_yesterday=last_row[colume_short])
                dif = macd.get_dif(ema_short, ema_long)
                dea = macd.get_ema(self.mid, dif, last_row[colume_dea])
                macd_ = (dif-dea) * 2
            # 更新 DataFrame 和 row
            row[colume_long] = ema_long
            row[colume_short] = ema_short
            row[colume_dif] = dif
            row[colume_dea] = dea
            row[colume_macd] = macd_

            df.loc[index, colume_long] = ema_long
            df.loc[index, colume_short] = ema_short
            df.loc[index, colume_dif] = dif
            df.loc[index, colume_dea] = dea
            df.loc[index, colume_macd] = macd_

            last_row = row
        df = df.iloc[::-1]
        # print(df)
        df.to_csv(self.file_prefix + str(code) + '.csv', index=False, encoding='gbk')

    # 多线程计算所有股票
    def calculate_all_by_thread(self, thread_num):
        file_list = os.listdir(self.file_prefix)
        file_count = len(file_list)
        offset = file_count / thread_num
        offset = math.ceil(offset)
        threads = []
        for i in range(thread_num):
            start = i * offset
            end = (i+1) * offset if (i+1) * offset < file_count else -1
            thread = threading.Thread(target=self.calculate_block, args=(start, end))
            threads.append(thread)
        for t in threads:
            t.setDaemon(True)
            t.start()
        t.join()

    # 计算股票块
    def calculate_block(self, start=0, end = -1):
        file_list = os.listdir(self.file_prefix)
        file_list = file_list[start:end]
        for index in tqdm(range(len(file_list))):
            code = file_list[index]
            code = code[0:6]
            self.calculate_one(code)

    # 验证计算结果
    def verify_calculate(self, code):
        try:
            df = pd.read_csv(self.file_prefix + str(code) + '.csv', encoding='gbk')
        except:
            print('文件%s.csv打开失败' % code)
            return
        df = df[df.日期 > self.end_date]    
        df = df[::-1]
        mid = []
        dates = []
        difs = []
        deas = []
        macds = []
        color_macd = []
        for index, row in df.iterrows():
            mid.append(0)
            dates.append(row['日期'])
            difs.append(row['DIF'])
            deas.append(row['DEA'])
            macds.append(row['MACD'])
            if row['MACD'] > 0:
                color_macd.append('red')
            else:
                color_macd.append('green')
        # 绘制图表
        fig = plt.figure(dpi=128, figsize=(100, 6))
        plt.plot(dates, mid, c='blue')
        plt.plot(dates, difs, c='#c78300')
        plt.plot(dates, deas, c='black')
        plt.bar(dates, macds, color=color_macd)
        plt.xticks(fontsize=5)
        
        plt.xticks(np.arange(0,200,10))
        plt.xlabel('', fontsize=5)
        fig.autofmt_xdate()
        plt.show()

    # 分析单只股票 的 macd
    def analyze_macd_one(self, code):
        try:
            df = pd.read_csv(self.file_prefix + code + '.csv', encoding='gbk')
            temp = df['MACD']
        except:
            print("文件%s.csv打开失败" % code)
            return
        df = df[df.日期 > self.end_date]    # 截取 截止日期之后的数据 
        df = df[::-1]   # 倒转
        day_min = 5     # 至少连续的天数， 设置为 5
        red_1 = 0
        red_1_day = 0
        green_1 = 0
        green_1_day = 0
        red_2 = 0
        red_2_day = 0
        buy = False
        last_row = None
        count_buy = 0                       # 标记符合条件后的几天
        count_max = self.count_max          # 最多看5天是否会涨
        count_raise = 0                     # 标记涨的天数
        count_border = self.count_border    # 要判断的涨了几天
        for index, row in df.iterrows():
            if row['MACD'] == '':
                continue
            # 验证是否会涨
            if buy and count_buy < count_max:
                count_buy += 1
                if row['收盘价'] > last_row['收盘价']:
                    count_raise += 1
            elif count_buy == count_max:
                dic = {'code': code, 'date': last_row['日期'], 'raise': False}
                if count_raise > count_border:
                    dic['raise'] = True
                buy = False
                count_buy = 0
                count_raise = 0
                self.macd_res.append(dic)

            # 找到第一个红色块
            if red_2 == 0 and green_1 == 0:
                if row['MACD'] <= 0:
                    if red_1 == 0:
                        continue
                    else:
                        if red_1_day < day_min:
                            red_1_day = 0
                            red_1 = 0
                        else:
                            green_1 += row['MACD']
                            green_1_day += 1
                else:
                    red_1 += row['MACD']
                    red_1_day += 1
            # 找到紧接着的绿色块
            elif red_1 != 0 and red_2 == 0:
                if row['MACD'] > 0:
                    if green_1_day < day_min:
                        red_1 = 0
                        red_1_day = 0
                        green_1 = 0
                        green_1_day = 0
                    else:
                        if -1 * green_1 > red_1:
                            red_1 = 0
                            red_1_day = 0
                            green_1 = 0
                            green_1_day = 0
                        else:
                            red_2 += row['MACD']
                            red_2_day += 1
                else:
                    green_1 += row['MACD']
                    green_1_day += 1
            # 找到第三个块
            elif red_1 != 0 and red_2 != 0 and green_1 != 0:
                if row['MACD'] > 0:
                    red_2 += row['MACD']
                    if red_2 > red_1:
                        # 符合情况， 应该买入
                        buy = True
                        last_row = row
                        # print(code, ":", row['日期'])
                        red_1 = red_2
                        red_1_day = red_2_day
                        green_1 = 0
                        green_1_day = 0
                        red_2 = 0
                else:
                    red_1 = 0
                    red_1_day = 0
                    green_1 = 0
                    green_1_day = 0
                    red_2 = 0

    # 多线程分析macd
    def analyze_macd_by_thread(self, thread_num):
        file_list = os.listdir(self.file_prefix)
        file_count = len(file_list)
        offset = file_count / thread_num
        offset = math.ceil(offset)
        threads = []
        for i in range(thread_num):
            start = i * offset
            end = (i+1) * offset if (i+1) * offset < file_count else -1
            thread = threading.Thread(target=self.analyze_block, args=(start, end))
            threads.append(thread)
        for t in threads:
            t.setDaemon(True)
            t.start()
        t.join()

    # 分析块
    def analyze_block(self, start, end):
        file_list = os.listdir(self.file_prefix)
        file_list = file_list[start:end]
        for index in tqdm(range(len(file_list))):
            code = file_list[index]
            code = code[0:6]
            self.analyze_macd_one(code)

    def show_res(self):
        txt = open('macd_res.txt',mode='w', encoding='utf-8')
        count = 0
        for i in self.macd_res:
            if i['raise']:
                txt.write("股票%s在 [%s] 满足条件， 后%s天至少%s天涨了\n" % (i['code'], i['date'], self.count_max, self.count_border))
                count += 1
            else:
                txt.write("股票%s在 [%s] 满足条件， 后%s天不到%s天涨了\n" % (i['code'], i['date'], self.count_max, self.count_border))
        rate = count / len(self.macd_res) * 100
        rate = format(rate, '.4f')
        rate += "%"
        txt.write("共有%s种可能情况， 后%s天内， 至少%s天涨的有%s种， 占比%s\n" % (len(self.macd_res), self.count_max, self.count_border, count, rate))
        print("共有%s种可能情况， 后%s天内， 至少%s天涨的有%s种， 占比%s\n" % (len(self.macd_res), self.count_max, self.count_border, count, rate))
    
if __name__ == '__main__':
    macd_analyze = MACD_Analyze(file_prefix='F:\\files\\sharesDatas\\kline\\', end_date='2018-08-01', count_max=10, count_border=6)
    # macd_analyze.calculate_one('603999')
    # macd_analyze.verify_calculate('000005')
    # macd_analyze.calculate_all_by_thread(thread_num=2)
    # macd_analyze.analyze_macd_one('000006')
    macd_analyze.analyze_macd_by_thread(thread_num=1)
    macd_analyze.show_res()