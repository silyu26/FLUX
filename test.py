import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")

print(torch.version.cuda)   # e.g. '12.1'
print(torch.cuda.is_available())  # True
