
import re
from y import run_prompt
from yemen import Term, FileWrite

def extract_tag(input_string):
    # regex pattern to extract xml tag
    pattern = r'<(\w+)(\s*/>|>(.*?)</\1>)'
    match = re.search(pattern, input_string, re.DOTALL)

    # return None if no match found
    if match is None:
        return None

    tag_name = match.group(1)

    # check if the tag is self-closing or has a closing tag
    if match.group(2).startswith('/'):
        # self-closing tag
        return (tag_name, "")
    else:
        # tag with closing tag
        content = match.group(3)
        return (tag_name, content.strip())


def make_plan(task, history):
    prompt = f"""
You are connected to a terminal on an ubuntu machine as root.
Your task is: {task}
Here is a history log of what happened so far: 
```
{history}
```

First, outline a rough plan of the next steps you would take from here in order to achieve your task.
Additionally, make sure that you validate the completion of the task. You should include validation criteria in your outline.

Consider carefully the history so far as to not do repeat past mistakes or perform redundant actions.

Then, give a detailed description of your immediate next step.
Format this detailed description inside like so: <NEXT_STEP> [description] </NEXT_STEP>
If you want to write to a file, provide the contents in your description.

If based on the history log, you are confident that the task is completed and validated, simply output <DONE/>.
"""

    ai_response = run_prompt(prompt)
    tag, content = extract_tag(ai_response)
    return (tag, content)

def extract_terminal_action(next_step):
    prompt = f"""
You are connected to a terminal on an ubuntu machine as root.
You have been instructed to complete this task:
{next_step}

First figure out what shell commands you need to execute to achieve this task.
Output the first shell command to execute to achieve this task in the following format:
<SHELL> [ shell command ] </SHELL>
There may be multiple commands needed, but only select the first.
Make sure there is only a single command, do not connect together multiple commands with &.

If you want to write to a file, use the following format instead of a shell command:
<FILE>[ file path ]
[ file contents ]</FILE>
Do not attempt to write to a file by redirecting echo.

For example:
<FILE>hello.py
if __name__ == \"__main__\":
    print(\"hello\")<\FILE>

You may not open programs that are highly interactive like text editors.
"""
    ai_response = run_prompt(prompt)
    tag, content = extract_tag(ai_response)
    return (tag, content)

def evaluate_result(plan, local_history, output):
    prompt = f"""
You are trying to:
{plan}
Here is what you've done so far:
{local_history}
Here is the current state of the terminal:
```
{output[-5000:]}
```

Evaluate the results of the output the last command, beginning each sentence with "It seems that...". Format your evaluation as <RESULT> [evaluation of results] </RESULT>.
Example 1:
```
root@7c586fef0ddd:/app# python3 -m http.server 80 &
[1] 908
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
```
<RESULT>It seems that an http python server is running on 0.0.0.0 port 80. It seems that the last command was successful.</RESULIT>

Example 2:
```
root@5d268fcc169e:/app# pip install flask
bash: pip: command not found
```
<RESULT>It seems that pip is not installed. It seems that the last command was unsuccessful.</RESULT>
"""
    ai_response = run_prompt(prompt)
    tag, content = extract_tag(ai_response)
    return content

def handle_interaction(task, local_history, output):
    prompt = f"""
We are connected to a terminal on an ubuntu machine as root.
We have been instructed to complete this task:
{next_step}
Here is a history of what has happened so far:
{local_history}

Here is the current state of the terminal:
```
{output[-5000:]}
```

Based on this information, first decide if you should wait for the current program to make more progress in its execution or if user interaction is required.
If user interaction is required, what are the exact keystrokes we should send?
If we should wait, output <WAIT/>.
If user interaction is required, output <INTERACT> [ input ] </INTERACT>, where the input is the exact keystroke we should send. If we should press enter at the end, make sure you end the interaction with a new line.
Do not attempt to run the next command, only interact if the current running program needs user interaction.

Example:
    Proceed with installation? [Y/n]
    <INTERACT>Y\\n</INTERACT>
"""
    ai_response = run_prompt(prompt)
    tag, content = extract_tag(ai_response)
    return (tag, content)

def simple_summary(content):
    prompt = f"""
Give a high level description of the contents of the following file in 1 or 2 sentences.
```
{content}
```
"""
    return run_prompt(prompt)

# task = "In the simplest way possible, make it such that when I curl localhost, \"hello\" is returned."
task = "Get a flask echo server running on localhost."
# task = "Create a file with a bunch of special characters written to it, one that might be used to check edge cases for string escaping. Special characters should be written to the files contents."
history = "You are on a completely fresh ubuntu installation. You have bash open as root.\n"

def amend_history(term_action, result):
    return history + f"""
Ran command: {term_action}
Result: {result}
"""

def write_string_to_file(filename, string):
    with open(filename, 'w') as f:
        f.write(string)

def show_curr(next_step, term_action, output):
    l = f"""
===== Current step:
{next_step}
===== Current shell command:
{term_action}
===== Current terminal output:
{output}
    """
    write_string_to_file("term.txt", l)


container = '033'

for i in range(100):
    write_string_to_file("history.txt", history)
    done, next_step = make_plan(task, history)
    if done == "DONE":
        print("FINISHED")
        break
    print(next_step)
    action_type, action_value = extract_terminal_action(next_step)
    if action_type == "SHELL":
        term_action = action_value
        print(term_action)
        term = Term(term_action, container)
        local_history = f"You have run the command `{term_action}`."
        while True:
            finished, output = term.read_term()
            show_curr(next_step, term_action, output)
            # print((finished, output))
            if finished:
                break
            action, term_input = handle_interaction(next_step, local_history, output) 
            print(action)
            if action == "INTERACT":
                term.send_interaction(term_input)
            elif action == "WAIT":
                continue
            else:
                assert False
        result = evaluate_result(next_step, local_history, output)
        history = amend_history(term_action, result)
    elif action_type == "FILE":
        path, content = action_value.split('\n', 1)
        f = FileWrite(path, content, container)
        finished, output = f.read_term(10)
        if output:
            history += f"""
Tried writing to the file {path} but the path does not exist.
"""
        else:
            history += f"""
Wrote to file: {path}.
Description: {simple_summary(content)}
"""

else:
    print("GAVE UP")