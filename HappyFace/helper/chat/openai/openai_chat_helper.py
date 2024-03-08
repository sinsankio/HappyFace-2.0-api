import pickle

import openai


class OpenAiChatHelper:
    INIT_PROMPT = "Name: {}, Address: {}, Gender: {}, Hidden Diseases: {}, Salary: ${}, " \
                  "Num. Family Members: {}, Monthly Cumulative Income: ${}, Monthly Cumulative Expenses: ${}, " \
                  "Num. Occupations within Family: ${}, Family Category: {}, Emotion: {}"

    @staticmethod
    def validate_user_message(chat_model: str = "gpt-3.5-turbo", message: str = None) -> bool | None:
        if message:
            with open("helper/chat/openai/validity_prompt.pkl", "rb") as validity_prompt_file:
                validity_prompts = pickle.load(validity_prompt_file)
            validity_prompts.append({"role": "user", "content": message})

            try:
                completion = openai.ChatCompletion.create(
                    model=chat_model,
                    messages=validity_prompts,
                    temperature=0
                )
                return bool(int(dict(completion.choices[0].message)["content"]))
            except Exception:
                return

    @staticmethod
    def get_assistant_response(chat_model: str = "gpt-3.5-turbo", conversation: list = None) -> str | None:
        if conversation:
            with open("helper/chat/openai/sys_prompt.pkl", "rb") as sys_prompt_file:
                sys_prompts = pickle.load(sys_prompt_file)
            sys_prompts.extend(conversation)

            try:
                completion = openai.ChatCompletion.create(
                    model=chat_model,
                    messages=sys_prompts,
                    temperature=0
                )
                return str(dict(completion.choices[0].message)["content"])
            except Exception:
                return
