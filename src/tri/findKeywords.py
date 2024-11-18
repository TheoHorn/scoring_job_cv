# Import libraries
import nltk
import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer

# Keywords to look for
keywords = []

# Load the data
df = pd.read_csv('data/Resume.csv')

# Drop unwanted columns and missing values
df = df.drop(columns=['Resume_html'], errors='ignore')
df = df.dropna()

# Initialize a dictionary to store processed data
processed_data = {}

# Process each resume
for i in range(len(df)):
    resume_id = df.iloc[i]['ID']
    resume_text = df.iloc[i]['Resume_str'].lower()
    resume_dict = {}
    # Find words with two blank spaces before or after them
    matches = re.findall(r'\s\s\s(\w+)|(\w+)\s\s\s', resume_text)
    # Filter out words that contain numbers
    matches = [match for match in matches if not any(char.isdigit() for char in match)]
    for match in matches:
        for word in match:
            if word:
                if word not in keywords:
                    keywords.append(word)

print(keywords)