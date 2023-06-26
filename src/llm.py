import os
import time
from langchain import OpenAI
from langchain.llms import AzureOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def add_indents(s, n=8):
    # Create a string of n spaces
    indentation = ' ' * n

    # Split the string into lines, add the indentation, then join it back together
    return '\n'.join(indentation + line for line in s.split('\n'))

def append_string_to_file(filename, string):
    with open(filename, 'a') as f:
        f.write(string + '\n')

gpt4 = AzureOpenAI(
    temperature=0,
    model_name="gpt-4",
    deployment_id="gpt-4",
    n=2,
)
gpt3 = OpenAI(temperature=0)
def run_prompt(prompt, gpt_version = 3):


    # llm = OpenAI(temperature=0)
   
    print(f"Prompting with: *****\n{add_indents(prompt)}\n<<<<<")
    start_time = time.time()
    result = gpt4(prompt)
    end_time = time.time()
    elapsed_time = end_time - start_time
    r = f"Response ({elapsed_time} seconds):\n{add_indents(result)}\n<<<<<"
    print(r)
    append_string_to_file("out.txt", r)
    return result

if __name__ == "__main__":
    print(run_prompt("What is yemen?"))
    print(run_prompt("Describe the first three images returned by google searching Yemen."))