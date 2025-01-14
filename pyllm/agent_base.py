from pyllm.llm import LLM
import logging
from prompt_toolkit import PromptSession  
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory  
from prompt_toolkit.completion import WordCompleter

FUNCTION_CALL_MAX_LOOP = 20

class AgentBase(object):
    "基础智能体"

    def __init__(self, model=None, ak = None, url = None, system="", child_agents=[], maxloop=FUNCTION_CALL_MAX_LOOP ):
        self.llm = LLM(model=model, ak=ak, url=url)
        self.model = model
        self.system_prompt = system
        self.context = {}
        self.maxloop = maxloop
        self.name = self.__class__.__name__.lower()
        self.desc = self.__class__.__doc__
        self.perpare_child_agent(child_agents)
        self.perpare_tool()
        
    def perpare_tool(self):
        # 这只是一个例子，实际使用时请替换为实际的工具函数
        self.register_tool(lambda input_str: input_str,
                           name = "echo",
                           tool_desc = "回声",
                           para_desc = {
                               "type": "object",
                               "properties": {
                                   "input_str": {"type": "string",
                                            "description": "输入"},
                               },
                               "required": ["input_str"]
                           })
    
    def register_tool(self, function,name=None, tool_desc=None, para_desc={}):
        self.llm.register_tool( function,name=name, tool_desc=tool_desc, para_desc=para_desc)
    

    def perpare_child_agent(self, child_agents):
        for agent in child_agents:
            self.register_child_agent(agent)

    def register_child_agent(self, agent):
        self.register_tool(lambda text: agent.chat(text),
                           name=agent.name,
                           tool_desc=agent.desc,
                           para_desc={"type": "object",
                                      "properties": {
                                          "text": {"type": "string",
                                                   "description": "使用自然语言来提问，会返回自然语言的回答"},
                                      },
                                      "required": ["text"]
                                      })
        
    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def ask(self,text, stream=False):
        return self.llm.using_tool(text, maxloop= self.maxloop, stream=stream)
    
    def chat(self, text, ctx="default", stream=False, style="colorful"):
        if ctx not in self.context:
            self.context[ctx] = [{
                "role": "system",
                "content": self.system_prompt}]
        msg = self.context[ctx]
        logging.debug(f"context: {msg}")
        msg.append({
            "role": "user",
            "content": text})
        msg_withouttool = [m for m in msg if m["role"] != "tool"]
        answer,function_call_history = self.llm.using_tool(messages=msg_withouttool, maxloop= self.maxloop, stream=stream, style=style)
        msg.append({
            "role": "tool",
            "content": function_call_history,
        })
        msg.append({
            "role": "assistant",
            "content": answer})
        return answer,function_call_history

    def interactive(self, prompt_index = ">>> "):
        history = InMemoryHistory()
        history.append_string("agent")
        keywords = []
        for i in self.llm.tools:
            keywords.append(i)
        agents_completer = WordCompleter(keywords)
        
        session = PromptSession(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
        )

        while True:
            try:
                text = session.prompt(prompt_index,completer=agents_completer)
            except EOFError:
                break
            if text == "exit":
                break
            self.chat(text)
