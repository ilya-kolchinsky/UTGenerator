from LLMWrapper import *
from sanity.DummyLLMWrapper import DummyLLMWrapper
from chat_gpt.ChatGPTWrapper import ChatGPTWrapper


class LLMWrapperFactory(object):

    @staticmethod
    def create_llm_wrapper(llm_type):

        wrapper_subclass_name = f"{llm_type}Wrapper"

        # assuming wrapper_subclass_name is a subclass of LLMWrapper that is defined in an imported module
        try:
            subclass = globals()[wrapper_subclass_name]
            return subclass()
        except ImportError:
            print(f"Unknown LLM type: {wrapper_subclass_name}")
            raise
