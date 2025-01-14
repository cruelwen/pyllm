import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pyllm.llm import LLM
from pyllm.agent_base import AgentBase
from pyllm.utils import *
import numexpr


def init_llm():
    return LLM(model="qwen-plus",url="https://dashscope.aliyuncs.com/compatible-mode/v1")

def init_agent():
    return AgentBase(model="qwen-plus", url="https://dashscope.aliyuncs.com/compatible-mode/v1")

def example_hello_world():
    llm = init_llm()
    answer = llm.ask("Hello, world")
    print(answer)

def example_bots_chat():
    llm = init_llm()
    a_say = "来成语接龙吧，我先说，百里挑一"
    printc(f"A: {a_say}", color="blue")
    for i in range(5):
        b_say = llm.chat_with_context(a_say, ctx="bot_b")
        printc(f"B: {b_say}", color="green")
        a_say = llm.chat_with_context(b_say, ctx="bot_a")
        printc(f"A: {a_say}", color="blue")

def example_interactive_chat():
    agent = init_agent()
    agent.interactive()
    
def example_agent_basic():
    agent = init_agent()
    print("先不用工具计算")
    agent.chat("123+456*789=?")

    print("用工具numexpr计算")
    agent.register_tool(lambda expr: numexpr.evaluate(expr),
                    name = "expr_calc",
                    tool_desc = "计算数学表达式",
                    para_desc = {
                        "type": "object",
                        "properties": {
                            "expr": {"type": "string",
                                    "description": "数学表达式"},
                        },
                        "required": ["expr"]
                    })
    agent.chat("123+456*789=?")

def example_agent_25():
    agent = init_agent()
    agent.register_tool(lambda expr: numexpr.evaluate(expr),
                    name = "expr_calc",
                    tool_desc = "计算数学表达式",
                    para_desc = {
                        "type": "object",
                        "properties": {
                            "expr": {"type": "string",
                                    "description": "数学表达式"},
                        },
                        "required": ["expr"]
                    })
    agent.chat("3 3 7 7 四个数字，通过四则运算，得出25")


if __name__ == "__main__":
    # example_hello_world()
    # example_bots_chat()
    # example_agent_basic()
    # example_interactive_chat()
    example_agent_25()