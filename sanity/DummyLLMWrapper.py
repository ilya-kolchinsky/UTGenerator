from LLMWrapper import LLMWrapper
from UTGenerationPrompts import SKELETON_PROMPT_PREFIX, DESCRIPTION_PROMPT_PREFIX
from sanity.consts import *


class DummyLLMWrapper(LLMWrapper):

    def _set_up(self):
        pass

    def execute_prompt(self, prompt, save_prompt_and_reply=False, use_history=False):
        if prompt.startswith(SKELETON_PROMPT_PREFIX):
            # a prompt to write a unit test from scratch
            return SANITY_SKELETON_QUERY_REPLY

        if prompt.startswith(DESCRIPTION_PROMPT_PREFIX):
            # a prompt to create a description of positive/negative scenarios
            return SANITY_SCENARIO_DESCRIPTION_QUERY_REPLY

        # otherwise, we assume the prompt is for serving a selected scenario
        return SANITY_SINGLE_SCENARIO_QUERY_REPLY
