from pathlib import Path
import pandas as pd
import runpy


def test_sample_data_can_be_prepared(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('data/raw').mkdir(parents=True)
    Path('pipeline').mkdir()
    Path('data/raw/emails.csv').write_text('text,label\nhello,0\nfree prize,1\n')
    source = Path(__file__).parents[1] / 'pipeline' / 'prepare_data.py'
    runpy.run_path(str(source), run_name='__main__')
    output = pd.read_csv('data/processed/emails.csv')
    assert list(output.columns) == ['text', 'label']
    assert len(output) == 2
