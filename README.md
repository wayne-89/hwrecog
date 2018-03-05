## 安装
1. 安装tesseract4.0
2. 安装netpbm
    brew install netpbm
3. 安装fontforge
    npm install fontforge
4. 安装potrace
    http://potrace.sourceforge.net/#downloading
5. 安装imagemagick
    brew install imagemagick
6. 安装opencv
    参考https://www.jianshu.com/p/b5424e9cb7ad
7. 安装python-mnist
    pip install python-mnist
8. 下载emnist物料
    https://www.westernsydney.edu.au/bens/home/reproducible_research/emnist
    放于根目录的 emnist/data下

## 使用
支持3种method
通用配置参数：
```
--langdata_dir /Users/wayne/Work/langdata  #langdata路径
--tessdata_dir /Users/wayne/Work/tesseract/tessdata #tessdata路径
--train_iteration_times 1200 #迭代次数
--train_target_error_rate 0.5 #目标训练错误率
注：train_iteration_times和train_target_error_rate只会有一个生效， 优先使用train_iteration_times
```
1. 通过生成字体训练
刚方式，会将单个字符生成字体去训练， 单词形式通过box去训练
训练需要使用模板，模板映射到的内容见template.txt
注意： 字体训练的训练物料要求必须是单个字符
```
--method 0
--filename test.png  #指定项目路径下的待训练图片
```
2. 通过生成box文件训练
过程类似生成字体训练， 只是全部是通过box文件训练
```
--method 1
--filename test.png  #指定项目路径下的待训练图片
```

3. 通过使用emnist的文件训练
将emnist中的数据提取出图片，生成box去训练
```
--method 2
```

使用举例：
```
python main.py --langdata_dir /Users/wayne/Work/langdata --tessdata_dir /Users/wayne/Work/tesseract/tessdata \
--train_iteration_times 1200 --method 0 --filename zxl.jpeg
```

训练过程产生的数据在 output/图片name/中

最后训练出的结果在 lstm/result/中






