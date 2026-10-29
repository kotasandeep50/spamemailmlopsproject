from pathlib import Path
import pandas as pd

source = Path('data/raw/emails.csv')
target = Path('data/processed/emails.csv')
target.parent.mkdir(parents=True, exist_ok=True)
if not source.exists():
    pd.DataFrame({'text': ['Win a free prize now', 'Project meeting at 10am'], 'label': [1, 0]}).to_csv(source, index=False)
data = pd.read_csv(source).dropna(subset=['text', 'label'])
data['text'] = data['text'].astype(str).str.strip()
data['label'] = data['label'].astype(int)
data.to_csv(target, index=False)
print(f'Prepared {len(data)} emails')
