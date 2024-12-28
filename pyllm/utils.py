import subprocess
import logging
import json
import copy

def run_command(cmd, style="colorful"):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  
    logging.debug(f"运行命令:\n{cmd}")
    if len(cmd.split("\n")) > 1:
        printc(f"运行命令:\n{cmd}", style=style)
    else:
        printc(f"运行命令: {cmd}", style=style)
    stdout, stderr = process.communicate()  
    return f"stdout\n{stdout.decode()}\nstderror\n{stderr.decode()}"

def truncate_string(text,length,truncate_mark = "<TRUNCATED>"):
    """
    截断字符串，如果长度大于指定长度则截断并添加省略号。
    Args:
        text (str): 原始字符串。
        length (int, optional): 指定长度。
    Returns:
        str: 截断后的字符串。
    """
    if len(text) <= length:
        return text
    else:
        return text[:length] + truncate_mark

def pretty(obj):
    obj = copy.deepcopy(obj)
    def change_str_value_to_list(txt):
        list = []
        for line in txt.split('\n'):
            if line.strip() != '':
                list.append(line)
        if len(list) <= 1:
            return txt
        else:
            return list
    
    def deep_parse(input):
        if isinstance(input,dict):
            for k in input:
                input[k] = deep_parse(input[k])
        if isinstance(input,list):
            for i in range(len(input)):
                input[i] = deep_parse(input[i])
        if isinstance(input,str):
            input = change_str_value_to_list(input)
        return input 

    try:
        if isinstance(obj, str):
            obj  = json.loads(obj)
        deep_parse(obj)
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception as e:
        return str(obj)

def printc(text, color = "white", end="\n",style = "colorful"):  
    """  
    在终端中打印彩色文本。  
      
    :param text: 要打印的文本。  
    :param color: 文本的颜色。
    """  
    if style == "mute":
        return
    elif style == "colorful":
        color_codes = {  
            'red': '\033[91m',  
            'green': '\033[92m',  
            'yellow': '\033[93m',  
            'blue': '\033[94m',  
            'magenta': '\033[95m',  
            'cyan': '\033[96m',  
            'white': '\033[97m',  
            'grey': '\033[90m',
            'reset': '\033[0m'  # 重置颜色  
        }  
        print(f"{color_codes[color]}{text}{color_codes['reset']}",end=end)  
    elif style == "plain":
        print(text, end=end)
    else:
        print(text, end=end)
        