class LLMWrapper(object):

    def __init__(self):
        self._set_up()

    def _set_up(self):
        raise NotImplementedError()

    def execute_prompt(self, prompt, save_prompt_and_reply=False, use_history=False):
        raise NotImplementedError()
