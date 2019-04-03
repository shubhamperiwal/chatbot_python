
# coding: utf-8

# In[ ]:


from Chatbot import Chatbot

message = ""
chatbot = Chatbot()


# In[ ]:


while("bye" not in message.lower()):
    message = input("User: ")
    response = chatbot.get_response(message)
    print("Bot: ", response)

