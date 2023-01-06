import asyncio
import prompt_toolkit
import vcc

import pygments
from pygments.token import Token
from prompt_toolkit.formatted_text import PygmentsTokens,FormattedText
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import Completer, Completion

from pygments.lexers.python import Python3Lexer

import nest_asyncio
nest_asyncio.apply()

def print_highlight_text(text):
    tokens = list(pygments.lex(text, lexer=Python3Lexer()))
    prompt_toolkit.print_formatted_text(PygmentsTokens(tokens))

def run_async(func):
    return asyncio.new_event_loop().run_until_complete(func)

class RpcCompleter(Completer):
    def __init__(self,client:vcc.RpcExchanger):
        self.client=client
    def get_completions(self, document, complete_event):
        text=document.text.split(" ")
        if "/" not in text[0]:
            for i in run_async(self.client.rpc.rpc.list_providers()):
                if i.startswith(text[0]):
                    yield Completion(i,start_position=-len(text[0]))
        elif len(text)==1:
            #prompt_toolkit.print_formatted_text(111)
            servicename=text[0].split("/")[0]
            for i in run_async(self.client.rpc.rpc.list_services(name=servicename)):
                #prompt_toolkit.print_formatted_text(1)
                if i.startswith(text[0].split("/")[1]):
                    yield Completion(i)#,start_position=-len(text[0]))
class App:
    def __init__(self):
        self.client:vcc.RpcExchanger=vcc.RpcExchanger()
        self.completer=RpcCompleter(self.client)
        self.session=prompt_toolkit.PromptSession(completer=self.completer)
    def prase_param(self,input:str):
        output={}
        key=""
        value=""
        state="key"
        ignore=False
        for i in input:
            if state=="key":
                if i=="=" and not ignore:
                    state="value"
                    continue
                if i=="\\":
                    ignore=True
                    continue
                key+=i
                ignore=False
            if state=="value":
                if i=='"':
                    ignore=not ignore
                if i==" " and not ignore:
                    output[key]=value
                    key=""
                    value=""
                    state="key"
                    continue
                value+=i
        if key!="":
            output[key]=value
        return output
    async def run(self):
        with self.client:
            while 1:
                input=(await self.session.prompt_async("VCC>")).split(" ")
                param=self.prase_param(" ".join(input[1:]))
                if len(input[0].split("/"))==2:
                    try:
                        print_highlight_text((await self.client.rpc_request(input[0],param)).__repr__())
                    except vcc.UnknownError:
                        prompt_toolkit.print_formatted_text("A error from vcc rpc!")
if __name__=="__main__":
    asyncio.run(App().run())
