import json

def add_indents(s, n=8):
    indentation = ' ' * n
    return '\n'.join(indentation + line for line in s.split('\n'))

def format_state(state):
    
    def format_action(action_tuple):
        action_type, action, evaluation = action_tuple
        f = ""
        if action_type == "SHELL":
            f += f"Running shell command: {action}\n"
        elif action_type == "USER_PROMPT":
            f += f"Prompting user: {action}\n"
        elif action_type == "DONE":
            f += f"Completed step. {action}\n"

        if evaluation:
            f += f"{evaluation}\n"

        return f

    f_current = f"""
Current step: {state["current_step"]}
{add_indents(format_action(state["current_action"]))}
"""
    f_history = ""
    for i, step in enumerate(state["history"]):
        if i + 1 == state["current_step"]:
            f_history += "[ IN PROGRESS ] "
        elif i + 1 < state["current_step"]:
            f_history += "[ COMPLETE ]    "
        else:
            f_history += "[ QUEUED ]      "

        f_history += f"Step {i + 1}: {step['step_description']}\n"

        k = "\n".join([format_action(a) for a in step["actions"]])
        f_history += add_indents(k)
        f_history += "\n\n"
    
    return (f_current, f_history, state["prompt_id"])





j = {
	"current_action": [
		"DONE",
		"Existing SSH key pair found in Step 2, no need to generate a new key. Proceed to Step 5.",
		""
	],
	"current_step": 4,
	"history": [
		{
			"actions": [
				[
					"DONE",
					"Terminal access already available",
					""
				]
			],
			"notes": "Step 1: Open a terminal\nNotes: Terminal access is already available. This step is completed. Proceed to Step 2.",
			"step_description": "Open a terminal"
		},
		{
			"actions": [
				[
					"SHELL",
					"ls -al ~/.ssh",
					"Notes: The output shows that there is an existing SSH key pair (id_rsa and id_rsa.pub) in the .ssh directory. This means we can proceed to Step 5 to add the key to the ssh-agent. No need to generate a new SSH key in Step 4."
				],
				[
					"DONE",
					"Existing SSH key pair found, proceeding to Step 5.",
					""
				]
			],
			"notes": "Notes for Step 2:\n\n- Ran the command `ls -al ~/.ssh`.\n- The output shows an existing SSH key pair (id_rsa and id_rsa.pub) in the .ssh directory.\n- No need to generate a new SSH key in Step 4.\n- Proceed to Step 5 to add the key to the ssh-agent.",
			"step_description": "Enter ls -al ~/.ssh to check for existing SSH keys"
		},
		{
			"actions": [
				[
					"DONE",
					"Existing SSH key pair found in Step 2, no need to check for other supported public key filenames.",
					""
				]
			],
			"notes": "Notes for Step 3:\n\n- In Step 2, an existing SSH key pair (id_rsa and id_rsa.pub) was found in the .ssh directory.\n- Since the existing key pair is already in a supported format, there is no need to check for other supported public key filenames in this step.\n- Proceed to Step 5 to add the key to the ssh-agent, as generating a new SSH key in Step 4 is not needed.",
			"step_description": "Check the directory listing for supported public key filenames (id_rsa.pub, id_ecdsa.pub, id_ed25519.pub)"
		},
		{
			"actions": [],
			"notes": "",
			"step_description": "If no existing key pair is found, generate a new SSH key"
		},
		{
			"actions": [],
			"notes": "",
			"step_description": "If an existing key pair is found, add the key to the ssh-agent"
		}
	],
	"prompt_id": "0"
}

# a, b = format_state(j)

# print(a)
# print(b)