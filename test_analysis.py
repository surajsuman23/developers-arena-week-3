"""Run with: python -m unittest -v"""
import csv
from collections import defaultdict
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import pandas as pd
from sales_analysis import clean_data, summarize


class SalesAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.raw = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Product': ['A', 'B'], 'Quantity': [2, 3],
            'Price': [10, 5], 'Total_Sales': [20, 15]})

    def test_known_metrics(self):
        data, _ = clean_data(self.raw)
        metrics, products = summarize(data)
        self.assertEqual(metrics, dict(revenue=35, units=5, rows=2,
                                       average=17.5, minimum=15, maximum=20))
        self.assertEqual(products['Units'].idxmax(), 'B')
        self.assertEqual(products['Revenue'].idxmax(), 'A')

    def test_exact_duplicates(self):
        data, _ = clean_data(pd.concat([self.raw, self.raw.iloc[[0]]]))
        self.assertEqual(len(data), 2)

    def test_missing_total_is_derived(self):
        self.raw.loc[0, 'Total_Sales'] = float('nan')
        data, _ = clean_data(self.raw)
        self.assertEqual(data.iloc[0]['Total_Sales'], 20)

    def test_missing_essential_fields(self):
        for column in ['Date', 'Product', 'Quantity', 'Price']:
            with self.subTest(column=column):
                raw = self.raw.copy()
                raw.loc[0, column] = None
                data, _ = clean_data(raw)
                self.assertEqual(len(data), 1)

    def test_invalid_numbers(self):
        for column, value in [('Quantity', 0), ('Quantity', -1),
                              ('Quantity', 1.5), ('Quantity', float('inf')),
                              ('Price', -10), ('Price', float('inf'))]:
            with self.subTest(column=column, value=value):
                raw = self.raw.astype({'Quantity': 'float64', 'Price': 'float64'})
                raw.loc[0, column] = value
                data, _ = clean_data(raw)
                self.assertEqual(len(data), 1)

    def test_invalid_date_and_blank_product(self):
        for column, value in [('Date', '2024-02-30'), ('Product', '   ')]:
            raw = self.raw.copy()
            raw.loc[0, column] = value
            data, _ = clean_data(raw)
            self.assertEqual(len(data), 1)

    def test_conflicting_total(self):
        self.raw.loc[0, 'Total_Sales'] = 999
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            clean_data(self.raw)

    def test_missing_column(self):
        with self.assertRaisesRegex(ValueError, 'Missing required columns'):
            clean_data(self.raw.drop(columns='Quantity'))

    def test_no_valid_rows(self):
        with self.assertRaisesRegex(ValueError, 'No valid sales rows'):
            clean_data(self.raw.iloc[:0])

    def test_zero_price_and_ties(self):
        self.raw['Price'] = 0
        self.raw['Total_Sales'] = 0
        self.raw['Quantity'] = 2
        data, _ = clean_data(self.raw)
        metrics, products = summarize(data)
        self.assertEqual(metrics['revenue'], 0)
        self.assertEqual(list(products.index[products.Units == products.Units.max()]), ['A', 'B'])

    def test_supplied_data_against_standard_library(self):
        path = Path(__file__).with_name('sales_data.csv')
        with path.open(newline='', encoding='utf-8') as file:
            records = list(csv.DictReader(file))
        amounts = [int(row['Total_Sales']) for row in records]
        units = defaultdict(int)
        for row in records:
            self.assertEqual(int(row['Total_Sales']), int(row['Quantity']) * int(row['Price']))
            units[row['Product']] += int(row['Quantity'])
        clean, _ = clean_data(pd.read_csv(path))
        metrics, products = summarize(clean)
        self.assertEqual(metrics['revenue'], sum(amounts))
        self.assertEqual(metrics['units'], sum(units.values()))
        self.assertEqual(metrics['average'], sum(amounts) / len(amounts))
        self.assertEqual(products.Units.to_dict(), dict(units))
        self.assertEqual(len(clean), 100)

    def test_command_from_different_directory(self):
        script = Path(__file__).with_name('sales_analysis.py').resolve()
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / 'report.md'
            result = subprocess.run([sys.executable, str(script), '--report', str(report)],
                                    cwd=folder, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('12,365,048.00', report.read_text())
            failed = subprocess.run([sys.executable, str(script), '--input', 'missing.csv'],
                                    cwd=folder, capture_output=True, text=True)
            self.assertEqual(failed.returncode, 1)
            self.assertIn('Analysis failed:', failed.stderr)


if __name__ == '__main__':
    unittest.main()
