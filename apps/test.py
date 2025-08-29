from ollama import Client

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'fbdd68026ce74d5c9032c9dc5e2c6f79.qGDBa76SzwR9wYM83blLvgkz'}
)

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
  print(part['message']['content'], end='', flush=True)
