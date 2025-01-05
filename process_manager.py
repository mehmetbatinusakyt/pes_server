import subprocess
from process_manager import ProcessManager

class ProcessManager:
    def __init__(self):
        self.processes = {}
        
    def start_process(self, process_name, command):
        """Start a new process with given name and command"""
        try:
            process = subprocess.Popen(command, shell=True)
            self.processes[process_name] = process
            return True
        except Exception as e:
            print(f"Error starting process {process_name}: {e}")
            return False
            
    def stop_process(self, process_name):
        """Stop a running process by name"""
        if process_name in self.processes:
            process = self.processes[process_name]
            process.terminate()
            process.wait()
            del self.processes[process_name]
            return True
        return False
        
    def list_processes(self):
        """Return list of running process names"""
        return list(self.processes.keys())
        
    def is_running(self, process_name):
        """Check if a process is currently running"""
        if process_name in self.processes:
            return self.processes[process_name].poll() is None
        return False

if __name__ == "__main__":
    pm = ProcessManager()
    port = pm.find_free_port()
    if port:
        # Използвайте свободния порт
        pass