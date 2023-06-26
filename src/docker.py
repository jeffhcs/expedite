import pexpect
import time
import base64

class DockerTerm:
    def __init__(self, command, container) -> None:
        wrapped_command = self.wrap_command(command, container)
        print(wrapped_command)
        self.child = pexpect.spawn(wrapped_command, encoding='utf-8')
        self.finished_output = None
    
    def wrap_command(self, command, container):
        return f"docker exec -it {container} bash -c \'echo \"{self.base64_encode(command)}\" | base64 --decode | bash\'"

    def base64_encode(self, input_string):
        # Convert the input string to bytes
        input_bytes = input_string.encode('utf-8')
        
        # Encode the bytes
        encoded_bytes = base64.b64encode(input_bytes)
        
        # Convert the encoded bytes back into a string
        encoded_string = encoded_bytes.decode('utf-8')
        
        return encoded_string

    def read_term(self, timeout=1):
        if self.finished_output is not None:
            return (True, self.finished_output)
        try:
            # Wait for EOF or 1 second to pass
            self.child.expect(pexpect.EOF, timeout=timeout)
            self.finished_output = self.child.before
            return (True, self.finished_output)
        except pexpect.TIMEOUT:
            # If a timeout occurred (i.e., 1 second passed without EOF), print the latest output
            return (False, self.child.before)
    

class Term(DockerTerm):
    def send_interaction(self, term_input):
        self.child.send(term_input)

class FileWrite(DockerTerm):
    def __init__(self, file_path, contents, container):
        command = f"echo {self.base64_encode(contents)} | base64 --decode > {file_path}"
        super().__init__(command, container)

if __name__ == "__main__":
    t = Term("echo hello", "033")
    print(t.read_term())
    f = FileWrite("/app/hello", "tf \"\' && $()", "033")
    print(f.read_term())
    t = Term("cat /app/hello", "033")
    print(t.read_term())
#     t.send_interaction("20 + 20\n")
#     print(t.read_term())
#     print(t.read_term())
#     t.send_interaction("exit()\n")
#     print(t.read_term())
#     print(t.read_term())