import re

def camel2snake(camel: str) -> str:
    # insert _ between lower and upper case characters
    snake = re.sub(r'([a-z])([A-Z])',r'\1_\2',camel)
    # insert _ between upper case and number
    snake = re.sub(r'([A-Z])([0-9])', r'\1_\2', snake)
    # insert _ between number and letter
    snake = re.sub(r'([0-9])([a-zA-Z])', r'\1_\2', snake)
    # finally 2+ upper followed by 1 upper, 1 lower
    snake = re.sub(r'([A-Z]{2,})([A-Z][a-z])', r'\1_\2', snake)
    return snake.lower()