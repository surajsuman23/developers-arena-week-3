# Sales Data Analysis

## Source and scope

Source: Developers Arena Week 3 supplied `sales_data.csv`, downloaded 29 October 2026.
This is a practice dataset. Each row is treated as one sales record, not a verified unique order.
Amounts are labelled INR following the portal sample; the CSV itself has no currency column.
Period: 01 Jan 2024 to 09 Apr 2024.

## Results

| Metric | Value |
| --- | ---: |
| Total revenue (INR) | 12,365,048.00 |
| Total units sold | 478 |
| Sales records analyzed | 100 |
| Average revenue per record (INR) | 123,650.48 |
| Lowest record revenue (INR) | 6,540.00 |
| Highest record revenue (INR) | 373,932.00 |

## Product comparison

| Product | Units sold | Revenue (INR) |
| --- | ---: | ---: |
| Laptop | 136 | 3,889,210.00 |
| Tablet | 127 | 2,884,340.00 |
| Phone | 101 | 2,859,394.00 |
| Headphones | 48 | 1,384,033.00 |
| Monitor | 66 | 1,348,071.00 |

## Findings

- Best-selling product by units: **Laptop** (136 units).
- Highest-revenue product: **Laptop** (INR 3,889,210.00).
- Each highest-revenue product contributes 31.45% of total revenue.
- Units sold and revenue answer different questions: a higher unit price can change the revenue ranking.
- These figures describe this sample only. There is no cost data to calculate profit, and no basis for a sales forecast.

## Data checks and cleaning

- Input: 100 rows and 7 columns.
- Missing cells before cleaning: 0.
- Exact duplicate rows removed: 0.
- Rows excluded for invalid date, product, quantity or price: 0.
- Missing or nonnumeric totals calculated as quantity x price: 0.
- Rows used in the analysis: 100.

Exact duplicate removal assumes repeated complete rows are accidental copies. Real transaction data should use an order ID before deduplicating.
Missing product/date/quantity/price rows are excluded rather than filled with averages. Missing totals are derived only when quantity and price are valid. Conflicting totals stop the analysis.

## Exploration

Original column types:

```text
Date           object
Product        object
Quantity        int64
Price           int64
Customer_ID    object
Region         object
Total_Sales     int64
```

First five original records:

```text
      Date    Product  Quantity  Price Customer_ID Region  Total_Sales
2024-01-01      Phone         7  37300     CUST001   East       261100
2024-01-02 Headphones         4  15406     CUST002  North        61624
2024-01-03      Phone         2  21746     CUST003   West        43492
2024-01-04 Headphones         1  30895     CUST004   East        30895
2024-01-05     Laptop         8  39835     CUST005  North       318680
```

## Method

`read_csv()` loads the source. `head()`, `shape`, `dtypes` and `isna()` inspect it. `clean_data()` validates records. `groupby()` totals units and revenue per product. `sum()`, `mean()`, `min()` and `max()` calculate the headline metrics.

Run `python sales_analysis.py` to regenerate this report. See README.md for setup, functions and the five-step walkthrough.
