import re, json
import random
import spacy 
import numpy as np
import en_core_web_sm
from nltk.stem import WordNetLemmatizer
import nltk
import pandas as pd
# coding: utf-8


class Chatbot(object):

    # In[3]:


    # Load the spacy model: nlp
    def __init__(self):
        self.nlp = en_core_web_sm.load()
        self.lemmatizer = WordNetLemmatizer()
    
    def get_response(self, message):
        response="Sorry, I could not understand you"
        
        def clean(text, pos=False):
            text = text.lower()
            text = re.sub(r'[^\w\s\$]','',text)
            text_list = [word for word in text.split()]
            #If last word has a question mark attached, that gets removed also.
            text_regex = [word for word in text_list if re.search('^[a-z0-9$]+$',word)]
            final_text = [self.lemmatizer.lemmatize(word) for word in text_regex]
            if(pos):         #If POS is true, then attach tag
                final_text = nltk.pos_tag(final_text)
            return final_text


    # In[5]:


        def listToString(inputList, sep=' '):
            return sep.join(inputList)


        # ## Intent-Entity match 

        # In[6]:


        default_response = "Sorry, I could not understand you."


        # In[7]:


        def get_response_from_intent(matched_intent):
            response = default_response
            for intent in intents['intents']:
                
                if(intent['tag']==matched_intent):
                    response = random.choice(intent['responses'])
            return response


        # In[8]:


        # import our chat-bot intents file
        with open('data/intents.json') as json_data:
            intents = json.load(json_data)


        # In[9]:


        patterns = {}
        for intent in intents['intents']:
            patterns[intent['tag']] = re.compile('|'.join(intent['patterns']))
            
        patterns


        # In[10]:


        # Define a function to find the intent of a message
        def match_intent(message):
            matched_intent = None
            for intent, pattern in patterns.items():
                # Check if the pattern occurs in the message 
                if pattern.search(message) :
                    matched_intent = intent
                
            return matched_intent


        # ## Entity Recognizer

        # In[11]:


        # Define included entities
        include_entities = ['CARDINAL', 'MONEY', 'GPE']

        # Define extract_entities()
        def extract_entities(message):
            # Create a dict to hold the entities
            ents = dict.fromkeys(include_entities)
            # Create a spacy document
            doc = self.nlp(message)
            for ent in doc.ents:
                if ent.label_ in include_entities:
                    # Save interesting entities
                    ents[ent.label_] = ent.text
            return ents

        # print(extract_entities('What are the top 5 hotels in Venice below $100"'))
        # print(extract_entities('terms of location'))


        # ## POS Tagging

        # In[12]:


        def getFeatureCriteria(sent):
            sent = [word for word in sent.split()]
            tagged_sent = nltk.pos_tag(sent)
            feature=None
            for tag in tagged_sent:
                if(tag[1]=='NN'):
                    feature=tag[0]
            return feature


        # In[13]:


        getFeatureCriteria("in venice")


        # ## Query the database

        # In[14]:


        df = pd.read_csv('data/listings_clean.csv')


        # In[15]:


        def getTopKHotelsCriteria(df, k, criteria=None):
            if(criteria is None):
                return df.sort_values('review_scores_rating', ascending=False).head(k).name.values
            else:
                entities = extract_entities(criteria)
                neighbourhood = entities['GPE']
                
                if(neighbourhood is not None):
                    df = df[df['neighbourhood']==neighbourhood]
                
                price = entities['MONEY']
                if(price is not None):   
                    price = float(price)
                    greater = True
                    if(re.search('below|less', criteria)):
                        greater=False
                        df = df[df['price']<=price]
                    else:
                        df = df[df['price']>=price]
                
                feature = getFeatureCriteria(criteria)
                if(feature is None):
                    feature='rating'
                
                criteria='review_scores_'+feature
                if(criteria not in df.columns.values):
                    criteria = 'review_scores_rating'
                    
                return df.sort_values(criteria, ascending=False).head(k).name.values


        # In[16]:


        def getFeatureRating(hotel, criteria):
            criteria='review_scores_'+criteria
            return df[df['name']==hotel][criteria].values[0]


        def getHotelRating(hotel):
            criteria='review_scores_rating'
            return df[df['name']==hotel][criteria].values[0]

        # ## Create a dictionary of rules and get responses

        # In[17]:


        def get_num_groups(regex):
            return re.compile(regex).groups


        # In[18]:


        rules = {}
        tags = {}
        for intent in intents['rules']:    
            rules[intent['patterns']] = intent['responses']
            tags[intent['patterns']] = intent['tag']
            
        tags


        # In[19]:


        # Define match_rule()
        def match_rule(rules, message, actual_message): #message refers to clean_version
            response, keywords, tag = default_response, [], None
            
            # Iterate over the rules dictionary
            for pattern, responseList in rules.items():
                # Create a match object
                match = re.search(pattern, message)
                num_groups = get_num_groups(pattern)        
                if match is not None:
                    # Choose a random response
                    tag = tags[pattern]
                    response = random.choice(responseList)
                
                    if '{0}' in response:
                        #fix case of keyword found
                        keyword = match.group(num_groups)
                        #index in actual message
                        index = actual_message.lower().index(keyword)
        #                 print(keyword, index, actual_message[index: index+len(keyword)], actual_message)
                        keywords.append(actual_message[index: index+len(keyword)])
                        response = response.replace('{0}', keywords[0])
                        
                    
                    if '{1}' in response:                
                        keyword = match.group(num_groups-1)
                        #index in actual message
                        index = actual_message.lower().index(keyword)
                        keywords.append(actual_message[index: index+len(keyword)])
                        response = response.replace('{1}', keywords[1])
                        
            # Return the response and phrase
            return response, keywords, tag
        
        
        clean_message = clean(message)
        clean_string = listToString(clean_message)
        intent = match_intent(clean_string)
        
        if(intent is not None):
            response = get_response_from_intent(intent)
        else:
            response, keywords, tag = match_rule(rules, clean_string, message)
            if(tag=="topN"):
                if(len(keywords)==1):                
                    topKHotels = getTopKHotelsCriteria(df, int(keywords[0]))
                else:
                    topKHotels = getTopKHotelsCriteria(df, int(keywords[1]), keywords[0]) 
                response = "The best hotels for you are: \n"+listToString(topKHotels, sep=',')
            if(tag=="amenities"):
                rating = getFeatureRating(keywords[1], keywords[0])
                response = str("The rating for "+keywords[1]+" in terms of "+keywords[0]+" is "+str(rating))
            if(tag=="rating"):
                rating = getHotelRating(keywords[0])
                response = str("The rating for "+keywords[0]+" is "+str(rating))
        return response


    # ## Test the Chatbot

    # # In[21]:


    # message = get_response("What is the rating of Venice Beach Cabana?")
    # # message = "What are the top 5 hotels above $100 in Venice?"
    # # message = "Does Venice Beach Cabana have good ratings?"
    # # message = input()
    # response = get_response(message)

    # print("USER: ", message)
    # print("BOT: ",response)
    # #What are the top 5 hotels?


    # # In[22]:


    # # message = "What are the top 5 hotels below $100 in Venice"
    # message = "Does Venice Beach Cabana have good cleanliness?"
    # # message = input()
    # response = get_response(message)

    # print("USER: ", message)
    # print("BOT: ",response)

    #What are the top 5 hotels?

