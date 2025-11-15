import os, struct

PAGE_SIZE = 4096  # Each page is 4 KB

# Create a Heap File

def create_heap_file(file_name):
    with open(file_name, 'wb') as f:  # Open in write-binary mode
        pass

# Read Page

def read_page(file_name, page_number):
    """Read a specific page (4 KB) from the heap file given the page number."""    
    file_size = os.path.getsize(file_name)
    last_page_number = file_size // PAGE_SIZE - 1
    
    if page_number > last_page_number:
        raise ValueError(f"Page {page_number} does not exist in the file.")

    with open(file_name, 'rb') as f:
        f.seek(page_number * PAGE_SIZE)
        page_data = f.read(PAGE_SIZE)
    return page_data

# Append Page

def append_page(file_name, page_data):
    """Appends the provided page data to the end of the file."""
    if len(page_data) != PAGE_SIZE:
        raise ValueError(f"Page data must be exactly {PAGE_SIZE} bytes.")
    with open(file_name, 'ab') as f:
        f.write(page_data)

# Write page

def write_page(file_name, page_number, page_data):
    """Write data to a specific page in the heap file."""
    file_size = os.path.getsize(file_name)
    last_page_number = file_size // PAGE_SIZE - 1
    if page_number > last_page_number:
        raise ValueError(f"Page {page_number} does not exist in the file.")
    if len(page_data) != PAGE_SIZE:
        raise ValueError(f"Data must be exactly {PAGE_SIZE} bytes long.")
    with open(file_name, 'r+b') as f:
        f.seek(page_number * PAGE_SIZE)
        f.write(page_data)


# Calculate the free space in a page
def Calculate_free_space(page_data):
    free_space_offset = int.from_bytes(page_data[4094:4096], 'big')
    slot_count = int.from_bytes(page_data[4092:4094], 'big')
    slot_table_size = slot_count * 4
    free_space = PAGE_SIZE - (free_space_offset + 4 + slot_table_size)
    return free_space

# Insert a record into a page.

def insert_record_data_to_page_data(page_data, record_data):

  record_length = len(record_data)
  page_data_buffer = bytearray(page_data)

  free_space_offset = int.from_bytes(page_data_buffer[4094:4096], 'big')
  slot_count = int.from_bytes(page_data_buffer[4092:4094], 'big')
  slot_table_size = slot_count * 4
  free_space = PAGE_SIZE - (free_space_offset + 4 + slot_table_size)

  if record_length + 4 > free_space:
      return None  # Not enough space

  # Insert the record data
  page_data_buffer[free_space_offset:free_space_offset + record_length] = record_data

  # Create new slot entry
  new_slot_offset = free_space_offset
  new_slot_length = record_length
  new_slot_pos = PAGE_SIZE - 4 - ((slot_count + 1) * 4)
  struct.pack_into('>H', page_data_buffer, new_slot_pos, new_slot_offset)
  struct.pack_into('>H', page_data_buffer, new_slot_pos + 2, new_slot_length)

  # Update footer metadata
  new_free_space_offset = free_space_offset + record_length
  struct.pack_into('>H', page_data_buffer, 4094, new_free_space_offset)
  struct.pack_into('>H', page_data_buffer, 4092, slot_count + 1)

  return bytes(page_data_buffer)

def insert_record_to_file(file_name, record_data):

  file_size = os.path.getsize(file_name)
  num_pages = file_size // PAGE_SIZE

  for page_number in range(num_pages):
      page_data = read_page(file_name, page_number)
      updated_page = insert_record_data_to_page_data(page_data, record_data)
      if updated_page:
          write_page(file_name, page_number, updated_page)
          return
  
  # If no page has space, create a new page
  page_data = b'\x00' * PAGE_SIZE
  page_data = insert_record_data_to_page_data(page_data, record_data)
  append_page(file_name, page_data)

# Get a record from a page
def get_record_from_page(page_data, record_id):
  # Retrieve a record from the specified page_data given the record ID.
  slot_pos = PAGE_SIZE - 4 - ((record_id + 1) * 4)
  record_offset = int.from_bytes(page_data[slot_pos:slot_pos + 2], 'big')
  record_length = int.from_bytes(page_data[slot_pos + 2:slot_pos + 4], 'big')
  record = page_data[record_offset:record_offset + record_length]
  return record

def get_record_from_file(file_name, page_number, record_id):
  #Retrieve a record from the specified page of the heap file given the record ID.
  page_data = read_page(file_name, page_number)
  return get_record_from_page(page_data, record_id)

def get_all_record_from_page(page_data):
  # Retrieve all records from the specified page_data.
  slot_count = int.from_bytes(page_data[4092:4094], 'big')
  records = []
  for record_id in range(slot_count):
      records.append(get_record_from_page(page_data, record_id))
  return records

def get_all_record_from_file(file_name):
  #Retrieve all record from the specified the heap file.
  file_size = os.path.getsize(file_name)
  num_pages = file_size // PAGE_SIZE
  all_records = []
  for page_number in range(num_pages):
      page_data = read_page(file_name, page_number)
      all_records.extend(get_all_record_from_page(page_data))
  return all_records

# ===========================
# Test Example
# ===========================
if __name__ == "__main__":
    file_name = "heap_test.bin"

    create_heap_file(file_name)
    print("heap file has been Created")
    print("Inserting records...")
    record1 = b'HELLO'
    record2 = b'WORLD'
    record3 = b'HiGuys'

    insert_record_to_file(file_name, record1)
    insert_record_to_file(file_name, record2)
    insert_record_to_file(file_name, record3)

    page_data = read_page(file_name, 0)
    print("\n--- Page Metadata ---")
    free_space_offset = int.from_bytes(page_data[4094:4096], 'big')
    slot_count = int.from_bytes(page_data[4092:4094], 'big')
    print(f"Free Space Offset: {free_space_offset}")
    print(f"Slot Count: {slot_count}")

    print("\n--- Records in Page 0 ---")
    records = get_all_record_from_page(page_data)
    for i, rec in enumerate(records):
        print(f"Record {i}: {rec} -> {rec.decode(errors='ignore')}")

    print("\n--- Single Record Retrieval ---")
    one_record = get_record_from_file(file_name, 0, 1)
    print(f"Record[1] = {one_record} -> {one_record.decode(errors='ignore')}")

    print("\n--- All Records in File ---")
    all_records = get_all_record_from_file(file_name)
    for i, rec in enumerate(all_records):
        print(f"File Record {i}: {rec} -> {rec.decode(errors='ignore')}")

    print("The End")
