# -*- coding: utf-8 -*-
import visa
import os
import sys
import time
# from pyvisa.resources import MessageBasedResource
print(sys.version)
pwd = os.getcwd()
print('Start at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def read_bmp():
    # PC端通过VISA接口发送命令，仪器响应命令后直接将当前显示图像的位图数据流返回至PC端缓存区。
    global rm, inst
    finalpath = "_".join(
        ["Screenshot",
         time.strftime("%Y%m%d_%H%M%S.bmp", time.localtime())])
    f = open(finalpath, 'wb')
    inst.write(':DISPlay:DATA?')
    data = inst.read_raw()  # 返回的是bytes类型
    bmp = data[11:-1]
    # 返回的数据流中含有TMC数据头，需要去掉才是符合标准的位图数据流。
    # 数据结束位置的结束符'\n'(0X0A)需要去掉。
    f.write(bmp)
    print('Finished, Storaged screenshot BMP image to: ' +
          os.path.join(pwd, finalpath))


def read_wavform(read_length, *, Channel):
    global rm, inst
    inst.write(':stop')
    if ("CH1" == Channel):
        inst.write(':WAV:SOUR CHAN1')
        print(':wavform:source channel1')
        print(inst.query(':WAVeform:SOURce?'))
    if ("CH2" == Channel):
        inst.write(':WAV:SOUR CHAN2')
        print(':wavform:source channel2')
        print(inst.query(':WAVeform:SOURce?'))
    inst.write(':WAVeform:MODE RAW')
    inst.write(':WAVeform:FORMat byte')  # word|byte|ascii
    code = 0  # 0 不编码 1 编码
    Yorigin = int(inst.query(':WAVeform:YORigin?'))
    Yreference = int(inst.query(':WAVeform:YREFerence?'))  # 127
    Yincrement = float(inst.query(':WAVeform:YINCrement?'))
    Sample_rate = (inst.query(':ACQuire:SRATe?')).strip().replace(
        '+', '').replace('0000e0', 'e').replace('.', '_')  # 剔除空字符，"\n""+" 和"0"
    # print(Yorigin)
    # print(Yreference)
    # print(Yincrement)
    finalpath = "_".join([
        Channel, 'SampleRate', Sample_rate, 'length',
        str(read_length),
        time.strftime("%Y%m%d_%H%M%S.txt", time.localtime())
    ])
    f = open(finalpath, 'w')
    package = 249999
    start_position = 1
    data = []
    outstr = b''
    if read_length <= package:
        stop_position = read_length
        inst.write(':WAVeform:STARt %d' % start_position)
        inst.write(':WAVeform:STOP %d' % stop_position)
        inst.write(':WAV:DATA?')
        data = inst.read_raw()  # 返回的是bytes类型
        if code == 1:
            outstr += data[11:-1].decode('ascii')  # 将bytes类型解码为string，方便拼接
        else:
            for x in data[11:-1]:
                x = (x - Yreference - Yorigin) * Yincrement  # 转换为电压
                # f.write(str(x))
                f.write('{0:.4e}'.format(x))
                f.write('\n')
        # print(outstr)
        # for x in data[11:-1]:
        #     x = (x - Yreference - Yorigin) * Yincrement
        #     f.write(str(x))
        #     f.write('\n')
        # data.append(inst.query_ascii_values(':WAV:DATA?')[11:])
    else:
        times = read_length // package
        for i in range(times):
            print(
                '{CH},分块存储，{current_time:>2}/{total_time}; '.format(
                    CH=Channel, current_time=i + 1, total_time=times + 1),
                end='')
            process_bar = (i + 1) / (times + 1)  # 进度条变量
            print('#' * int(20 * process_bar),
                  '.' * int(20 - 20 * process_bar), '[{0:2.2f}%]'.format(
                      100 * process_bar))  # 输出进度条
            start_position = 1 + package * i
            stop_position = package * (i + 1)
            # print('strat= %d' % start_position)
            # print('stop= %d' % stop_position)
            inst.write(':WAVeform:STARt %d' % start_position)
            inst.write(':WAVeform:STOP %d' % stop_position)
            # data.append(inst.query_ascii_values(':WAV:DATA?')[11:])
            inst.write(':WAV:DATA?')
            data = inst.read_raw()  # 返回的是bytes类型
            if code == 1:
                outstr += data[11:-1].decode('ascii')  # 将bytes类型解码为string，方便拼接
            else:
                for x in data[11:-1]:
                    x = (x - Yreference - Yorigin) * Yincrement  # 转换为电压
                    # f.write(str(x))
                    f.write('{0:.4e}'.format(x))
                    f.write('\n')
        i = i + 1
        print(
            '{CH},分块存储，{current_time:>2}/{total_time}. '.format(
                CH=Channel, current_time=i + 1, total_time=times + 1),
            end='')
        process_bar = (i + 1) / (times + 1)  # 进度条变量
        print('#' * int(20 * process_bar), '.' * int(20 - 20 * process_bar),
              '[{0:2.2f}%]'.format(100 * process_bar))  # 输出进度条
        start_position = 1 + package * i
        # print('strat= %d' % start_position)
        # print('stop= %d' % read_length)
        inst.write(':WAVeform:STARt %d' % start_position)
        inst.write(':WAVeform:STOP %d' % read_length)
        inst.write(':WAV:DATA?')
        data = inst.read_raw()  # 返回的是bytes类型
        if code == 1:
            outstr += data[11:-1].decode('utf-8')  # 将bytes类型解码为string，方便拼接
        else:
            for x in data[11:-1]:
                x = (x - Yreference - Yorigin) * Yincrement  # 转换为电压
                # f.write(str(x))
                f.write('{0:.4e}'.format(x))
                f.write('\n')

    # dataarray = bytes(b"#9000200000WWWW\n")
    # dataarray = bytes(data)
    # output = data[11:]
    # print(output)
    # print(len(output))
    # print(len(data))
    # print(type(data))
    # print(type(dataarray))
    if code == 1:
        finalbytes = outstr.encode()
        for x in finalbytes:
            x = (x - Yreference - Yorigin) * Yincrement  # 转换为电压
            f.write(str(x))
            f.write('\n')
    f.close()
    print('Finished, Storage waveform to: ' + os.path.join(pwd, finalpath))
    print('')
    # inst.close()
    # print(inst.query(':WAVeform:STATus?'))


rm = visa.ResourceManager()
# print(rm.list_resources())

inst = rm.open_resource('USB0::6833::1200::DS2G181000049::0::INSTR')
inst.timeout = 5000
inst.read_termination = '\n'
print(inst)
print(inst.query('*IDN?'))
# inst.write(':autoscale')
inst.write(':CHAN2:DISP 1')
inst.write(':CHAN1:DISP 1')
inst.write(':run')
inst.write(':ACQuire:MDEPth 7000000')  # 设置存储深度

print('当前存储深度: ', inst.query(':ACQuire:MDEPth?').strip())  # 获取存储深度

# time.sleep(3)

inst.write(':single')
time.sleep(0.5)
# inst.write(':tforce')
time.sleep(3)

# inst.write(':stop')

# inst.write(':SAVE:IMAGe:FACTors 1')# 打开或关闭图像存储时的参数保存功能
# inst.write(':SAVE:IMAGe D:\\20171217.png')

# 分块读取模式

read_bmp()

read_wavform(7000000, Channel='CH1')
time.sleep(2)
# print(inst.query(':wavform:source?'))

read_wavform(7000000, Channel='CH2')
# print(inst.query(':wavform:source?'))

# f = open('D:\\YY\\RIGOL\\new.txt', 'w')
# f.write(data)
# f.close()
# for idata in bytearray(data,'ascii'):
#     YREFerence = 0
#     YORigin = 0
#     YINCrement = 1
#     out = (idata - YREFerence - YORigin) * YINCrement
#     # print(out)
#     # print(i)
#     f.write(str(out))
#     f.write('\n')
#     # print(idata)
#     # print(type(idata))
#     f.close()
print('Finished at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
inst.close()
