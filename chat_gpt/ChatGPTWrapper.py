import os
from dotenv import load_dotenv
import openai

from LLMWrapper import LLMWrapper


class ChatGPTWrapper(LLMWrapper):
    def _set_up(self):
        load_dotenv()
        api_key = os.environ["OPENAI_API_KEY"]
        self.__openai_client = openai.OpenAI(api_key=api_key)
        self.__saved_messages = []

    def execute_prompt(self, prompt, save_prompt_and_reply=False, use_history=False):
        # Note that we intentionally do not keep the message history unless specified otherwise.
        # While this could help improve the quality of replies, this way we hit the limit on the request size
        # very quickly. Instead, it is expected that the prompt parameter will contain all the necessary context.
        if save_prompt_and_reply:
            self.__saved_messages.append({"role": "user", "content": prompt})

        new_message = {"role": "user", "content": prompt}
        messages = self.__saved_messages+[new_message] if use_history else [new_message]
        completion = self.__openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        response = completion.choices[0].message.content
        if save_prompt_and_reply:
            self.__saved_messages.append({"role": "assistant", "content": response})
        return response
