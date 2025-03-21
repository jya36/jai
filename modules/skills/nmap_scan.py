import subprocess
import os
def run_nmap(network:str) -> str:
    current_dir = os.getcwd()
    fileName = f"{current_dir}/nmap_scan_{network}.txt"
    cmd = ["nmap", "-sV", "-p 1-65535", f"-oN", fileName, network]
    print(cmd)
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return(fileName)

if __name__ == "__main__":
    run_nmap("192.168.1.99")


def read_results(filename:str) -> str:
    try:
        with open(filename, "r") as file:
            file_contents = file.read()
        return file_contents
    except:
        return "Unable to open file"