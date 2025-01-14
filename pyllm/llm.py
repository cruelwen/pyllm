import os
import logging
from openai import OpenAI
from pyllm.utils import pretty, truncate_string,printc
import copy
import json

FUNCTION_CALL_MAX_LOOP = 20

class OpenAIInitializationError(Exception):
    pass

class LLM:
    def __init__(self, model=None, ak=None, url=None, system = ""):
        if model is None:
            self.default_model = "gpt-4o"   # 修改为 self.default_model
        else:
            self.default_model = model     # 确保 model 被赋值给 self.default_model
        self.init_openai(ak, url)
        self.system = system
        self.context = {}
        self.tools = {}
    
    def init_openai(self, ak=None, url=None):
        if ak is None:
            api_key = os.environ.get("OPENAI_API_KEY", None)
            if api_key is None:
                logging.error("找不到API-KEY")
                raise OpenAIInitializationError("API-KEY not found")
        else:
            api_key = ak
        if url is None:
            api_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/")
        else:
            api_url = url
        logging.debug(f"api_key: {api_key}, api_url: {api_url}")
        try:
            self.openai = OpenAI(
                api_key=api_key,
                base_url=api_url,
            )
        except Exception as e:
            logging.error(f"初始化openai失败，{e}")
            raise OpenAIInitializationError(f"OpenAI initialization failed: {e}")
        return self.openai

    def chat_with_context(self, question, ctx="default", model=None):
        if model is None:
            model = self.default_model
        if ctx not in self.context:
            logging.debug(f"context {ctx} not found, create a new one")
            self.context[ctx] = []
        messages = self.context[ctx]
        messages.append({
            "role": "user",
            "content": question})
        answer = self.chat(messages, model=model)
        messages.append({
            "role": "assistant",
            "content": answer})
        return answer
    
    def ask(self, prompt, model=None):
        msg = [{"role": "user", "content": prompt}]
        return self.chat(msg, model=model)
    
    def chat(self, messages, model=None):
        """
        向指定的模型发送问题并返回答案。
        Args:
            messages (dict): 待询问的问题，模型上下文。
            model (str, optional): 模型名称，默认为None。如果未指定，则使用默认模型。
        Returns:
            str: 模型的回答。
        """
        if model is None:
            model = self.default_model
        response = self.openai.chat.completions.create(
            model=model, messages=messages)
        logging.debug(f"reponse content {str(response)}")
        answer = response.choices[0].message.content
        logging.debug(f"answer by {model}, {answer}")
        return answer

    def register_tool(self, function, name=None, tool_desc=None, para_desc={}):
        if name is None:
            name = function.__name__
        if tool_desc is None:
            tool_desc = function.__doc__
            
        self.tools[name] = {
            "name": name,
            "function": function,
            "tool_desc": tool_desc,
            "para_desc": para_desc
        }
    
            
    def using_tool(self, question=None, messages=None, model=None, maxloop=FUNCTION_CALL_MAX_LOOP, stream=False, style = "colorful"):
        """
        调用外部工具。
        
        Args:
            question (str): 待询问的问题。
            messages (list, optional): 消息列表，默认为None。如果未指定则按question提问。
            model (str, optional): 模型名称，默认为None。如果未指定，则使用默认模型。
            
        Returns:
            tuple: 模型的回答和函数调用历史。
        """
        
        if model is None:
            model = self.default_model
        
        messages = self._prepare_messages(question, messages)
        tools = self._prepare_tools()
        
        function_call_loop = 0
        function_call_history = []
        
        while function_call_loop < maxloop:
            function_call_loop += 1
            printc(f"## 开始第{function_call_loop}轮迭代...", "yellow", style=style)
            
            answer, tool_calls, response_message = self.function_call(model, messages, tools, stream=stream, style=style)
            messages.append(response_message)
            
            # 如果模型响应没有tool_calls，则说明循环结束，返回结果。
            if not tool_calls:
                return answer, function_call_history
            
            for tool_call in tool_calls:
                self._handle_tool_call(tool_call, function_call_history, messages)
        
        printc("超过最大迭代轮次，尚未完成，当前的进展","red", style=style)
        printc(answer, "green", style=style)
        logging.info(f"Exceed max loop, answer: {answer}, function_call_history: {function_call_history}")
        return answer, function_call_history

    def _prepare_messages(self, question, messages):
        if messages is None or not messages:
            if question is None:
                logging.error("No question provided.")
                return None
            messages = [{"role": "user", "content": question}]
        else:
            messages = copy.deepcopy(messages)
        return messages

    def _prepare_tools(self):
        tools = []
        for tool_name, tool_info in self.tools.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_info['name'],
                    "description": tool_info["tool_desc"],
                    "parameters": tool_info["para_desc"],
                }
            })
        return tools

    def function_call(self, model, messages, tools, stream=False, style="colorful"):
        if not stream:
            response = self.openai.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
            )
            response_message = response.choices[0].message
            answer = response_message.content
            if answer:
                printc(answer, "green", style=style)
            tool_calls = []
            if response_message.tool_calls:
                for tool in response_message.tool_calls:
                    printc(f'模型申请运行：{tool.function.name}{truncate_string(tool.function.arguments.replace("{", "(").replace("}", ")"), 100)}', style=style)
                    tool_calls.append({
                        "id": tool.id,
                        "function": {
                            "name": tool.function.name,
                            "arguments": tool.function.arguments,
                        }
                    })
            response_message_dump = response_message.model_dump()
            logging.info(f"tool choice:{pretty(response_message_dump)}")
            return answer, tool_calls, response_message
        else: 
            # 流式调用和打印输出
            stream = self.openai.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                stream=True
            )
            tool2call = {}
            answer = ""
            truncate_len = 100
            first = True
            for chunk in stream:
                chunk_message = chunk.choices[0].delta.content
                if chunk_message is not None:
                    answer += chunk_message
                    printc(chunk_message, "green", end="", style=style)
                    first = False
                delta_tool_calls = chunk.choices[0].delta.tool_calls
                if delta_tool_calls is not None:
                    for i in delta_tool_calls:
                        index = i.index
                        function_id = i.id
                        function_name = i.function.name
                        function_params = i.function.arguments
                        if index not in tool2call:
                            tool2call[index] = ({"id": function_id, "name": function_name, "params": function_params})
                            if not first:
                                printc(style=style) 
                            printc(f'模型申请运行: {tool2call[index]["name"]}', end="", style=style)
                            first = False
                        else:
                            tool2call[index]["params"] += function_params
                            if truncate_len > 0 :
                                if len(function_params) > truncate_len:
                                    to_print = function_params[:truncate_len]
                                    truncate_len = 0
                                else:
                                    to_print = function_params
                                    truncate_len -= len(function_params)
                                printc(to_print.replace("{","(").replace("}",")"), end="", style=style)
                                if truncate_len <= 0:
                                    printc("...", end="", style=style)
            printc("", style=style)
            tool_calls = []
            for index in tool2call:
                tool_calls.append({
                    "id": tool2call[index]["id"],
                    "function": {
                        "name": tool2call[index]["name"],
                        "arguments": tool2call[index]["params"]
                    },
                    "type": "function",
                })
            response_message = {
                "role": "assistant",
                "content": answer,
                "refusal": None,
                "function_call": None,
                "tool_calls": tool_calls
            }
            logging.debug(f"tool choice:{pretty(response_message)}")
            return answer, tool_calls, response_message
            

    def _handle_tool_call(self, tool_call, function_call_history, messages):
        try:
            tool_name = tool_call["function"]["name"]
            para = self._parse_parameters(tool_call["function"]["arguments"])
            
            if tool_name not in self.tools:
                logging.error(f"Tool not found: {tool_name}")
                raise Exception(f"Tool not found: {tool_name}")
            
            logging.info(f"Running tool: {tool_name}({para})")
            tool_function = self.tools[tool_name]["function"]
            result = tool_function(**para)
            
            function_call_history.append({"call": f"{tool_name}({para})", "result": truncate_string(str(result), 256)})
            
            messages.append({
                "tool_call_id": tool_call.get("id"),
                "role": "tool",
                "name": tool_name,
                "content": str(result),
            })
            
        except Exception as e:
            function_call_string = f"{tool_name}({para})"  # Assume para is string or can be converted to string
            logging.error(f"Function call error:function is {function_call_string}, error is  {e}")
            function_call_history.append({"call": function_call_string, "result": str(e)})
            messages.append({
                "tool_call_id": tool_call.get("id"),
                "role": "tool",
                "name": tool_name,
                "content": f"Function call error: {e}",
            })

    def _parse_parameters(self, arguments):
        try:
            return json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            return arguments  # Return original if not a JSON string or other error occurs
