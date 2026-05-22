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
    

#-- 并发安全分类 --
#只读工具可安全并行运行；修改型工具必须串行执行。
CONCURRENCY_SAFE = {"read_file"}
CONCURRENCY_UNSAFE = {"write_file", "edit_file"}

TOOL_HANDLERS={
    "bash":      lambda **kw:run_bash(kw["command"]),
    "read_file": lambda **kw:run_read(kw["path"],kw.get["limit"]),
    "write_file":lambda **kw:run_write(kw["path"],kw["content"]),
    "edit_file": lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}

TOOLS = [
    {"name": "bash", "description": "Run a shell command.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read file contents.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace exact text in file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
]

# # 初始化空列表
# clean_content = []

# # 遍历所有内容块
# for block in msg["content"]:
#     # 只处理字典
#     if isinstance(block, dict):
#         # 新建空字典，存放清洗后的数据
#         new_block = {}
#         # 遍历字典的键值对
#         for k, v in block.items():
#             # 只保留 不以下划线开头 的键
#             if not k.startswith("_"):
#                 new_block[k] = v
#         # 把清洗后的字典加入列表
#         clean_content.append(new_block)

# # 最终赋值
# clean["content"] = clean_content
def normalize_messages(messages:list) -> list:
    """ 在发送至 API 前清理消息。
    包含三项工作：
    移除 API 无法识别的内部元数据字段
    确保每条工具调用(tool_use)都有对应的工具执行结果(tool_result)，缺失则插入占位符
    合并连续的同角色消息(API 要求角色严格交替)
    """
    cleaned=[]
    for msg in messages:
        clean={"role":msg["role"]}
        if isinstance(msg.get("content"),str):
            clean["content"]=msg["content"]
        elif isinstance(msg.get("content"),list):
            #.items()方法：获取字典里所有的「键 (key) : 值 (value)」对，返回一个可遍历的视图对象，
            #里面的每一个元素都是 (键, 值) 格式的元组。
            #遍历消息里的内容块，只保留字典类型的块，
            #并且删除字典中以下划线 _ 开头的内部字段，把清洗后的数据存入 clean["content"]。
            clean["content"]=[
                {k:v for k,v in block.items()
                 if not k.startswith("_")}#专门用来检查一个字符串是否以指定的 字符 / 子字符串 开头，
                                          #最终返回布尔值：True（是）或 False（否）。
                for block in msg["content"]
                if isinstance(block,dict)
            ]
        else:
            clean["content"]=msg.get("contnet","")
    cleaned.append(clean)
    # Collect existing tool_result IDs

    # 1. 创建一个空集合，用来存储【已存在的工具结果ID】
    existing_results=set()
    # 2. 遍历【清理完成后的所有消息】（cleaned 是清理好的消息列表）
    for msg in cleaned:
        ## 3. 安全判断：如果这条消息的 content 是列表类型（避免报错）
        if isinstance(msg.get["content"],list):
            # 4. 遍历消息内容里的每一个块（和你上一段代码的 block 是同一个东西）
            for block in msg["content"]:
                # 5. 筛选：是字典 且 类型为「工具执行结果」
                if isinstance(block,dict) and block.get("type") == "tool_result":
                    existing_results.add(block.get("tool_use_id"))

    #找出孤立的工具调用块，并插入占位符结果
    #遍历清理后的消息，只检查助手（assistant）发送的内容，
    #找到没有对应结果的孤立工具调用（tool_use），
    #并自动插入一条占位符工具结果，标记为 (cancelled)（已取消）。
    for msg in cleaned:
        if msg["role"] != "assistant" or not isinstance(msg.get("content"),list):
            continue
        for block in msg["content"]:
            if not isinstance(block,dict):
                continue
            if block.get("type") == "tool_use" and block.get("id") not in existing_results:
                cleaned.append({"role":"user","content":[
                    {"type":"tool_result","tool_use_id":block["id"],
                     "content":"(cancelled)"}
                ]})

    if not cleaned:
        return cleaned
