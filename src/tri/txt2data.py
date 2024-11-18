# Import libraries
import nltk
import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer

def main():
    # Download the required NLTK resources
    nltk.download('stopwords')
    nltk.download('punkt')

    # Initialize tools
    stemmer = SnowballStemmer('english')
    stop_words = set(stopwords.words('english'))

    # Keywords to look for
    keywords = ["summary", "skills", "experience", "education", "accomplishments", "projects", "certifications", "languages", "interests", "publications","overview","qualifications"]
    keywords = [keyword.lower() for keyword in keywords]

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

        # Find all keywords and their positions in the text
        keyword_positions = []
        for key in keywords:
            pattern = r'  ' + re.escape(key) + r'|' + re.escape(key) + r'  '
            matches = [(key, m.start(), m.end()) for m in re.finditer(pattern, resume_text, re.IGNORECASE)]
            keyword_positions.extend(matches)

        # Sort keyword positions by their starting index
        keyword_positions = sorted(keyword_positions, key=lambda x: x[1])

        # Extract content between keywords
        for j, (key, start, end) in enumerate(keyword_positions):
            # Start of the current keyword content
            content_start = end

            # End of the current keyword content (start of the next keyword or end of the text)
            if j + 1 < len(keyword_positions):
                content_end = keyword_positions[j + 1][1]
            else:
                content_end = len(resume_text)

            # Extract and clean content
            content = resume_text[content_start:content_end]
            content = re.sub(r'[^\w\s]', '', content)  # Remove special characters
            tokens = word_tokenize(content.lower())  # Tokenize and convert to lowercase
            filtered_tokens = [stemmer.stem(word) for word in tokens if word not in stop_words]  # Remove stopwords and stem words
            filtered_tokens = ' '.join(filtered_tokens)
            if key in resume_dict:
                resume_dict[key] += " "+ filtered_tokens
            else:
                resume_dict[key] = filtered_tokens

        # Store processed data
        processed_data[resume_id] = resume_dict

    # Convert dictionary to a DataFrame for analysis or export
    processed_df = pd.DataFrame.from_dict(processed_data, orient='index')

    # Export the results to a CSV file
    processed_df.to_csv('data/processed_resumes.csv', index_label='ID')

    ## Example: Print processed data for a specific resume ID
    #example_id = 33176873
    #if example_id in processed_data:
    #    for key, value in processed_data[example_id].items():
    #       print(f"{key}:\n{' '.join(value)}\n{'-' * 20}\n")
    #else:
    #    print(f"No data found for ID {example_id}")

if __name__ == "__main__":
    main()