import pandas as pd
import numpy as np
from datetime import datetime, date
import mediacloud.api
from goose3 import Goose

def preprocess_df(df):
  # All NaN/null values in 'text' column --> error in scraping
  null_count = df['text'].isnull().sum().sum()
  assert null_count == df.isnull().sum().sum()
  print('Number of null values:', null_count)

  df.dropna(inplace = True)
  df.reset_index(drop = True, inplace = True)
  df.drop(['url'], axis = 1, inplace = True)
  print(len(df))
  if "publish_date" in df.columns:
    df['publish_date'] = pd.to_datetime(df['publish_date']).dt.date
  print(df.info(verbose=True))

  return df

def goose_text_extraction(article_url):
  try:
      g = Goose()
      article = g.extract(article_url)
      return article.cleaned_text
  except Exception as e:
      print(f"Error fetching text from {article_url}: {e}")
      return None
     

def retrieve_articles_and_process(API_KEY, query, start_date, end_date, mc_collection_ids):
    mc_search = mediacloud.api.SearchApi(API_KEY)
    all_articles = []

    more_articles_avail = True
    pagination_token = None
    while more_articles_avail:
        page, pagination_token = mc_search.story_list(query, start_date=start_date, end_date=end_date, collection_ids=[mc_collection_ids], pagination_token=pagination_token)
        all_articles += page
        more_articles_avail = pagination_token is not None

    print(f"Retrieved {len(all_articles)} articles")

    mc_articles = pd.DataFrame(all_articles)
    mc_articles.attrs['name'] = "mc_articles"
    mc_articles.drop(columns=["media_url", "language", "id", "indexed_date"], axis=1, inplace=True)

    print("Parsing articles and extracting text... Please be patient...")
    mc_articles['text'] = mc_articles['url'].apply(goose_text_extraction)
    mc_articles = mc_articles.dropna(subset = ["text"])

    print(mc_articles.head())

    return mc_articles


API_KEY = input("Enter your MediaCloud API key (free, sign up here: https://search.mediacloud.org/sign-up): ")
query = input("Enter appropriate keywords to query (separate words/phrases with AND + OR): ")
start_date = input("Enter START date to search: ")
end_date = input("Enter END date to search: ")
start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
print(type(end_date))
collection_ids = input("Enter collection IDs separated by commas (i.e. 1234,2345). Visit directory to see possible source IDs: ")
collection_ids = [int(id) for id in collection_ids.strip().split(',')]
print(collection_ids)

print("Retrieving articles...")


mc_articles = retrieve_articles_and_process(API_KEY, query, start_date, end_date, collection_ids)
mc_articles.to_csv("mc_articles.csv", index=False)