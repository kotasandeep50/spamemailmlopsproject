import argparse
import pandas as pd
from sklearn.metrics import classification_report
from inference import load_classifier

parser = argparse.ArgumentParser()
parser.add_argument('--data', default='data/processed/emails.csv')
args = parser.parse_args()
data = pd.read_csv(args.data)
classifier = load_classifier()
predictions = [1 if item['label'].lower() in {'label_1', 'spam'} else 0 for item in classifier(data['text'].tolist(), truncation=True)]
print(classification_report(data['label'].astype(int), predictions, zero_division=0))
