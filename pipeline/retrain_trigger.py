import argparse
import json
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--report', default='monitoring/reports/summary.json')
args = parser.parse_args()
with open(args.report, encoding='utf-8') as report_file:
    report = json.load(report_file)
if report.get('drift_detected') or report.get('performance_below_threshold'):
    print('Retraining required')
    subprocess.run(['python', 'pipeline/prepare_data.py'], check=True)
    subprocess.run(['python', 'model/train.py'], check=True)
else:
    print('Current model remains healthy')
