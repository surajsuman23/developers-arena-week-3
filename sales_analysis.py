"""Week 3: explore, clean and summarize the supplied sales CSV."""
from pathlib import Path
import argparse
import pandas as pd


def clean_data(raw):
    """Keep usable sales records and record each cleaning decision."""
    required = ['Date', 'Product', 'Quantity', 'Price', 'Total_Sales']
    missing = [column for column in required if column not in raw.columns]
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(missing))
    data = raw.copy()
    notes = [f'Input: {len(data)} rows and {len(data.columns)} columns.',
             f'Missing cells before cleaning: {int(data.isna().sum().sum())}.']

    # Exact repeated rows are treated as accidental copies in this practice file.
    duplicates = int(data.duplicated().sum())
    data = data.drop_duplicates().copy()
    notes.append(f'Exact duplicate rows removed: {duplicates}.')
    data['Product'] = data['Product'].astype('string').str.strip().replace('', pd.NA)
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d', errors='coerce')
    for column in ['Quantity', 'Price', 'Total_Sales']:
        data[column] = pd.to_numeric(data[column], errors='coerce')
        data[column] = data[column].replace([float('inf'), -float('inf')], float('nan'))

    # Do not invent a product, date, quantity or price for incomplete records.
    invalid = (data[['Date', 'Product', 'Quantity', 'Price']].isna().any(axis=1)
               | (data['Quantity'] <= 0) | (data['Quantity'] % 1 != 0)
               | (data['Price'] < 0))
    notes.append(f'Rows excluded for invalid date, product, quantity or price: {int(invalid.sum())}.')
    data = data.loc[~invalid].copy()
    expected = (data['Quantity'] * data['Price']).round(2)
    missing_totals = data['Total_Sales'].isna()
    data.loc[missing_totals, 'Total_Sales'] = expected[missing_totals]
    notes.append(f'Missing or nonnumeric totals calculated as quantity x price: {int(missing_totals.sum())}.')
    # Stop on conflicting amounts instead of silently choosing a revenue figure.
    if ((data['Total_Sales'] - expected).abs() > 0.01).any():
        raise ValueError('Total_Sales conflicts with Quantity x Price. Review the source amounts.')
    if data.empty:
        raise ValueError('No valid sales rows remain after cleaning.')
    notes.append(f'Rows used in the analysis: {len(data)}.')
    return data, notes


def summarize(data):
    """Calculate totals and group products by both revenue and units sold."""
    products = data.groupby('Product').agg(
        Units=('Quantity', 'sum'), Revenue=('Total_Sales', 'sum'))
    products = products.sort_values('Revenue', ascending=False)
    metrics = {
        'revenue': float(data['Total_Sales'].sum()),
        'units': int(data['Quantity'].sum()),
        'rows': len(data),
        'average': float(data['Total_Sales'].mean()),
        'minimum': float(data['Total_Sales'].min()),
        'maximum': float(data['Total_Sales'].max()),
    }
    return metrics, products


def build_report(raw, data, notes, metrics, products):
    """Build Markdown using calculated values, so the report can be regenerated."""
    unit_winners = ', '.join(products.index[products['Units'] == products['Units'].max()])
    revenue_winners = ', '.join(products.index[products['Revenue'] == products['Revenue'].max()])
    share = products['Revenue'].max() / metrics['revenue'] * 100 if metrics['revenue'] else 0
    lines = [
        '# Sales Data Analysis', '',
        '## Source and scope', '',
        'Source: Developers Arena Week 3 supplied `sales_data.csv`, downloaded 29 October 2026.',
        'This is a practice dataset. Each row is treated as one sales record, not a verified unique order.',
        'Amounts are labelled INR following the portal sample; the CSV itself has no currency column.',
        f"Period: {data['Date'].min():%d %b %Y} to {data['Date'].max():%d %b %Y}.", '',
        '## Results', '', '| Metric | Value |', '| --- | ---: |',
        f"| Total revenue (INR) | {metrics['revenue']:,.2f} |",
        f"| Total units sold | {metrics['units']:,} |",
        f"| Sales records analyzed | {metrics['rows']} |",
        f"| Average revenue per record (INR) | {metrics['average']:,.2f} |",
        f"| Lowest record revenue (INR) | {metrics['minimum']:,.2f} |",
        f"| Highest record revenue (INR) | {metrics['maximum']:,.2f} |", '',
        '## Product comparison', '', '| Product | Units sold | Revenue (INR) |', '| --- | ---: | ---: |',
    ]
    for product, row in products.iterrows():
        lines.append(f"| {product} | {int(row['Units'])} | {row['Revenue']:,.2f} |")
    lines += ['', '## Findings', '',
              f'- Best-selling product by units: **{unit_winners}** ({int(products["Units"].max())} units).',
              f'- Highest-revenue product: **{revenue_winners}** (INR {products["Revenue"].max():,.2f}).',
              f'- Each highest-revenue product contributes {share:.2f}% of total revenue.',
              '- Units sold and revenue answer different questions: a higher unit price can change the revenue ranking.',
              '- These figures describe this sample only. There is no cost data to calculate profit, and no basis for a sales forecast.', '',
              '## Data checks and cleaning', '']
    lines += ['- ' + note for note in notes]
    lines += ['', 'Exact duplicate removal assumes repeated complete rows are accidental copies. Real transaction data should use an order ID before deduplicating.',
              'Missing product/date/quantity/price rows are excluded rather than filled with averages. Missing totals are derived only when quantity and price are valid. Conflicting totals stop the analysis.', '',
              '## Exploration', '', 'Original column types:', '', '```text', raw.dtypes.to_string(), '```', '',
              'First five original records:', '', '```text', raw.head().to_string(index=False), '```', '',
              '## Method', '',
              '`read_csv()` loads the source. `head()`, `shape`, `dtypes` and `isna()` inspect it. `clean_data()` validates records. `groupby()` totals units and revenue per product. `sum()`, `mean()`, `min()` and `max()` calculate the headline metrics.', '',
              'Run `python sales_analysis.py` to regenerate this report. See README.md for setup, functions and the five-step walkthrough.']
    return '\n'.join(lines) + '\n'


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=folder / 'sales_data.csv')
    parser.add_argument('--report', type=Path, default=folder / 'analysis_report.md')
    args = parser.parse_args()
    try:
        raw = pd.read_csv(args.input)
        data, notes = clean_data(raw)
        metrics, products = summarize(data)
        report = build_report(raw, data, notes, metrics, products)
        args.report.write_text(report, encoding='utf-8')
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.exit(1, f'Analysis failed: {error}\n')
    print('SALES DATA ANALYSIS')
    print(f'Input shape: {raw.shape[0]} rows x {raw.shape[1]} columns')
    for note in notes:
        print(note)
    print(f"Total revenue: INR {metrics['revenue']:,.2f}")
    print(f"Units sold: {metrics['units']}")
    print(f"Average revenue per record: INR {metrics['average']:,.2f}")
    print(f"Minimum / maximum: INR {metrics['minimum']:,.2f} / INR {metrics['maximum']:,.2f}")
    print('\nPRODUCT SUMMARY')
    print(products.to_string(float_format=lambda value: f'{value:,.2f}'))
    print('\nReport saved:', args.report.name)


if __name__ == '__main__':
    main()
