import subprocess

# Define the range of parameters
num_pairs = 10  # change to how many pairs you want

for i in range(1, num_pairs + 1):
    n = i
    x = i+1
    print(f"Running: python a.py {n} {x}")
    
    # Run the script with parameters
    result = subprocess.run(["python", "sender_yolo_fat.py", str(n), str(x)])
    
    # Optionally, check the return code
    if result.returncode != 0:
        print(f"Script failed for parameters n={n}, x={x}")
