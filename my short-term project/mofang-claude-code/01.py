import os
#执行系统命令（如 Windows 的 dir、ping;Linux/macOS 的 ls、pwd）
#启动外部程序（如 .exe、.sh 脚本、ffmpeg、git 等工具）
#让 Python 代码调用系统的命令行
import subprocess
from dataclasses import dataclass

try:
    import readline
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
    readline.parse_and_bind('set enable-meta-keybindings on')
#专门用来控制终端的命令行输入交互
#parse_and_bind() 就是给 readline 库加载配置规则，每一行都是一条终端输入规则：
#使之有识别中文、输出中文、不会有乱码、中文转义正常的功能
except ImportError:
    pass

#创建大模型接口，并配置环境变量和参数
from anthropic import Anthropic
from dotenv import load_dotenv
#override=True 是关键参数：强制覆盖系统中已存在的同名环境变量。
load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN",None)

client=Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]

#系统提示词
SYSTEM = (
    f"You are a coding agent at {os.getcwd()}. "
    "Use bash to inspect and change the workspace. Act first, then report clearly."
)

#全都是大写，恒定不变的常量
#定义了一个工具列表，工具列表里目前就一个工具(bash),
#列表元素的形式是字典
TOOLS=[{
    "name":"bash",
    "description":"Run a shell command in the current workspace.",
    #定义「输入数据的格式规则」
    "input_schema":{
        "type":"object",
        #定义字典里允许有哪些字段
        "properties":{
            "command":{"type":"string"}
        },
        "required":["command"],
    },
}]

@dataclass
class LoopState:
    messages:list#无默认值的话，意味着使用时必须赋值
    turn_count:int=1
    transition_reason:str|None=None#可以是字符串，也可以是空值；默认为空
#带安全防护的系统命令执行函数
#接收一个系统命令 → 
#拦截危险命令（防止删库 / 关机 / 提权）→ 
#安全执行普通命令 → 捕获超时 / 错误 → 
#最终返回执行结果或报错信息。
#输入：command（字符串类型，就是你要执行的系统命令，
#比如 ls、dir、ping）
#输出：返回字符串（命令的执行结果 或 错误提示）
def run_bash(command:str)->str:
    #危险命令拦截（安全防护）
    dangerous=["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(item in command for item in dangerous):
        return "Error: Dangerous command blocked"
    try:
        #在当前工作目录下，
        #执行指定的系统命令，
        #捕获命令的输出 / 错误信息，
        # 设置超时限制，最后把执行结果存到 result 变量中。
        result=subprocess.run(
            command,# 1. 要执行的命令
            shell=True,# 2. 通过系统Shell执行命令
            cwd=os.getcwd(),# 3. 命令的工作目录(获取Python 脚本当前所在的工作目录)
            capture_output=True,# 4. 捕获命令的输出和错误
            text=True,# 5. 输出转为文本字符串
            timeout=120,# 6. 执行超时时间
        )
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    #比如命令写错、命令不存在、权限不足，返回具体的错误原因
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}" 
    output=(result.stdout+result.stderr).strip()
    return output[:50000] if output else"(no output)"

#从由字典构成的列表里，提取文本，并且把所有文本串联起来，
#返回一个字符串；
#提取用户消息中的命令，再执行系统命令
def extract_text(content)-> str:
    #Python 内置判断函数，专门检查变量的类型
    #检查变量 content 是不是列表（list）,如果不是列表,
    #就直接返回空字符串 ""，并终止函数后续所有代码。
    if not isinstance(content,list):
        return ""
    texts=[]
    #遍历 content 列表里的每一个数据块 → 
    #尝试取出每个数据块的 text（文本）→ 
    #如果文本有内容 →
    #就把它存进 texts 列表中。
    for block in content:
        #getattr(对象, 属性名, 默认值),安全获取对象属性
        text=getattr(block,"text",None)
        if text:
            texts.append(text)
    #.join() 是一个字符串方法，
    #用于将序列（如列表、元组等）中的元素连接成一个字符串。
    return "\n".join(texts).strip()

#执行调用工具的命令
def execute_tool_calls(response_content)-> list[dict]:
    results=[]
    for block in response_content:
        if block.type !="tool_use":
            continue
        command = block.input["command"]
        #\033：转义字符（代表键盘上的 ESC 键）
        #[33m：黄色前景色代码
        #$→ 命令行提示符
        #\033[0m:重置终端颜色
        print(f"\033[33m$ {command}\033[0m")
        output=run_bash(command)
        print(output[:200])
        results.append({
            "type":"tool_result",
            "tool_use_id":block.id,
            "content":output,
        })
    return results

#涉及到前面的循环状态这个类、大模型回复的调用（参数的配置）；
#执行工具命令函数；上下文消息列表中要加两次（角色、内容）
def run_one_turn(state:LoopState)-> bool:
    #调用大模型，让它回复
    response=client.messages.create(
        model=MODEL,
        system=SYSTEM,
        messages=state.messages,
        tools=TOOLS,
        max_tokens=8000,
    )
    state.messages.append({"role":"assistant","content":response.content})

    if response.stop_reason!="tool_use":
        state.transition_reason=None
        return False
    
    results=execute_tool_calls(response.content)
    if not results:
        state.transition_reason=None
        return False
    
    state.messages.append({"role":"user","content":results})
    state.turn_count += 1
    state.transition_reason="tool_result"
    return True

def agent_loop(state:LoopState) -> None:
    while run_one_turn(state):
        pass

#1. Python 程序主入口：只有直接运行这个脚本时，
#才会执行下面的代码
if __name__ =="__main__":
    history=[]
    while True:
        try:
            query=input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q","exit",""):
            break

        history.append({"role":"user","content":query})
        state=LoopState(messages=history)
        agent_loop(state)

        ## 9. 提取【最后一条助手回复】的纯文本（用你之前的 extract_text 函数
        final_text=extract_text(history[-1]["content"])
        if final_text:
            print(final_text)
        ## 空行分隔，让界面更整洁
        print()
