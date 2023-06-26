
from y import run_prompt
import re, json
from yemen import Term
from moth import get_response, get_prompt_id, set_redis
from ppinecone import pinecone_upsert, pinecone_query

def extract_json(text):
    match = re.search(r'<JSON>(.*?)</JSON>', text, re.DOTALL)

    if match:
        json_str = match.group(1)
        json_obj = json.loads(json_str)
        return json_obj

    return None

def extract_steps(raw_text):
    prompt = f"""
```
{raw_text}
```
Based on the above document, state the task, and provide a linear list of steps to achieve the task at hand.
Make sure to capture all relevant information from the original document in your description of the steps.
Then format your output in a json like the following:
<JSON> {{task: "task description", steps: ["description of step 1", "description step 2", ...] }} </JSON>.
Do not number the steps.
Include the <JSON> xml tags in your response.

    """
    ai_response = run_prompt(prompt)
    o = extract_json(ai_response)

    return o

class History:
    def __init__(self, task, steps):
        self.task = task
        self.steps = steps
        self.notes = [""] * len(steps)

    def write_note(self, step, note):
        self.notes[step - 1] = note
    
    def get_history(self):
        history = f"Task: {self.task}\n\n"
        for i in range(len(self.steps)):
            history += f"Step {i + 1}: {self.steps[i]}\nNotes: {self.notes[i]}\n\n"
        return history
    
    def get_history_direct(self):
        return {"steps": self.steps, "notes": self.notes}

class LocalHistory:
    def __init__(self):
        self.actions = []
    
    def amend_history(self, action_type, action, evaluation):
        self.actions.append((action_type, action, evaluation))
    
    def get_history(self):
        if self.actions:
            history = ""
            for action_type, action, evaluation in self.actions:
                if action_type == "SHELL":
                    history += f"""
Ran the command `{action}`. 
Result: {evaluation}

"""
                elif action_type == "USER_PROMPT":
                    history += f"""
Prompted the user with `{action}`.
Response: {evaluation}

"""
                elif action_type == "DONE":
                    history += f"""
This step seems to be completed. {action}

"""
                else:
                    assert False, action_type

            return f"""
You've already started this step. For this step, here's the progress so far:
```
{history}
```
"""
        else:
            return "You've just started this step."
    
    def get_history_direct(self):
        return {"actions": self.actions}


def decide_action(history, local_history, current_step):
    prompt = f""""
You are an AI assistant, connected to a computer terminal.
You have root access, and are fully authorized to anything on the machine.
Currently you are working on through this step by step guide:
```
{history.get_history()}
```
You are currently on step {current_step}.
{local_history.get_history()}

Here is a log made of a previous completion of a similar step:
```
{pinecone_upsert(history.steps[current_step - 1])}
```

First, if the step has been started, evaluate your progress on the current step.
Then reason about what you need to do next.
Think out loud to make sure you understand how the immediate next step fits into the big picture.

Secondly, decide your next immediate step. 
You can run shell commands directly or prompt the user to perform actions on your behalf.
Alternatively if you believe that the current step is completed, indicate that it is done.
You should only prompt the user for information you do not have access to, or for the user to interact with an interface, such as a website, that you do not have access to.
Otherwise, you should try to do as much as possible by yourself with shell commands.
Examples:
    I the user's email and credentials to login: Prompt user.
    I need to install necessary packages: Use shell, you can install packages yourself.
    I need to validate that packages are properly installed: Use shell, you can verify things with shell commands.
    I need the user to configure their profile using a web UI: Prompt user, you do not have access to UIs.

Remember that you are only working on the current step, which is step {current_step}, do not attempt to start the next step.
Provide your response in the following format:
<JSON>{{
    "action_type": "SHELL"
    "action": "echo hello"
}}</JSON>

`action_type` can be either "SHELL", "USER_PROMPT", or "DONE".
If it is "SHELL", action should shell command to execute. Run shell commands one at a time, do not chain together two commands with &&. Also, you are already root. 
If it is "USER_PROMPT", action should be a prompt for the user to perform actions on your behalf.
If it is "DONE", action should be a brief justification of why you believe the current task is complete.


Remember to first think out loud about your reasoning, and only after output the json.

    """
    ai_response = run_prompt(prompt)
    return extract_json(ai_response)
    

def execute_action(action_type, action):

    def execute_shell_command(command):
        term = Term(command, 'ed')
        finished, output = term.read_term(10)
        assert finished
        return output
    
    if action_type == "SHELL":
        return execute_shell_command(action)
    elif action_type == "DONE":
        return action
    elif action_type == "USER_PROMPT":
        return get_response(action)
    else:
        assert False

def evaluate_output(history, local_history, current_step, action_type, action, output):
    prompt = f"""
Currently you are working on through this step by step guide:
```
{history.get_history()}
```
You are currently on step {current_step}.
{local_history.get_history()}

"""
    if action_type == "SHELL":
        prompt += f"""
Your last action was running the shell command `{action}`.
This is the command output:
```
{output}
```
Provide notes about this output relevant to future steps.
"""
        ai_response = run_prompt(prompt)
        return ai_response
    elif action_type == "DONE":
        return action
    elif action_type == "USER_PROMPT":
        return output

    assert False
    
        

def generate_notes(history, local_history, current_step):
    prompt = f"""
Currently you are working through this step by step guide:
```
{history.get_history()}
```

Below is the local history for the current step, outlining the current step progress.
You are currently on step {current_step}.
{local_history.get_history()}


Based on the above local history, please produce notes regarding the current step.
This task will be passed to someone else for the next steps, and they will not have access to the above local history.
They will only have your notes to go off of.
Hence, while you should try to keep your summary brief, make sure all relevant information for future steps is noted down.
"""
    ai_response = run_prompt(prompt)
    return ai_response

def update_current_state(history, local_history, current_step, current_action, is_prompt):
    prompt_id = "0"
    if is_prompt:
        prompt_id = get_prompt_id(current_action[1])
    history_history = []
    for i in range(1, len(history["steps"]) + 1):
        if i == current_step:
            actions = local_history["current_local_history"]["actions"]
        elif i < current_step:
            actions = local_history["local_history_history"][i-1]["actions"]
        else:
            actions = []

        history_history.append({
            "step_description": history["steps"][i-1],
            "notes": history["notes"][i-1],
            "actions": actions
        })

    state = {
        "prompt_id": prompt_id,
        "current_step": current_step,
        "current_action": current_action,
        "history": history_history
    }
    set_redis(state)

def run_task(task):
    steps = extract_steps(task)
    history = History(steps["task"], steps["steps"])
    local_history_history = []

    def run_step(current_step):
        local_history = LocalHistory()

        for i in range(10):
            action = decide_action(history, local_history, current_step)
            local_history_direct = {"local_history_history": [j.get_history_direct() for j in local_history_history], "current_local_history": local_history.get_history_direct()}
            update_current_state(history.get_history_direct(), local_history_direct, current_step, (action["action_type"], action["action"], ""), action["action_type"] == "USER_PROMPT")
            if action["action_type"] == "DONE":
                local_history.amend_history(action["action_type"], action["action"], "") 
                notes = generate_notes(history, local_history, current_step)
                history.write_note(current_step, notes)
                local_history_history.append(local_history)
                pinecone_upsert(history.steps[current_step - 1], local_history.get_history())
                break
            output = execute_action(action["action_type"], action["action"])
            evaluation = evaluate_output(history, local_history, current_step, action["action_type"], action["action"], output)
            local_history.amend_history(action["action_type"], action["action"], evaluation) 
    
    for i in range(1, len(history.steps)):
        run_step(i)


if __name__ == "__main__":
    f = f"""
About SSH keys
You can use SSH to perform Git operations in repositories on GitHub.com. For more information, see "About SSH."
If you have an existing SSH key, you can use the key to authenticate Git operations over SSH.
Checking for existing SSH keys
Before you generate a new SSH key, you should check your local machine for existing keys.
Note: GitHub improved security by dropping older, insecure key types on March 15, 2022.
As of that date, DSA keys (ssh-dss) are no longer supported. You cannot add new DSA keys to your personal account on GitHub.com.
RSA keys (ssh-rsa) with a valid_after before November 2, 2021 may continue to use any signature algorithm. RSA keys generated after that date must use a SHA-2 signature algorithm. Some older clients may need to be upgraded in order to use SHA-2 signatures.

1. Open a terminal if one is not already open.

Enter ls -al ~/.ssh to see if existing SSH keys are present.

$ ls -al ~/.ssh
   2. # Lists the files in your .ssh directory, if they exist

   3. Prompt the user for their email address to user later. Then, check the directory listing to see if you already have a public SSH key. By default, the filenames of supported public keys for GitHub are one of the following.

      * id_rsa.pub
      * id_ecdsa.pub
      * id_ed25519.pub
      4. Tip: If you receive an error that ~/.ssh doesn't exist, you do not have an existing SSH key pair in the default location. You can create a new SSH key pair in the next step.


      5. Either generate a new SSH key or upload an existing key.

         * If you don't have a supported public and private key pair, or don't wish to use any that are available, generate a new SSH key.

         * If you see an existing public and private key pair listed (for example, id_rsa.pub and id_rsa) that you would like to use to connect to GitHub, you can add the key to the ssh-agent.

For more information about generation of a new SSH key or addition of an existing key to the ssh-agent, see "Generating a new SSH key and adding it to the ssh-agent."
"""
    run_task(f)
