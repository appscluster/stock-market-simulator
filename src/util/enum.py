
# Define enum structure.
# Example usage: Numbers = enum(ONE=1, TWO=2, THREE='three')

def enum(**enums):
  return type('Enum', (), enums)
