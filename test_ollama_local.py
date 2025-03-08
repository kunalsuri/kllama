import ollama
from ollama import chat
from ollama import ListResponse, list

models = ollama.list()

# Iterate over each model and print its details
for model in models:
    print(model)


response: ListResponse = list()

for model in response.models:
  print('Name:', model.model)
  print('  Size (MB):', f'{(model.size.real / 1024 / 1024):.2f}')
  if model.details:
    print('  Format:', model.details.format)
    print('  Family:', model.details.family)
    print('  Parameter Size:', model.details.parameter_size)
    print('  Quantization Level:', model.details.quantization_level)
  print('\n')


stream = chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'Where is Paris? give me just 1 line'}],
    stream=True,
)

for chunk in stream:
  print(chunk.message.content, end='', flush=True)
