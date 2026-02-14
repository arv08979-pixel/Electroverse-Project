import os

folder_path = "plates_folder_path"

batch_size = 5
plates_batches = {}   # final structure

# sort to match video grouping order
all_files = sorted(
    [f for f in os.listdir(folder_path)
     if os.path.isfile(os.path.join(folder_path, f))]
)

for i in range(0, len(all_files), batch_size):
    
    batch_files = all_files[i:i + batch_size]
    
    batch_plates = []   # array for this 5-video group
    
    for filename in batch_files:
        
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, "r") as f:
            for line in f:
                
                plate = line.strip()
                
                if plate:
                    batch_plates.append(plate)
    
    batch_name = f"batch_{i//batch_size + 1}"
    
    plates_batches[batch_name] = batch_plates
