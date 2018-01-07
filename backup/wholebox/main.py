# coding=utf-8
import interceptor as intercpt
import fontout as fontout
import os
import time

filename = "lzx.jpg"
name, ext = os.path.splitext(filename)
langdata_dir = "/Users/wayne/Work/langdata"
tessdata_dir = "/Users/wayne/Work/tesseract/tessdata"
method = 1  # 0是字体 1是box


def convert300dP(name):
    return os.system(
        'convert ./output/{0}/eng.{0}.exp1.tif -density 300 ./output/{0}/eng.{0}.exp1.tif'.format(name))


def convert2tif(filename, output):
    fileRealName = filename.split('.')[0]
    return os.system(
        'convert {0} -density 300 {1}/{2}.tif'.format(filename, output, fileRealName)) == 0


def convert(path, srcname, name, size):
    print name, path
    print('convert {0}/{1} {0}/{2}.pbm'.format(path, srcname, name))
    os.system(
        'convert {0}/{1} {0}/{2}.pbm'.format(path, srcname, name))
    print('potrace -s {0}/{1}.pbm -o {0}/{1}.eps'.format(path, name))

    os.system(
        'potrace -s {0}/{1}.pbm -o {0}/{1}.eps'.format(path, name))
    return os.system('convert {0}/{1}.eps -resize {2}  {0}/lstm/traindata/eng.{1}.exp1.png'.format(path, name, size))
    # return os.system(
    #     "convert {0}/lstm/traindata/eng.{1}.exp1.png -flatten -alpha Off -resize {2} {0}/lstm/traindata/eng.{1}.exp1.tif".format(
    #         path, name,
    #         size))


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
if intercpt.doIntercept(name, path, method):
    tprint(filename + ' opencv split char success')
else:
    tprint(filename + ' opencv split char failed')
    exit(0)
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
os.system('mkdir -p {0}/lstm/traindata'.format(path))
os.system('mkdir -p {0}/lstm/traindata/tune'.format(path))
os.system('mkdir -p ./lstm/result')
os.system('mkdir -p {0}/lstm/src'.format(path))

# 生成lstmf
tprint('step4.1 通过字体生成lstmf')
# --tessdata_dir {2} \
cmd = None
if method == 0:
    cmd = 'PANGOCAIRO_BACKEND=fc tesstrain.sh --fonts_dir {0} --lang eng \
      --training_text /Users/wayne/Work/langdata/eng/eng.training_text \
      --linedata_only \
      --noextract_font_properties --langdata_dir {1} \
      --fontlist "tesseracthand" --output_dir {0}/lstm/traindata'.format(path, langdata_dir, tessdata_dir)
else:
    size = os.popen('identify -format "%G" ./output/{0}/result_for_box.tif'.format(name)).read()
    convert('./output/{0}'.format(name), 'result_for_box.tif', name, size)
    os.system('cp -rf ./output/{0}/eng.{0}.exp1.* ./output/{0}/lstm/traindata'.format(name))
    cmd = 'tesseract ./output/{0}/lstm/traindata/eng.{0}.exp1.png ./output/{0}/lstm/traindata/eng.{0}.exp1 ' \
          '~/Work/tesseract/tessdata/configs/lstm.train'.format(
        name)
tprint(cmd)
os.system(cmd)
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
cmd = 'lstmtraining --model_output {0}/lstm/traindata/tune/tune \
  --continue_from {0}/lstm/src/eng.lstm \
  --traineddata {0}/lstm/src/eng.traineddata \
  --train_listfile {0}/lstm/traindata/eng.training_files.txt \
  --max_iterations 800'.format(path)
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
