import requests
import re

class SimpleOpenaiAPI:
    def __init__(self, server, key, model = None):
        self.model = model
        self.url = server
        self.key = key

    def chat(self, request: str, system: str, temp = 0.9, max_new_tokens = 50000) -> str:
        headers = {
            "Authorization": f"Bearer {self.key}", 
            "Content-Type": "application/json"
        }
        json = {
            "max_completion_tokens": max_new_tokens,
            "temperature": temp,
            "messages": [],
            #"chat_template_kwargs": {
            #    "enable_thinking": False,
            #}
        }
        if self.model is not None:
            json["model"] = self.model
            json["reasoning_effort"] = "low"
            json["temperature"] = 1
        else:
            json["reasoning"] = {"effort": "none"}
            json["enable_thinking"] = False
            json["reasoning_effort"] = "none"
            json["chat_template_kwargs"] = {"enable_thinking": False,}

        json["messages"].append({"role": "system", "content": f"{system}"})
        json["messages"].append({"role": "user", "content": f"{request}"})

        reply = requests.post(self.url, headers=headers, json=json)
        if reply.status_code != 200:
            raise Exception(f"{reply.reason}: {reply.text}")
        
        json = reply.json()

        content = json["choices"][0]["message"]["content"]
        if json["choices"][0]["finish_reason"] != "stop":
            print(f"finish reason != stop, is:'{json["choices"][0]["finish_reason"]}'")
        return content
    
    def alternativePhrasing(self, task : str) -> list[str]:
        system = """

You are tasked with generating **three paraphrased versions** of a given task command.

Your input will be a **single task command**.
Your output must be **a single Markdown list** containing **three alternative phrasings** of that command **and nothing else**.

---

### **Guidelines**

* **Complexity gradient:**

  * The **first paraphrase** should use the **most complex or formal** sentence structure.
  * Each subsequent paraphrase should become **progressively simpler and more natural**.

* **Content preservation:**

  * Keep all **entities, objects, and locations exactly the same** (e.g., “coke” must remain “coke”).
  * You may **restructure the sentence** as long as meaning and entities are preserved.

* **Tone and style:**

  * Maintain a **natural, conversational tone** write as if real people might say it.
  * Avoid robotic or overly formal phrasing unless required for the most complex version.


"""
# * Maintain a natural tone — write like people actually talk.


        reply = self.chat(task, system)
        alternatives = []
        for line in reply.splitlines():
            if line == "":
                continue
            if line.startswith("- "):
                alternatives += [line.removeprefix("- ")]
            elif line.startswith("* "):
                alternatives += [line.removeprefix("* ")]
            elif re.match(r"[1-9]+\.", line):
                alternatives += [re.sub(r"[1-9]+\.", '', line)]
            else:
                print(f"Error reply line: '{line}'")
                print(f"\t full reply was {reply}")
                raise Exception("bad reply")
            
        return alternatives


if __name__ == '__main__':
    _host = "rhenium"
    _port = "9090"
    _key = "tiago"
    llm = SimpleOpenaiAPI(f"http://{_host}:{_port}/v1/chat/completions", f"{_key}")

    tasks = [
        "Find Apple in Kitchen, place it on Drawer", 
        "Tell the gesture of the person at the kitchen table to the person at the bed", 
        "Tell me what is the smallest food on the sink"
    ]

    for task in tasks:
        print(f"Task: '{task}'")
        alternatives = llm.alternativePhrasing(task)
        for a in enumerate(alternatives):
            print(a)
    

