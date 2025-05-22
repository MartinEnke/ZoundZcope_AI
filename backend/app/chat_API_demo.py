import openai

openai.api_key = "your-api-key"  # Replace with your real API key

response = openai.ChatCompletion.create(
    model="gpt-4",  # or "gpt-3.5-turbo"
    messages=[
        {"role": "system", "content": "You are a friendly travel assistant."},
        {"role": "user", "content": "Where should I go for a summer vacation in Europe?"}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response['choices'][0]['message']['content'])
