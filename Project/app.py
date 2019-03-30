from Chatbot import Chatbot

message = ""
chatbot = Chatbot()
while("bye" not in message.lower()):
    message = input("User: ")
    # message = "Thank you! Bye"
    response = chatbot.get_response(message)
    print("Bot: ", response)