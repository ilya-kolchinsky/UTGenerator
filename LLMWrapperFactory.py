from LLMWrapper import *
from sanity.DummyLLMWrapper import DummyLLMWrapper
from chat_gpt.ChatGPTWrapper import ChatGPTWrapper


class LLMWrapperFactory(object):

    @staticmethod
    def create_llm_wrapper(subclass_name):

        # assuming subclass_name is a subclass of LLMWrapper that is defined in an imported module
        try:
            subclass = globals()[subclass_name]
            return subclass()
        except ImportError:
            print(f"Unknown LLM type: {subclass_name}")
            raise
