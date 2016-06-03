import os, sys
import subprocess
import shlex
import shutil
import time
__author__ = 'ray'

g_project_dir = "./"
g_bitsPerSample = "8"

def get_file_info(filePath):
    image_command = "sips -g pixelWidth -g pixelHeight -g bitsPerSample {file_path}".format(file_path = filePath)
    s = subprocess.Popen(image_command,shell = True,stdout=subprocess.PIPE)
    result = s.communicate()[0]
    result = result.split()
    if len(result) == 7:
        return [result[2], result[4], result[6]]
    return []

def check_file_size(info1x, info2x, info3x):
    if int(info3x[0]) == int(info1x[0]) * 3 and int(info2x[0]) == int(info1x[0]) * 2 and int(info3x[1]) == int(info1x[1]) * 3 and int(info2x[1]) == int(info1x[1]) * 2:
        return True
    else:
        return False

def check_file_bits(info):
    global g_bitsPerSample
    return info[2] == g_bitsPerSample

def do_find_command(search_dir,file_type):

    if len(search_dir) == 0 or len(file_type) == 0:
        return set()

    search_dir = search_dir.replace('\n','')

    need_add_file_list = list()
    size_not_correct_list = list()
    bits_not_correct_list = list()

    command = "find '{}' -name '*.{other}' 2>/dev/null".format(search_dir,other = file_type)
    s = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    results = s.communicate()[0].split()
    have_checked_path = set();

    for fullPath in results:

        if not fullPath.endswith(file_type):
            continue
        if fullPath in have_checked_path:
            continue
        if (not fullPath.startswith("/")) and (not fullPath.startswith(".") and (not fullPath.startswith("~")):
            continue

        prefixPath, fileName = os.path.split(fullPath)
        # print(os.path.splitext(fileName))
        splitedFileName = os.path.splitext(fileName);
        fileNamePrefix = splitedFileName[0]
        fileNameSuffix = splitedFileName[1] 

        filePath1x = ""
        filePath2x = ""
        filePath3x = ""

        if "@2x" in fileNamePrefix:
            normalFileNamePrefix = fileNamePrefix.split('@')[0];
            filePath1x = prefixPath + "/" + normalFileNamePrefix + fileNameSuffix
            filePath2x = fullPath
            filePath3x = prefixPath + "/" + normalFileNamePrefix + "@3x" +fileNameSuffix

        elif "@3x" in fileNamePrefix:
            normalFileNamePrefix = fileNamePrefix.split('@')[0];
            filePath1x = prefixPath + "/" + normalFileNamePrefix + fileNameSuffix
            filePath2x = prefixPath + "/" + normalFileNamePrefix + "@2x" +fileNameSuffix
            filePath3x = fullPath

        else:
            filePath1x = fullPath
            filePath2x = prefixPath + "/" + fileNamePrefix + "@2x" +fileNameSuffix
            filePath3x = prefixPath + "/" + fileNamePrefix + "@3x" +fileNameSuffix

        will_check_info = True    
        if (filePath1x != fullPath) and (filePath1x not in results):
            need_add_file_list.append(filePath1x)
            will_check_info = False
        if (filePath2x != fullPath) and (filePath2x not in results):
            need_add_file_list.append(filePath2x)
            will_check_info = False
        if (filePath3x != fullPath) and (filePath3x not in results):
            need_add_file_list.append(filePath3x)
            will_check_info = False


        have_checked_path.add(filePath1x)
        have_checked_path.add(filePath2x)
        have_checked_path.add(filePath3x)

        if will_check_info:
            info1x = get_file_info(filePath1x)
            info2x = get_file_info(filePath2x)
            info3x = get_file_info(filePath3x)
            if not check_file_size(info1x, info2x, info3x):
                size_not_correct_list.append([filePath1x,info1x,info2x,info3x])
            if not check_file_bits(info1x):
                bits_not_correct_list.append([filePath1x,info1x[2]])
            if not check_file_bits(info2x):
                bits_not_correct_list.append([filePath2x,info2x[2]])
            if not check_file_bits(info3x):
                bits_not_correct_list.append([filePath3x,info3x[2]])

    return need_add_file_list, size_not_correct_list, bits_not_correct_list


def support_types():
    types = []
    types.append('png')
    types.append('jpg')
    types.append('jpeg')
    types.append('gif')
    return types

def start_find_task():
    print("\n======================check begin======================")

    global g_project_dir
    global g_bitsPerSample
    for i, arg in enumerate(sys.argv):
        if arg == "-bits" and len(sys.argv) > i + 1:
            g_bitsPerSample = sys.argv[i + 1]
        if arg == "-dir" and len(sys.argv) > i + 1:
            g_project_dir = sys.argv[i + 1]

    print("#Expected dir : " + g_project_dir)
    print("#Expected bitsPerSample : " + g_bitsPerSample)

    print("\n")

    need_add_result_list = list()
    size_not_correct_list = list()
    bits_not_correct_list = list()

    for type in support_types():
        find_result = do_find_command(g_project_dir,type)
        need_add_result_list.extend(find_result[0])
        size_not_correct_list.extend(find_result[1])
        bits_not_correct_list.extend(find_result[2])

    need_add_result_list.sort()
    size_not_correct_list.sort()
    bits_not_correct_list.sort()

    print("#Lack images:\n")
    for image_name in need_add_result_list:
        print(image_name)
    print("\n-------------------------------------------------\n")

    print("#Size not correct:\n")
    for image_size_info in size_not_correct_list :
        print(image_size_info[0] + ", size1x:" + 'x'.join(image_size_info[1][:2]) + ", size2x:" + 'x'.join(image_size_info[2][:2]) + ", size3x:" + 'x'.join(image_size_info[3][:2]))
    print("\n-------------------------------------------------\n")

    print("#Bits not correct:\n")
    for image_bits_info in bits_not_correct_list :
        print(','.join(image_bits_info))

    print("\n==========================end==========================\n")

start_find_task()