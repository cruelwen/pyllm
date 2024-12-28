import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pyllm.llm import LLM
from pyllm.agent_base import AgentBase

llm = LLM(model="qwen-plus",ak="sk-3067acd513f54db3a2c14f0718df071f",url="https://dashscope.aliyuncs.com/compatible-mode/v1")

answer = llm.ask("Hello, world")
print(answer)

agent = AgentBase(model="qwen-plus",ak="sk-3067acd513f54db3a2c14f0718df071f",url="https://dashscope.aliyuncs.com/compatible-mode/v1")
agent.chat("Hello, world")