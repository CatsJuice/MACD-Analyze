# MACD-Analyze

Python 对 MACD 的计算以及相关投资策略的分析

## 使用：

### 运行前提：

- Python 3.x
- 相关模块的安装
- 网易日线数据

### 方法太笨了，建议将getEMA方法改为递归

例如这样：

```python
# EMA=［2*X+(DAY-1)*EMA’］/(DAY+1)
def get_ema(x,day):
    if day==1:
        return x[0]
    
    if day>1:
        ret=(2*x[day-1]+(day-1)*get_ema(x,day-1))/(day+1)

    return ret
```

### 运行

直接运行 `macd.py` 即可(参数说明在下详述)

直接查看结果： 在 `macd_res.txt` 中存有某次运行的结果

## **基本概念**

### **MACD**

百度百科的解释：

> `MACD` 称为异同移动平均线，是从双指数移动平均线发展而来的，由快的指数移动平均线（ `EMA12` ）减去慢的指数移动平均线（ `EMA26` ）得到快线 `DIF` ，再用 `2 ×（快线DIF-DIF的9日加权移动均线DEA）` 得到 **MACD柱**

### **MACD 金叉**

> `MACD` 指标是股票技术分析中一个重要的技术指标，由两条曲线和一组红绿柱线组成。两条曲线中波动变化大的是 `DIF` 线，通常为**白线**或**红线**，相对平稳的是  `DEA` 线(MACD线)，通常为**黄线**。当 `DIF` 线上穿 `DEA` 线时，这种技术形态叫做 **`MACD金叉`**，通常为 **买入信号**

### **MACD 死叉**

> `DIF` 由上向下突破 `DEA`,为**卖出信号**

## **程序设计**

### **数据计算**

【MACD公式】

以下为通达信的公式：

```js
DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
DEA:EMA(DIF,MID);
MACD:(DIF-DEA)*2,COLORSTICK;
```

需要的变量参数为 `SHORT` , `LONG` , `MID`， 在通达信中默认分别为 `12` , `26` , `9`;
要计算 `MACD` ，关键在于求 `EMA`（指数移动平均值）, 其公式如下：

![EMA公式](https://catsjuice.cn/index/src/markdown/stock/20190520111714.png "EMA公式")

其中， `α` 为平滑指数， 一般取 `2 / ( N + 1 )`

该公式是依赖于前一日的递归的计算，最大的问题便是第一天的 `EMA[yesterday]` 无法求得， 在程序设计时， 我将它设置为当日`收盘价`,
再求 `DIF`, 第一天的 `DIF` 就变成了 `0` （当日收盘价 - 当日收盘价）, 而求 `DEA` （即 DIF 的 EMA） 时，第一天所需的 `DEA[yesterday]` 同样不知道， 将其设置为 `DIF` ( 即 0 )。

【性能优化之多线程】

由于数据量较大， 在这里我尝试使用 Python 的多线程进行分析， 添加了一个 `calculate_all_by_thread` 的方法， 接收 `1` 个参数（thread_num）即需要的线程数， 然后根据线程数动态创建线程， 将文件划分为等分的块分别计算， 创建线程部分的代码如下：

```py
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
```

这里我使用的 2 个线程进行计算， 实际测试速度虽然不是单线程的 2 倍，但是计算的时间上是有所优化的。

【数据存储】

在了解公式后， 便可迭代文件进行带入计算， 计算结果这里我采用的是将其写入原文件， 在列末尾追加新的 5 列：

- `EMA26` (26根据传参而定)
- `EMA12` (12根据传参而定)
- `DIF`
- `DEA`
- `MACD`

【数据验证】

完成计算后， 有必要对计算结果进行验证, 这里， 我简单写了一个输出来进行简单验证， 该部分代码如下：

```py
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
    plt.plot(dates, difs, c='yellow')
    plt.plot(dates, deas, c='black')
    plt.bar(dates, macds, color=color_macd)
    plt.xticks(fontsize=5)
    plt.xlabel('', fontsize=5)
    fig.autofmt_xdate()
    plt.show()
```

在对股票 `'000002'` 进行验证， 验证结果如下（上图为通达信MACD截图， 下图为程序输出的图片， 时间为`2018-01-01` ~ `2019-04-26`）：

![2018-01-01 ~ 20019-04-26, 000002 macd验证](https://catsjuice.cn/index/src/markdown/stock/20190520.jpg "2018-01-01 ~ 20019-04-26, 000002 macd验证")

可以看到图形基本一致， 但是同样对股票 `000001` 进行验证， 结果如下：

![2018-01-01 ~ 20019-04-26, 000001 macd验证](https://catsjuice.cn/index/src/markdown/stock/201905201329.jpg "2018-01-01 ~ 20019-04-26, 000001 macd验证")

此时， 两图形基本没有重合， 原因是因为计算 `MACD` 时， 第一天的 `EMA`并不是前一天计算的，同样 `DEA` 也是， 而这里数据只计算了 `2018-01-01 ~ 2010-04-26`, 所以前面基本一致的时候， 是因为第一日刚好相近导致后面计算偏差不大， 对此， 应该不设置截止日期以保证数据的可靠性, 我将时间设置到了 `2014-01-01`， 重新验证 `000001` 得到如下：

![2018-01-01 ~ 20019-04-26, 000001 macd验证(修改后)](https://catsjuice.cn/index/src/markdown/stock/201905211027.jpg "2018-01-01 ~ 20019-04-26, 000001 macd验证(修改后)")

然后再随机抽取一直股票进行验证， 如下为 `600702` 的结果

![2018-01-01 ~ 20019-04-26, 600702 macd验证](https://catsjuice.cn/index/src/markdown/stock/201905211033.jpg "2018-01-01 ~ 20019-04-26, 600702 macd验证")

### **数据分析**

这里主要是对 `MACD` 的分析， 所以以上计算的数据实际上只要用到 `MACD` , 对 `MACD` 柱满足以下形态的股票进行分析：

![MACD形态](https://catsjuice.cn/index/src/markdown/stock/20190521151217.png "MACD形态")

该形态需满足以下特点：

- 出现连续的红色块（MACD > 0）
- 紧接着出现连续蓝色块（MACD < 0）
- 蓝色块小于第一个红色块
- 蓝色块后面跟着一个红色块， 且后一红色块大于前一红色块

在程序设计时， 使用的是迭代数据行， 通过 `if` 判断， 来定位上述的 3 个块， 在第三块大于第一块时即为符合条件的形态；大致思路是， 定义 3 个变量来标记 3 块的合计值：

- red_1
- green_1
- red_2

判断三个块的条件分别为：

- 块 1 ：`green_1 == 0 and red_2 == 0`
- 块 2 ：`red_1 != 0 and red_2 == 0`
- 块 3 ：`red_1 != 0 and red_2 != 0 and green_1 != 0`

## **参数说明**

no. | param              | type          | mean                 | format       | default      | necessary | demo
:---|--------------------|---------------|----------------------|--------------|--------------|-----------|------
1   | `file_prefix`      | `str`         | 日线文件前缀          | /            | `None`        | `True`   | `'F:\\files\\sharesDatas\\kline\\'`
2   | `end_date`         | `str`         | 截止日期              |`yyyy-mm-dd`  | '0000-00-00'  | `False`  | `'2019-01-01'`
3   | `short`            | `int`         | 短期的天数            | /            | `12`          |  `False` | `12`
4   | `long`             | `int`         | 长期的天数            | /            | `26`          | `False`  |  `26`
5   | `mid`              | `int`         | 计算`DEA`时， `DIF`的`EMA`天数| /    | `9`           | `False`   | `9`
6   | `count_max`        | `int`         | 判断后面的多少天涨跌情况| /           | `5`            | `False`  | `10`
7   | `count_border`     | `int`         | 设置最大天数内至少多少天涨才符合  | /  | `3`           | `False` | `6`

## **function注释**

- `calculate_noe`
  - 计算单只股票的 `MACD` 、 `DIF` 、 `EMA` 、 `DEA`
  - 需要参数：
    - `code`: 股票的代码
  - 返回值：
    - `None`
- `calculate_all_by_thread`
  - 通过多线程计算所有股票
  - 需要参数：
    - `thread_num`: 线程数量
  - 返回值:
    - `None`
- `calculate_block`:
  - 计算指定代码块的股票
  - 需要参数：
    - `start`：块下标开始
    - `end`: 块下标结束
  - 返回值：
    - `None`
- `verify_calculate`
  - 验证计算的结果
  - 需要参数：
    - `code`: 股票的代码
  - 返回值：
    - `None`
- `analyze_macd_one`:
  - 分析单只股票 的 `macd`
  - 需要参数：
    - `code`: 股票的代码
  - 返回值：
    - `None`
- `analyze_macd_by_thread`:
  - 通过多线程分析所有股票
  - 需要参数：
    - `thread_num`: 线程数量
  - 返回值:
    - `None`
- `analyze_block`:
  - 分析指定代码块的股票
  - 需要参数：
    - `start`：块下标开始
    - `end`: 块下标结束
  - 返回值：
    - `None`
- `show_res`:
  - 输出分析结果并写入相关文件
  - 需要参数：`None`
  - 返回值： `None`

## **结果分析**

【某次结果截图】

![MACD分析结果截图](https://catsjuice.cn/index/src/markdown/stock/20190521155326.png "MACD分析结果截图")

计算 MACD 时候的传参均为默认， 即通达信公式中的默认值， 对上述情况进行分析得到的结果是， 后 10 天内至少 6 天比符合条件时涨了的比例约为 55% ， 而如果将参数调整为  5 天内至少 3 天， 则比例降低到约47%， 而如果不是 MACD 的值计算有误的话， 可见这个 `MACD` 的指标并不是很可靠， 但可以调整计算 `MACD` 的参数的值
