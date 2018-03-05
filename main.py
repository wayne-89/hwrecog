# coding=utf-8
import interceptor as intercpt
import fontout as fontout
import os
import time
from emnist import EMNIST
import sys

filename = "zxlbox.jpeg"
name, ext = os.path.splitext(filename)
langdata_dir = "/Users/wayne/Work/langdata"
tessdata_dir = "/Users/wayne/Work/tesseract/tessdata"
method = 2  # 0是字体 1是box 2是emnist
imgBlockLineSize = 1  # 图片几行分割为一块 当method=1时有效
trainIterationTime = None
trainTargetErrorEate = 5
if method == 2:
    name = "emnist"


def gotArg(argsMap, key, oldValue):
    if key in argsMap:
        return argsMap[key]
    return oldValue


if len(sys.argv) > 1:
    argsMap = {}
    lastArg = None
    for arg in sys.argv:
        if arg.startswith("--"):
            lastArg = arg
        elif lastArg is not None:
            argsMap[lastArg] = arg
            lastArg = None
    method = gotArg(argsMap, "--method", method)
    filename = gotArg(filename, "--filename", filename)
    langdata_dir = gotArg(argsMap, "--langdata_dir", langdata_dir)
    tessdata_dir = gotArg(argsMap, "--tessdata_dir", tessdata_dir)
    trainIterationTime = gotArg(argsMap, "--train_iteration_times", trainIterationTime)
    trainTargetErrorEate = gotArg(argsMap, "--train_target_error_rate", trainTargetErrorEate)


# if method == 0:
#     imgBlockLineSize = -1


def convert300dP(path):
    print('convert {0} -density 300 {0}'.format(path))
    return os.system(
        'convert {0} -density 300 {0}'.format(path))


def convert2tif(filename, output):
    fileRealName = filename.split('.')[0]
    return os.system(
        'convert {0} -density 300 {1}/{2}.tif'.format(filename, output, fileRealName)) == 0


def convert(path, srcname, name, size, output):
    # os.system(
    #     'convert  {0}/{1}  -density 100  {2}'.format(
    #         path, srcname, output))
    os.system(
        'convert {0}/{1} -quality 100  {0}/{2}.pbm'.format(path, srcname, name))
    os.system(
        'potrace -s {0}/{1}.pbm -o {0}/{1}.eps'.format(path, name))
    # os.system(
    #     'convert {0}/{1}.eps  -quality 100 -density 300  -depth 32  -background white +matte -morphology Smooth  Octagon:1 -alpha Off -resize {2} {3}'.format(
    #         path, name, size, output))
    os.system(
        'convert {0}/{1}.eps -quality 100 -resize {2} {0}/{1}.jpg'.format(path, name, size))
    os.system(
        'convert {0}/{1}.jpg -quality 100   -density 300  {2}'.format(path, name, output))
    # os.system(
    #     'convert  {0}/{1}.png  -density 300 -resize {2} -background white +matte -depth 32  -alpha Off  {3}'.format(
    #         path, name, size, output))
    # exit(0)
    # os.system('convert {0}/{1}.eps  -quality 100 {0}/{1}.png'.format(path, name))

    # return os.system('convert {0}/{1}.png -resize {2} -quality 100 -alpha Off {3}'.format(path, name, size, output))


def tprint(str):
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + str)


# if convert300dP(name) == 0:
#     print('convert 300dp success')
# else:
#     print('convert 300dp failed')
#     exit()

tprint('step0 开始执行')
stTicks = time.time()
path = './output/' + name
isExists = os.path.exists(path)
if not isExists:
    os.makedirs(path)

if method == 2:
    tprint('step1 预处理: 通过enmist生成box')
    print path
    emnist = EMNIST(path, name)
    firstParNum, totalParNum = emnist.load()
    print firstParNum, totalParNum
    tprint('预处理耗时s:  ' + str(time.time() - stTicks))
else:
    ######## step1 图片转为300dp的tif
    tprint('step1 图片转为300dp的tif')
    if convert2tif(filename, path):
        tprint(filename + ' convert to tif success')
    else:
        tprint(filename + ' convert to tif failed')
        exit()
    ################################

    ####### step2 opencv依照模板识别每个字符
    tprint('step2 opencv依照模板识别每个字符')
    totalParNum, firstParNum = intercpt.doIntercept(name, path, method, imgBlockLineSize)
    tprint(filename + ' opencv split char success')
    ################################

    ####### step3 转换为字体文件
    if method == 0:
        tprint('step3 转换为字体文件')
        if fontout.generate(path + '/chars', name, 'map_file.txt', path):
            tprint(filename + ' generate font success')
        else:
            tprint(filename + ' generate font failed')
            exit(0)
    ################################
####### step4 开始训练
tprint('step4 开始训练')
# 创建文件夹
os.system('rm -rf {0}/lstm'.format(path))
os.system('mkdir -p {0}/lstm/traindata'.format(path))
os.system('mkdir -p {0}/lstm/traindata/tune'.format(path))
os.system('mkdir -p ./lstm/result')
os.system('mkdir -p {0}/lstm/src'.format(path))

# 生成lstmf
# --tessdata_dir {2} \
cmd = None
if method == 0:
    tprint('step4.1 通过字体生成lstmf')
    cmd = 'PANGOCAIRO_BACKEND=fc tesstrain.sh --fonts_dir {0} --lang eng \
      --training_text /Users/wayne/Work/langdata/eng/eng.training_text \
      --linedata_only \
      --noextract_font_properties --langdata_dir {1} \
      --fontlist "tesseracthand" --output_dir {0}/lstm/traindata'.format(path, langdata_dir, tessdata_dir)
    tprint(cmd)
    os.system(cmd)
tprint('step4.2 通过box生成lstmf ' + str(firstParNum))
for i in range(firstParNum + 1, totalParNum + 1):
    size = os.popen('identify -format "%G" ./output/{0}/eng.{0}.exp{1}.tif'.format(name, i)).read()
    print('size ', size)
    convert300dP('./output/{0}/eng.{0}.exp{1}.tif'.format(name, i))
    if method != 2:
        convert('./output/{0}'.format(name), 'eng.{0}.exp{1}.tif'.format(name, i), 'eng.{0}.exp{1}'.format(name, i),
                size,
                './output/{0}/lstm/traindata/eng.{0}.exp{1}.tif'.format(name, i))
    else:
        os.system('cp -rf ./output/{0}/eng.{0}.exp{1}.tif ./output/{0}/lstm/traindata'.format(name, i))
    os.system('cp -rf ./output/{0}/eng.{0}.exp{1}.box ./output/{0}/lstm/traindata'.format(name, i))
    # os.system('cp -rf ./output/{0}/eng.{0}.exp{1}.tif ./output/{0}/lstm/traindata'.format(name, i))

    cmd = 'tesseract ./output/{0}/lstm/traindata/eng.{0}.exp{1}.tif -psm 13 ./output/{0}/lstm/traindata/eng.{0}.exp{1} ' \
          '~/Work/tesseract/tessdata/configs/lstm.train'.format(name, i)
    tprint(cmd)
    os.system(cmd)
    if os.path.exists("./output/{0}/lstm/traindata/eng.{0}.exp{1}.lstmf".format(name, i)):
        os.system(
            'echo "./output/{0}/lstm/traindata/eng.{0}.exp{1}.lstmf" >> '
            './output/{0}/lstm/traindata/eng.training_files.txt'.format(
                name, i))
# 抽取出基础训练集中的lstm
tprint('step4.2 抽取出基础训练集中的lstm')
cmd = 'combine_tessdata -e ./lstm/eng.traineddata \
  {0}/lstm/src/eng.lstm'.format(path)
tprint(cmd)
os.system(cmd)
os.system('cp ./lstm/eng.traineddata \
  {0}/lstm/src/eng.traineddata'.format(path))
# 进行微调训练
tprint('step4.3 基于基础训练集进行微调训练')
#   --max_iterations {1}
# --target_error_rate {2}

if trainIterationTime is not None:
    cmd = 'lstmtraining --model_output {0}/lstm/traindata/tune/tune \
      --debug_interval 0 \
      --max_iterations {1} \
      --continue_from {0}/lstm/src/eng.lstm \
      --traineddata {0}/lstm/src/eng.traineddata \
      --train_listfile {0}/lstm/traindata/eng.training_files.txt \
    '.format(path, trainIterationTime, trainTargetErrorEate)
else:
    cmd = 'lstmtraining --model_output {0}/lstm/traindata/tune/tune \
      --debug_interval 0 \
      --target_error_rate {2} \
      --continue_from {0}/lstm/src/eng.lstm \
      --traineddata {0}/lstm/src/eng.traineddata \
      --train_listfile {0}/lstm/traindata/eng.training_files.txt \
    '.format(path, trainIterationTime, trainTargetErrorEate)
tprint(cmd)
os.system(cmd)
# 合并训练结果
tprint('step4.4 合并训练结果')
cmd = 'lstmtraining --stop_training \
  --continue_from {0}/lstm/traindata/tune/tune_checkpoint \
  --traineddata {0}/lstm/src/eng.traineddata \
  --model_output ./lstm/result/eng.traineddata'.format(path)
tprint(cmd)
os.system(cmd)
###############################
edTicks = time.time()

tprint("共耗时s:  " + str(edTicks - stTicks))
if method == 0:
    # 测试训练结果
    tprint('step5 测试训练结果')
    tprint('step5.1 生成测试数据')
    os.system('mkdir -p ./lstm/result/{0}'.format(name))
    os.system('cp ./lstm/eng.training_text ./lstm/result/{0}'.format(name))

    cmd = 'PANGOCAIRO_BACKEND=fc text2image --fonts_dir={0} --font=tesseracthand \
      --outputbase=./lstm/result/{1}/eng.training_text  \
      --text=./lstm/result/{1}/eng.training_text'.format(path, name)
    tprint(cmd)
    os.system(cmd)
    tprint('step5.2 输出测试结果')
    cmd = 'tesseract  --tessdata-dir ./lstm/result  ./lstm/result/{0}/eng.training_text.tif ./lstm/result/{0}/out -l eng --oem 1 --psm 3'.format(
        name)
    tprint(cmd)
    os.system(cmd)
