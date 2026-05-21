import os
import subprocess
from pathlib import Path

#cwd = Current Working Directory（当前工作目录）
#是Path的类方法，直接调用就能获取程序运行时所在的文件夹路径
WORKDIR = Path.cwd()

def safe_path(p:str)-> Path:
    #用 / 直接拼接路径
    #结果：生成一个相对路径对象
    path=(WORKDIR/p).resolve()
    #判断 path 是不是 WORKDIR 的「子路径]
    #（也就是文件是否在项目工作目录内部）
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path 

def run_bash(command:str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any (d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        #作用：指定 subprocess.run() 启动的子命令 / 子进程，在哪个文件夹里运行
        #你的 Python 主程序：有自己的工作目录（就是 WORKDIR = Path.cwd()）
        #subprocess.run() 启动的 子命令 / 子进程：可以有独立的工作目录 → 这个目录就是 cwd= 指定的
        #cwd=None（不写这个参数）→ 子进程继承Python 主程序的工作目录（和 WORKDIR 一样）
        r=subprocess.run(command,shell=True,cwd=WORKDIR,capture_output=True, text=True, timeout=120)
        out=(r.stdout+r.stderr).strip()
        return out if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    
def run_read(path:str,limit:int=None) -> str:
    try:
        #.read_text() 是 Python 内置标准库 pathlib 中 Path 对象的专属实例方法
        #一键读取文本文件的全部内容
        text=safe_path(path).read_text
        #把一整段文本，按「换行符」切割成「元素是一行一行的列表」
        #输出：一个列表 lines，列表里的每一个元素 = 文本的一行
        lines=text.splitlines()
        if limit and limit < len(lines):
            lines=lines[:limit]+[f"... ({len(lines) - limit} more lines)"]
            #用 join() 可以把 行列表 → 还原成原始文本！
            #把列表 / 序列里的元素，拼接成一整段字符串
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"
    
def run_write(path:str,content:str) -> str:
    try:
        fp=safe_path(path)
        fp.parent.mkdir(parents=True,exist_ok=True)
        #自动创建文件
        #如果 test.txt 不存在，write_text 会自动新建文件，不用手动创建。
        #默认覆盖写入
        #会清空文件原有内容，再写入新内容（追加内容用其他方法，这个是覆盖）。
        fp.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"
    
def run_edit(path:str,old_text:str,new_text:str) -> str:
    try:
        fp=safe_path(path)
        content=fp.read_text()
        if old_text not in content:
            return f"Error: Text not found in {path}"
        #content：你之前读取的原始文件文本（字符串）
        #old_text：要被替换掉的旧内容
        #new_text：用来替换的新内容
        #只替换【第一次出现】的旧内容（默认不写会替换所有）
        fp.write_text(content.replace(old_text,new_text,1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"
